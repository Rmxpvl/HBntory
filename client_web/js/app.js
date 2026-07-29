import { AiApiError, sendQuestion } from './api.js';
import {
  getPublicErrorMessage,
  setButtonBusy,
  setText,
  setVisible,
  showResultState
} from './ui.js';

const form = document.querySelector('#query-form');
const questionInput = document.querySelector('#question');
const questionError = document.querySelector('#question-error');
const characterCount = document.querySelector('#question-character-count');
const submitButton = document.querySelector('#query-submit');

const exampleButtons = document.querySelectorAll('.query-example');

const loadingElement = document.querySelector('#query-loading');
const errorElement = document.querySelector('#query-error');
const errorMessage = document.querySelector('#query-error-message');
const retryButton = document.querySelector('#retry-query-button');

const resultElement = document.querySelector('#query-result');
const answerElement = document.querySelector('#query-answer');
const newQueryButton = document.querySelector('#new-query-button');

let lastQuestion = '';
let activeRequestController = null;

const resultElements = {
  loadingElement,
  errorElement,
  resultElement
};

function updateCharacterCount () {
  setText(characterCount, questionInput.value.length);
}

function clearQuestionError () {
  questionInput.removeAttribute('aria-invalid');
  setVisible(questionError, false);
}

function showQuestionError (message) {
  questionInput.setAttribute('aria-invalid', 'true');
  setText(questionError, message);
  setVisible(questionError, true);
}

function validateQuestion () {
  const question = questionInput.value.trim();

  clearQuestionError();

  if (!question) {
    showQuestionError('Saisissez une question avant de lancer la recherche.');
    questionInput.focus();
    return null;
  }

  if (question.length < 3) {
    showQuestionError('La question doit contenir au moins trois caractères.');
    questionInput.focus();
    return null;
  }

  if (question.length > questionInput.maxLength) {
    showQuestionError(
      `La question ne doit pas dépasser ${questionInput.maxLength} caractères.`
    );
    questionInput.focus();
    return null;
  }

  return question;
}

function extractAnswer (data) {
  const answer = data?.answer ?? data?.response ?? data?.result;

  return typeof answer === 'string' && answer.trim() ? answer.trim() : null;
}

async function runQuery (question) {
  lastQuestion = question;
  activeRequestController?.abort();
  const requestController = new AbortController();
  activeRequestController = requestController;

  clearQuestionError();
  setText(answerElement, '');
  setButtonBusy(submitButton, true, 'Recherche…');
  showResultState('loading', resultElements);

  try {
    const data = await sendQuestion(question, requestController.signal);
    const answer = extractAnswer(data);

    if (!answer) {
      throw new AiApiError(
        502,
        'Le service n’a renvoyé aucune réponse exploitable.',
        'EMPTY_ANSWER'
      );
    }

    /*
     * textContent est volontaire : une réponse produite par l’IA ne doit
     * jamais être injectée dans la page avec innerHTML.
     */
    setText(answerElement, answer);
    showResultState('success', resultElements);
    answerElement.focus();
  } catch (error) {
    if (error?.code === 'REQUEST_ABORTED') {
      return;
    }

    setText(errorMessage, getPublicErrorMessage(error));
    showResultState('error', resultElements);
    errorElement.focus?.();
  } finally {
    if (activeRequestController === requestController) {
      setButtonBusy(submitButton, false);
      activeRequestController = null;
    }
  }
}

async function handleSubmit (event) {
  event.preventDefault();

  const question = validateQuestion();

  if (!question) {
    return;
  }

  await runQuery(question);
}

function useExampleQuestion (button) {
  const question = button.dataset.question ?? '';

  questionInput.value = question;
  updateCharacterCount();
  clearQuestionError();
  questionInput.focus();
  questionInput.setSelectionRange(question.length, question.length);
}

function resetQueryPage () {
  activeRequestController?.abort();
  form.reset();
  lastQuestion = '';
  setText(answerElement, '');
  updateCharacterCount();
  clearQuestionError();
  showResultState('idle', resultElements);
  questionInput.focus();
}

function bindEvents () {
  form.addEventListener('submit', handleSubmit);

  questionInput.addEventListener('input', () => {
    updateCharacterCount();
    clearQuestionError();
  });

  exampleButtons.forEach((button) => {
    button.addEventListener('click', () => useExampleQuestion(button));
  });

  retryButton.addEventListener('click', () => {
    if (lastQuestion) {
      runQuery(lastQuestion);
    }
  });

  newQueryButton.addEventListener('click', resetQueryPage);
}

function initializePublicClient () {
  errorElement.setAttribute('tabindex', '-1');
  bindEvents();
  updateCharacterCount();
  showResultState('idle', resultElements);
}

initializePublicClient();
