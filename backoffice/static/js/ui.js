const toastTimers = new WeakMap();

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

export function showAlert (container, messageElement, message) {
  setText(messageElement, message);
  setVisible(container, true);
}

export function hideAlert (container) {
  setVisible(container, false);
}

export function setButtonBusy (button, busy, busyLabel = 'Chargement…') {
  if (!button) {
    return;
  }

  // Write to the .button__label span when present, so a busy/idle cycle
  // doesn't wipe out that child element - overwriting the button's own
  // textContent would destroy it and any styling that targets it.
  const labelElement = button.querySelector('.button__label') ?? button;

  if (busy) {
    button.dataset.originalLabel = labelElement.textContent.trim();
    labelElement.textContent = busyLabel;
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    return;
  }

  labelElement.textContent = button.dataset.originalLabel ?? labelElement.textContent;
  button.disabled = false;
  button.removeAttribute('aria-busy');
  delete button.dataset.originalLabel;
}

export function openDialog (dialog) {
  if (!dialog) {
    return;
  }

  if (typeof dialog.showModal === 'function') {
    if (!dialog.open) {
      dialog.showModal();
    }
  } else {
    dialog.setAttribute('open', '');
  }
}

export function closeDialog (dialog) {
  if (!dialog) {
    return;
  }

  if (typeof dialog.close === 'function' && dialog.open) {
    dialog.close();
  } else {
    dialog.removeAttribute('open');
  }
}

export function bindDialogCloseButtons (root = document) {
  root.addEventListener('click', (event) => {
    const button = event.target.closest('[data-close-dialog]');

    if (!button) {
      return;
    }

    const dialog = document.getElementById(button.dataset.closeDialog);
    closeDialog(dialog);
  });

  root.querySelectorAll('dialog').forEach((dialog) => {
    dialog.addEventListener('click', (event) => {
      if (event.target === dialog) {
        closeDialog(dialog);
      }
    });
  });
}

export function showToast (container, messageElement, message) {
  if (!container) {
    return;
  }

  const currentTimer = toastTimers.get(container);

  if (currentTimer) {
    window.clearTimeout(currentTimer);
  }

  setText(messageElement, message);
  setVisible(container, true);

  const timer = window.setTimeout(() => {
    setVisible(container, false);
    toastTimers.delete(container);
  }, 4500);

  toastTimers.set(container, timer);
}

export function clearFieldError (input, errorElement) {
  input?.removeAttribute('aria-invalid');
  setVisible(errorElement, false);
}

export function showFieldError (input, errorElement, message) {
  input?.setAttribute('aria-invalid', 'true');
  setText(errorElement, message);
  setVisible(errorElement, true);
}

export function isPositiveInteger (value) {
  const number = Number(value);
  return Number.isInteger(number) && number > 0;
}

export function getApiErrorMessage (error) {
  if (error?.status === 401) {
    return 'Votre session a expiré. Veuillez vous reconnecter.';
  }

  if (error?.status === 403) {
    return 'Vous n’êtes pas autorisé à effectuer cette action.';
  }

  if (error?.status === 404) {
    return 'La ressource demandée est introuvable.';
  }

  if (error?.status === 409) {
    return error.message || 'L’opération demandée provoque un conflit.';
  }

  if (error?.status === 422 || error?.status === 400) {
    return error.message || 'Les informations saisies sont invalides.';
  }

  if (error?.status === 502 || error?.status === 503) {
    return 'Un service nécessaire est temporairement indisponible.';
  }

  return error?.message || 'Une erreur inattendue est survenue.';
}
