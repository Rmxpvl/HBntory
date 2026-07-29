const runtimeConfig = globalThis.HBNTORY_CONFIG ?? {};

function normalizeBaseUrl (url) {
  return String(url).replace(/\/+$/, '');
}

export const BACKOFFICE_API_URL = normalizeBaseUrl(
  runtimeConfig.BACKOFFICE_API_URL ?? '/api'
);

export const API_REQUEST_TIMEOUT_MS = Number(
  runtimeConfig.API_REQUEST_TIMEOUT_MS ?? 15000
);

export const ROLE_ADMIN = runtimeConfig.ROLE_ADMIN ?? 'admin';
export const ROLE_COMMON = runtimeConfig.ROLE_COMMON ?? 'common';
