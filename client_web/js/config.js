const runtimeConfig = globalThis.HBNTORY_CONFIG ?? {};

function normalizeBaseUrl (url) {
  return String(url).replace(/\/+$/, '');
}

// Relative by default: client_web is served by the same app as the
// Backoffice, so a relative path works regardless of host/port.
export const PUBLIC_API_URL = normalizeBaseUrl(
  runtimeConfig.PUBLIC_API_URL ?? '/api/public'
);

export const API_REQUEST_TIMEOUT_MS = Number(
  runtimeConfig.API_REQUEST_TIMEOUT_MS ?? 15000
);
