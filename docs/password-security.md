# Password Security

## Mechanism: Argon2id

Passwords are hashed with **Argon2id** (`argon2-cffi`), the mechanism recommended
by OWASP for new applications and the winner of the 2015 Password Hashing
Competition. The `id` variant mixes Argon2i (side-channel resistant) and
Argon2d (GPU-cracking resistant), which is why it's the general recommendation
over plain Argon2i/Argon2d.

Parameters (library defaults, deliberately expensive):

| Parameter | Value | Meaning |
| --- | --- | --- |
| `time_cost` | 3 | number of passes over memory |
| `memory_cost` | 65536 KiB (64 MiB) | RAM required per hash attempt |
| `parallelism` | 4 | number of threads |
| `salt_len` | 16 bytes | random salt, generated per password |
| `hash_len` | 32 bytes | output hash length |

## How passwords are hashed

`app/auth/passwords.py::hash_password(plain)` wraps one shared
`PasswordHasher()` instance. It returns a single self-describing string, e.g.:

```
$argon2id$v=19$m=65536,t=3,p=4$xEAsA8DDml0cqQM/cVqp2A$vD+/msTxiqxobKcLqpUFoLg3JqBoFBxzKqid6Wr0RW8
```

This string encodes the algorithm, version, cost parameters, a random salt,
and the derived hash — all in one field. Two users with the same password get
different stored values, and no separate `salt` column is needed: everything
required to verify is in `password_hash`.

Only this hash is persisted (`User.password_hash`). The plaintext password
never reaches the database and is not logged.

## How verification works

`app/services/auth_services.py::authenticate_user(db, username, password)`:

1. Looks up the user by username.
2. Calls `verify_password_or_dummy(password, stored_hash)`
   (`app/auth/passwords.py`) with `stored_hash=None` if the username doesn't
   exist. That function always runs a real Argon2 verify — against the
   user's hash, or against a **fixed dummy Argon2id hash** (`DUMMY_HASH`) when
   there's no user — instead of short-circuiting immediately. This keeps the
   response time close to a real "wrong password" case, so an attacker can't
   distinguish "no such user" from "wrong password" by timing the response
   (a username-enumeration mitigation).
3. `verify_password_or_dummy` delegates to `verify_password`, which calls
   `PasswordHasher.verify(stored_hash, submitted_password)` — re-deriving the
   hash with the same salt/parameters embedded in the stored string and
   comparing it. Any failure (`VerifyMismatchError`, `VerificationError`,
   `InvalidHashError`) is caught and turned into `False`; `authenticate_user`
   turns that into the generic `ValueError("invalid credentials")` — the
   caller never learns *why* it failed.
4. Rejects the user if `status != ACTIVE` (soft-deleted or deactivated
   accounts), again with the same generic error, after the password check has
   already run — so this check doesn't leak "this account exists but is
   disabled" through a faster response.

There is one shared `PasswordHasher()` instance for the whole app
(`app/auth/passwords.py::_hasher`) — `hash_password`, `verify_password` and
`verify_password_or_dummy` all go through it, so every caller (`seed.py`,
`user_services.py`, `authenticate_user`) hashes and verifies the same way.
`verify_password(plain, stored_hash)` is the plain version (no dummy-hash
handling) for callers that already know the account exists — e.g.
`change_password` flows that re-check a user's current password.

## Why plain SHA-256 (or MD5, SHA-1) is not sufficient

A general-purpose cryptographic hash is built to be **fast** — that's the
opposite of what password storage needs:

- **No built-in salt.** Identical passwords produce identical hashes, making
  precomputed rainbow-table attacks possible across every account at once.
- **Too fast to brute-force-resist.** A modern GPU computes billions of
  SHA-256 hashes per second. A stolen hash database can be dictionary-attacked
  or brute-forced in a practical amount of time.
- **Not memory-hard.** SHA-256 needs almost no RAM per hash, so attackers can
  run massively parallel cracking on GPUs/ASICs cheaply. Argon2id's
  `memory_cost` (64 MiB per attempt) makes that parallelism expensive: an
  attacker needs 64 MiB *per guess in flight*, not per core.
- **No adjustable work factor.** Argon2id's `time_cost`/`memory_cost` can be
  raised as hardware gets faster; SHA-256 has no such knob — you'd have to
  change algorithms entirely.

Argon2id (like bcrypt/PBKDF2, but with better memory-hardness) is
purpose-built to be *slow and memory-expensive on attackers* while staying
cheap enough for one legitimate login per request.
