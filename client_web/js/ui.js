export function setText (element, value = '') {
  if (element) {
    element.textContent = String(value);
  }
}

export function setVisible (element, visible) {
  if (element) {
    element.hidden = !visible;
  }
}

export function setButtonBusy (button, busy, busyLabel = 'Recherche…') {
  if (!button) {
    return;
  }

  if (busy) {
    button.dataset.originalLabel = button.textContent.trim();
    button.textContent = busyLabel;
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    return;
  }

  button.textContent = button.dataset.originalLabel ?? button.textContent;
  button.disabled = false;
  button.removeAttribute('aria-busy');
  delete button.dataset.originalLabel;
}

export function showResultState (
  state,
  { loadingElement, errorElement, resultElement }
) {
  setVisible(loadingElement, state === 'loading');
  setVisible(errorElement, state === 'error');
  setVisible(resultElement, state === 'success');
}

export function getPublicErrorMessage (error) {
  if (error?.status === 400 || error?.status === 422) {
    return error.message || 'La question envoyée est invalide.';
  }

  if (error?.status === 404) {
    return 'Le service de recherche demandé est introuvable.';
  }

  if (error?.status === 502 || error?.status === 503 || error?.status === 504) {
    return 'Le service est temporairement indisponible. Réessayez plus tard.';
  }

  return error?.message || 'Une erreur inattendue est survenue.';
}
