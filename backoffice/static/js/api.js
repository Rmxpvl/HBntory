import { API_REQUEST_TIMEOUT_MS, BACKOFFICE_API_URL } from './config.js';

export class ApiError extends Error {
  constructor (status, message, code = null, details = null) {
    super(message);

    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function createRequestUrl (path) {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${BACKOFFICE_API_URL}${normalizedPath}`;
}

function createHeaders (body, suppliedHeaders = {}) {
  const headers = new Headers(suppliedHeaders);
  const bodyIsFormData =
    typeof FormData !== 'undefined' && body instanceof FormData;

  if (body != null && !bodyIsFormData && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  headers.set('Accept', 'application/json');
  return headers;
}

async function parseResponse (response) {
  if (response.status === 204) {
    return null;
  }

  const rawBody = await response.text();

  if (!rawBody) {
    return null;
  }

  const contentType = response.headers.get('content-type') ?? '';

  if (!contentType.includes('application/json')) {
    return { message: rawBody };
  }

  try {
    return JSON.parse(rawBody);
  } catch {
    throw new ApiError(
      response.status,
      'Le serveur a renvoyé une réponse JSON invalide.',
      'INVALID_JSON_RESPONSE'
    );
  }
}

function extractError (data, status) {
  const error = data?.error;

  if (typeof error === 'string') {
    return new ApiError(status, error);
  }

  return new ApiError(
    status,
    error?.message ??
      data?.message ??
      'Une erreur est survenue pendant la requête.',
    error?.code ?? data?.code ?? null,
    error?.details ?? data?.details ?? null
  );
}

export async function apiRequest (path, options = {}) {
  const {
    body = null,
    headers = {},
    signal: externalSignal,
    timeout = API_REQUEST_TIMEOUT_MS,
    ...fetchOptions
  } = options;

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeout);

  const abortFromExternalSignal = () => controller.abort();
  externalSignal?.addEventListener('abort', abortFromExternalSignal, {
    once: true
  });

  try {
    const response = await fetch(createRequestUrl(path), {
      ...fetchOptions,
      body,
      credentials: 'include',
      headers: createHeaders(body, headers),
      signal: controller.signal
    });

    const data = await parseResponse(response);

    if (!response.ok) {
      throw extractError(data, response.status);
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    if (error.name === 'AbortError') {
      if (externalSignal?.aborted) {
        throw new ApiError(0, 'La requête a été annulée.', 'REQUEST_ABORTED');
      }

      throw new ApiError(
        0,
        'Le serveur met trop de temps à répondre.',
        'REQUEST_TIMEOUT'
      );
    }

    throw new ApiError(
      0,
      'Impossible de contacter le serveur.',
      'NETWORK_ERROR'
    );
  } finally {
    window.clearTimeout(timeoutId);
    externalSignal?.removeEventListener('abort', abortFromExternalSignal);
  }
}
