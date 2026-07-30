import { fetchCategories, fetchProducts, PublicApiError } from './api.js';
import {
  populateCategoryOptions,
  renderProductGrid,
  setText,
  setVisible,
  showCatalogueState
} from './ui.js';

const form = document.querySelector('#catalogue-form');
const searchInput = document.querySelector('#search-input');
const categorySelect = document.querySelector('#category-select');
const submitButton = document.querySelector('#catalogue-submit');

const loadingElement = document.querySelector('#catalogue-loading');
const errorElement = document.querySelector('#catalogue-error');
const errorMessage = document.querySelector('#catalogue-error-message');
const retryButton = document.querySelector('#retry-catalogue-button');
const emptyElement = document.querySelector('#catalogue-empty');
const resultsElement = document.querySelector('#product-grid');

const stateElements = {
  loadingElement,
  errorElement,
  emptyElement,
  resultsElement
};

let activeController = null;

function getPublicErrorMessage (error) {
  if (error instanceof PublicApiError && error.status === 502) {
    return 'Le catalogue produit est temporairement indisponible.';
  }

  return error?.message || 'Une erreur inattendue est survenue.';
}

async function loadProducts () {
  activeController?.abort();
  const controller = new AbortController();
  activeController = controller;

  const filters = {
    q: searchInput.value.trim(),
    category: categorySelect.value
  };

  submitButton.disabled = true;
  showCatalogueState('loading', stateElements);

  try {
    const products = await fetchProducts(filters, controller.signal);

    if (products.length === 0) {
      showCatalogueState('empty', stateElements);
    } else {
      renderProductGrid(resultsElement, products);
      showCatalogueState('results', stateElements);
    }
  } catch (error) {
    if (error?.status === 0 && error.message === 'La requête a été annulée.') {
      return;
    }

    setText(errorMessage, getPublicErrorMessage(error));
    showCatalogueState('error', stateElements);
  } finally {
    if (activeController === controller) {
      submitButton.disabled = false;
      activeController = null;
    }
  }
}

async function loadCategories () {
  try {
    const categories = await fetchCategories();
    populateCategoryOptions(categorySelect, categories);
  } catch {
    // The category filter is a nice-to-have: if it fails to load, the
    // search box and "all categories" still work fine on their own.
  }
}

function handleSubmit (event) {
  event.preventDefault();
  loadProducts();
}

function initializePublicClient () {
  form.addEventListener('submit', handleSubmit);
  retryButton.addEventListener('click', loadProducts);

  loadCategories();
  loadProducts();
}

initializePublicClient();
