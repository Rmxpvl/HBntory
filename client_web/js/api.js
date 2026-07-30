import { API_REQUEST_TIMEOUT_MS, PUBLIC_API_URL } from './config.js';

export class PublicApiError extends Error {
  constructor (status, message) {
    super(message);
    this.name = 'PublicApiError';
    this.status = status;
  }
}

function buildUrl (path, params = {}) {
  const url = new URL(`${PUBLIC_API_URL}${path}`, window.location.origin);

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value);
    }
  }

  return url;
}

async function request (path, params, signal) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(
    () => controller.abort(),
    API_REQUEST_TIMEOUT_MS
  );

  signal?.addEventListener('abort', () => controller.abort(), { once: true });

  try {
    const response = await fetch(buildUrl(path, params), {
      signal: controller.signal
    });

    if (!response.ok) {
      let message = 'Une erreur est survenue.';

      try {
        const data = await response.json();
        message = data?.error ?? message;
      } catch {
        // No JSON body to read the error from - keep the generic message.
      }

      throw new PublicApiError(response.status, message);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof PublicApiError) {
      throw error;
    }

    if (error.name === 'AbortError') {
      throw new PublicApiError(
        0,
        signal?.aborted
          ? 'La requête a été annulée.'
          : 'Le service met trop de temps à répondre.'
      );
    }

    throw new PublicApiError(0, 'Impossible de contacter le service.');
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export function fetchCategories (signal) {
  return request('/categories', {}, signal);
}

export function fetchProducts ({ q, category } = {}, signal) {
  return request('/products', { q, category }, signal);
}
