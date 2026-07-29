import { AI_API_URL, AI_QUERY_PATH, AI_REQUEST_TIMEOUT_MS } from './config.js';

export class AiApiError extends Error {
  constructor (status, message, code = null) {
    super(message);

    this.name = 'AiApiError';
    this.status = status;
    this.code = code;
  }
}

async function parseResponse (response) {
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
    throw new AiApiError(
      response.status,
      'Le service a renvoyé une réponse invalide.',
      'INVALID_JSON_RESPONSE'
    );
  }
}

function createApiError (response, data) {
  const error = data?.error;

  return new AiApiError(
    response.status,
    error?.message ?? data?.message ?? 'Impossible d’obtenir une réponse.',
    error?.code ?? data?.code ?? null
  );
}

export async function sendQuestion (question, externalSignal = null) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(
    () => controller.abort(),
    AI_REQUEST_TIMEOUT_MS
  );

  const abortFromExternalSignal = () => controller.abort();
  externalSignal?.addEventListener('abort', abortFromExternalSignal, {
    once: true
  });

  try {
    const response = await fetch(`${AI_API_URL}${AI_QUERY_PATH}`, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ question }),
      signal: controller.signal
    });

    const data = await parseResponse(response);

    if (!response.ok) {
      throw createApiError(response, data);
    }

    return data;
  } catch (error) {
    if (error instanceof AiApiError) {
      throw error;
    }

    if (error.name === 'AbortError') {
      if (externalSignal?.aborted) {
        throw new AiApiError(0, 'La requête a été annulée.', 'REQUEST_ABORTED');
      }

      throw new AiApiError(
        0,
        'La recherche prend trop de temps. Veuillez réessayer.',
        'REQUEST_TIMEOUT'
      );
    }

    throw new AiApiError(
      0,
      'Impossible de contacter le service de recherche.',
      'NETWORK_ERROR'
    );
  } finally {
    window.clearTimeout(timeoutId);
    externalSignal?.removeEventListener('abort', abortFromExternalSignal);
  }
}
