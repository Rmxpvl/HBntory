from .db import SessionLocal


def get_db():
    db = SessionLocal()  # Open a database session
    try:
        yield db         # Give it to the backend function (for example: add stock)
    finally:
        db.close()       # Close the session when the work is finished