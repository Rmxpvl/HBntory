import { ApiError } from './api.js';
import { getCurrentUser, login } from './auth.js';
import { redirectAuthenticatedUser, redirectByRole } from './guards.js';
import {
  clearFieldError,
  getApiErrorMessage,
  hideAlert,
  setButtonBusy,
  setText,
  setVisible,
  showAlert,
  showFieldError
} from './ui.js';

const form = document.querySelector('#login-form');
const usernameInput = document.querySelector('#username');
const usernameError = document.querySelector('#username-error');
const passwordInput = document.querySelector('#password');
const passwordError = document.querySelector('#password-error');
const passwordToggle = document.querySelector('#password-toggle');
const passwordToggleText = passwordToggle?.querySelector(
  '.password-field__toggle-text'
);
const submitButton = document.querySelector('#login-submit');
const loadingElement = document.querySelector('#login-loading');
const errorContainer = document.querySelector('#login-error');
const errorMessage = document.querySelector('#login-error-message');

function validateForm () {
  let valid = true;

  clearFieldError(usernameInput, usernameError);
  clearFieldError(passwordInput, passwordError);

  if (!usernameInput.value.trim()) {
    showFieldError(
      usernameInput,
      usernameError,
      'Veuillez saisir votre identifiant.'
    );
    valid = false;
  }

  if (!passwordInput.value) {
    showFieldError(
      passwordInput,
      passwordError,
      'Veuillez saisir votre mot de passe.'
    );
    valid = false;
  }

  return valid;
}

function togglePasswordVisibility () {
  const passwordWillBeVisible = passwordInput.type === 'password';

  passwordInput.type = passwordWillBeVisible ? 'text' : 'password';
  passwordToggle.setAttribute('aria-pressed', String(passwordWillBeVisible));
  passwordToggle.setAttribute(
    'aria-label',
    passwordWillBeVisible
      ? 'Masquer le mot de passe'
      : 'Afficher le mot de passe'
  );
  setText(passwordToggleText, passwordWillBeVisible ? 'Masquer' : 'Afficher');
}

async function handleSubmit (event) {
  event.preventDefault();
  hideAlert(errorContainer);

  if (!validateForm()) {
    return;
  }

  setButtonBusy(submitButton, true, 'Connexion…');
  setVisible(loadingElement, true);

  try {
    const loginResult = await login(
      usernameInput.value.trim(),
      passwordInput.value
    );

    const user = loginResult?.user ?? (await getCurrentUser());
    redirectByRole(user.role);
  } catch (error) {
    const message =
      error instanceof ApiError &&
      (error.status === 401 || error.status === 403)
        ? 'Identifiants incorrects ou compte indisponible.'
        : getApiErrorMessage(error);

    showAlert(errorContainer, errorMessage, message);
    passwordInput.value = '';
    passwordInput.focus();
  } finally {
    setButtonBusy(submitButton, false);
    setVisible(loadingElement, false);
  }
}

async function initializeLoginPage () {
  if (!form) {
    return;
  }

  passwordToggle?.addEventListener('click', togglePasswordVisibility);
  form.addEventListener('submit', handleSubmit);

  usernameInput.addEventListener('input', () => {
    clearFieldError(usernameInput, usernameError);
    hideAlert(errorContainer);
  });

  passwordInput.addEventListener('input', () => {
    clearFieldError(passwordInput, passwordError);
    hideAlert(errorContainer);
  });

  await redirectAuthenticatedUser();
}

initializeLoginPage();
