const runtimeConfig = globalThis.HBNTORY_CONFIG ?? {};

function normalizeBaseUrl (url) {
  return String(url).replace(/\/+$/, '');
}

export const AI_API_URL = normalizeBaseUrl(
  runtimeConfig.AI_API_URL ?? 'http://localhost:8000/api'
);

export const AI_REQUEST_TIMEOUT_MS = Number(
  runtimeConfig.AI_REQUEST_TIMEOUT_MS ?? 45000
);

export const AI_QUERY_PATH = runtimeConfig.AI_QUERY_PATH ?? '/query';
