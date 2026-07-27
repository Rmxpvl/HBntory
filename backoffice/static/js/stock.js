import { ApiError, apiRequest } from './api.js';
import { logout } from './auth.js';
import { ROLE_COMMON } from './config.js';
import { redirectToLogin, requireRole } from './guards.js';
import { API_ROUTES } from './routes.js';
import {
  bindDialogCloseButtons,
  closeDialog,
  getApiErrorMessage,
  hideAlert,
  isPositiveInteger,
  openDialog,
  setButtonBusy,
  setText,
  setVisible,
  showAlert,
  showToast
} from './ui.js';

const state = {
  currentUser: null,
  products: [],
  productsById: new Map(),
  stock: [],
  search: ''
};

const usernameElement = document.querySelector('#current-username');
const branchElement = document.querySelector('#current-branch-name');
const logoutButton = document.querySelector('#logout-button');

const productsCountElement = document.querySelector('#stock-products-count');
const totalQuantityElement = document.querySelector('#stock-total-quantity');

const searchForm = document.querySelector('#stock-search-form');
const searchInput = document.querySelector('#stock-search');
const resetSearchButton = document.querySelector('#reset-stock-search');

const loadingElement = document.querySelector('#stock-loading');
const errorContainer = document.querySelector('#stock-error');
const errorMessage = document.querySelector('#stock-error-message');
const retryButton = document.querySelector('#retry-stock-loading');
const emptyElement = document.querySelector('#stock-empty');
const emptyTitle = emptyElement?.querySelector('h3');
const emptyDescription = emptyElement?.querySelector('p');
const emptyAddButton = document.querySelector('#empty-add-stock-button');
const tableContainer = document.querySelector('#stock-table-container');
const tableBody = document.querySelector('#stock-table-body');

const notificationContainer = document.querySelector('#stock-notification');
const notificationMessage = document.querySelector(
  '#stock-notification-message'
);

const addDialog = document.querySelector('#add-stock-dialog');
const openAddButton = document.querySelector('#open-add-stock-dialog');
const addForm = document.querySelector('#add-stock-form');
const addProductSelect = document.querySelector('#add-product-id');
const addQuantityInput = document.querySelector('#add-quantity');
const addSubmitButton = document.querySelector('#add-stock-submit');
const addLoadingElement = document.querySelector('#add-stock-loading');
const addErrorContainer = document.querySelector('#add-stock-error');
const addErrorMessage = document.querySelector('#add-stock-error-message');

const removeDialog = document.querySelector('#remove-stock-dialog');
const openRemoveButton = document.querySelector('#open-remove-stock-dialog');
const removeForm = document.querySelector('#remove-stock-form');
const removeProductSelect = document.querySelector('#remove-product-id');
const removeQuantityInput = document.querySelector('#remove-quantity');
const removeAvailability = document.querySelector('#selected-product-stock');
const removeSubmitButton = document.querySelector('#remove-stock-submit');
const removeLoadingElement = document.querySelector('#remove-stock-loading');
const removeErrorContainer = document.querySelector('#remove-stock-error');
const removeErrorMessage = document.querySelector(
  '#remove-stock-error-message'
);

function extractArray (data, possibleKeys) {
  if (Array.isArray(data)) {
    return data;
  }

  for (const key of possibleKeys) {
    if (Array.isArray(data?.[key])) {
      return data[key];
    }
  }

  return [];
}

function getProductId (value) {
  return String(value?.product_id ?? value?.id ?? '');
}

function normalizeProducts (data) {
  return extractArray(data, ['products', 'items', 'results']).filter(
    (product) => getProductId(product)
  );
}

function normalizeStock (data) {
  return extractArray(data, ['stock', 'items', 'stocks'])
    .map((item) => ({
      ...item,
      product_id: getProductId(item),
      quantity: Number(item.quantity ?? item.available_quantity ?? 0)
    }))
    .filter(
      (item) =>
        item.product_id && Number.isFinite(item.quantity) && item.quantity >= 0
    );
}

function getProductForStockItem (item) {
  return (
    item.product ??
    state.productsById.get(item.product_id) ?? {
      id: item.product_id,
      name: `Produit ${item.product_id}`,
      description: 'Informations produit indisponibles.'
    }
  );
}

function getProductName (product, productId) {
  return product?.name ?? product?.title ?? `Produit ${productId}`;
}

function getPositiveStock () {
  return state.stock.filter((item) => item.quantity > 0);
}

function getFilteredStock () {
  const positiveStock = getPositiveStock();
  const search = state.search.trim().toLowerCase();

  if (!search) {
    return positiveStock;
  }

  return positiveStock.filter((item) => {
    const product = getProductForStockItem(item);
    const productName = getProductName(product, item.product_id).toLowerCase();

    return (
      item.product_id.toLowerCase().includes(search) ||
      productName.includes(search)
    );
  });
}

function createCell (text, className = null) {
  const cell = document.createElement('td');

  if (className) {
    cell.className = className;
  }

  cell.textContent = String(text);
  return cell;
}

function createProductCell (item) {
  const product = getProductForStockItem(item);
  const cell = document.createElement('td');
  const container = document.createElement('div');
  const name = document.createElement('span');
  const description = document.createElement('span');

  container.className = 'product-cell';
  name.className = 'product-cell__name';
  description.className = 'product-cell__description';

  name.textContent = getProductName(product, item.product_id);
  description.textContent =
    product.description ??
    product.short_description ??
    'Aucune description disponible.';

  container.append(name, description);
  cell.append(container);
  return cell;
}

function createActionButton (label, action, productId, danger = false) {
  const button = document.createElement('button');

  button.type = 'button';
  button.className = danger
    ? 'table-action table-action--danger'
    : 'table-action';
  button.dataset.action = action;
  button.dataset.productId = productId;
  button.textContent = label;
  return button;
}

function createStockRow (item) {
  const row = document.createElement('tr');
  const quantityCell = createCell(item.quantity, 'quantity-value');
  const actionsCell = document.createElement('td');
  const actions = document.createElement('div');

  actions.className = 'data-table__actions';
  actions.append(
    createActionButton('Ajouter', 'add', item.product_id),
    createActionButton('Retirer', 'remove', item.product_id, true)
  );

  actionsCell.append(actions);
  row.append(
    createCell(item.product_id),
    createProductCell(item),
    quantityCell,
    actionsCell
  );

  return row;
}

function updateSummary () {
  const positiveStock = getPositiveStock();
  const totalQuantity = positiveStock.reduce(
    (total, item) => total + item.quantity,
    0
  );

  setText(productsCountElement, positiveStock.length);
  setText(totalQuantityElement, totalQuantity);
}

function renderEmptyState (filteredStock) {
  const stockIsEmpty = getPositiveStock().length === 0;

  setText(
    emptyTitle,
    stockIsEmpty
      ? 'Aucun produit en stock'
      : 'Aucun produit ne correspond à la recherche'
  );
  setText(
    emptyDescription,
    stockIsEmpty
      ? 'Ajoutez un produit pour commencer à gérer le stock de cette branche.'
      : 'Modifiez ou réinitialisez votre recherche.'
  );
  setVisible(emptyAddButton, stockIsEmpty);
  setVisible(emptyElement, filteredStock.length === 0);
}

function renderStock () {
  const filteredStock = getFilteredStock();

  tableBody.replaceChildren(
    ...filteredStock.map((item) => createStockRow(item))
  );

  updateSummary();
  renderEmptyState(filteredStock);
  setVisible(tableContainer, filteredStock.length > 0);
}

function replaceSelectOptions (select, items, selectedValue = '') {
  const placeholder = document.createElement('option');

  placeholder.value = '';
  placeholder.textContent = 'Sélectionnez un produit';
  select.replaceChildren(placeholder);

  items.forEach((item) => {
    const productId = getProductId(item);
    const product = item.product ?? state.productsById.get(productId) ?? item;
    const option = document.createElement('option');

    option.value = productId;
    option.textContent = `${productId} — ${getProductName(product, productId)}`;
    select.append(option);
  });

  select.value = selectedValue;
}

function populateAddProductSelect (selectedProductId = '') {
  replaceSelectOptions(addProductSelect, state.products, selectedProductId);
}

function populateRemoveProductSelect (selectedProductId = '') {
  replaceSelectOptions(
    removeProductSelect,
    getPositiveStock(),
    selectedProductId
  );
  updateRemoveAvailability();
}

function updateRemoveAvailability () {
  const selectedItem = state.stock.find(
    (item) => item.product_id === removeProductSelect.value
  );

  if (!selectedItem) {
    setText(removeAvailability, '');
    setVisible(removeAvailability, false);
    removeQuantityInput.removeAttribute('max');
    return;
  }

  removeQuantityInput.max = String(selectedItem.quantity);
  setText(
    removeAvailability,
    `Quantité actuellement disponible : ${selectedItem.quantity}`
  );
  setVisible(removeAvailability, true);
}

function openAddStockDialog (productId = '') {
  addForm.reset();
  hideAlert(addErrorContainer);
  populateAddProductSelect(productId);
  openDialog(addDialog);
  addProductSelect.focus();
}

function openRemoveStockDialog (productId = '') {
  removeForm.reset();
  hideAlert(removeErrorContainer);
  populateRemoveProductSelect(productId);
  openDialog(removeDialog);
  removeProductSelect.focus();
}

function validateQuantity (input) {
  const quantity = Number(input.value);

  input.setCustomValidity('');

  if (!isPositiveInteger(quantity)) {
    input.setCustomValidity(
      'La quantité doit être un entier supérieur à zéro.'
    );
    input.reportValidity();
    return null;
  }

  return quantity;
}

async function loadStockData () {
  setVisible(loadingElement, true);
  setVisible(errorContainer, false);
  setVisible(emptyElement, false);
  setVisible(tableContainer, false);

  try {
    const [stockData, productsData] = await Promise.all([
      apiRequest(API_ROUTES.stock),
      apiRequest(API_ROUTES.products)
    ]);

    state.products = normalizeProducts(productsData);
    state.productsById = new Map(
      state.products.map((product) => [getProductId(product), product])
    );
    state.stock = normalizeStock(stockData);

    populateAddProductSelect();
    populateRemoveProductSelect();
    renderStock();
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      redirectToLogin();
      return;
    }

    showAlert(errorContainer, errorMessage, getApiErrorMessage(error));
  } finally {
    setVisible(loadingElement, false);
  }
}

async function handleAddStock (event) {
  event.preventDefault();
  hideAlert(addErrorContainer);

  if (!addForm.checkValidity()) {
    addForm.reportValidity();
    return;
  }

  const quantity = validateQuantity(addQuantityInput);

  if (quantity === null) {
    return;
  }

  setButtonBusy(addSubmitButton, true, 'Ajout…');
  setVisible(addLoadingElement, true);

  try {
    await apiRequest(API_ROUTES.addStock, {
      method: 'POST',
      body: JSON.stringify({
        product_id: addProductSelect.value,
        quantity
      })
    });

    closeDialog(addDialog);
    await loadStockData();
    showToast(
      notificationContainer,
      notificationMessage,
      `${quantity} unité(s) ajoutée(s) au stock.`
    );
  } catch (error) {
    showAlert(addErrorContainer, addErrorMessage, getApiErrorMessage(error));
  } finally {
    setButtonBusy(addSubmitButton, false);
    setVisible(addLoadingElement, false);
  }
}

async function handleRemoveStock (event) {
  event.preventDefault();
  hideAlert(removeErrorContainer);

  if (!removeForm.checkValidity()) {
    removeForm.reportValidity();
    return;
  }

  const quantity = validateQuantity(removeQuantityInput);
  const selectedItem = state.stock.find(
    (item) => item.product_id === removeProductSelect.value
  );

  if (quantity === null) {
    return;
  }

  if (!selectedItem || quantity > selectedItem.quantity) {
    showAlert(
      removeErrorContainer,
      removeErrorMessage,
      `Impossible de retirer ${quantity} unité(s) : seulement ${
        selectedItem?.quantity ?? 0
      } disponible(s).`
    );
    return;
  }

  setButtonBusy(removeSubmitButton, true, 'Retrait…');
  setVisible(removeLoadingElement, true);

  try {
    await apiRequest(API_ROUTES.removeStock, {
      method: 'POST',
      body: JSON.stringify({
        product_id: removeProductSelect.value,
        quantity
      })
    });

    closeDialog(removeDialog);
    await loadStockData();
    showToast(
      notificationContainer,
      notificationMessage,
      `${quantity} unité(s) retirée(s) du stock.`
    );
  } catch (error) {
    showAlert(
      removeErrorContainer,
      removeErrorMessage,
      getApiErrorMessage(error)
    );
  } finally {
    setButtonBusy(removeSubmitButton, false);
    setVisible(removeLoadingElement, false);
  }
}

async function handleLogout () {
  setButtonBusy(logoutButton, true, 'Déconnexion…');

  try {
    await logout();
  } finally {
    redirectToLogin();
  }
}

function bindEvents () {
  bindDialogCloseButtons();

  logoutButton.addEventListener('click', handleLogout);
  retryButton.addEventListener('click', loadStockData);
  openAddButton.addEventListener('click', () => openAddStockDialog());
  emptyAddButton.addEventListener('click', () => openAddStockDialog());
  openRemoveButton.addEventListener('click', () => openRemoveStockDialog());

  addForm.addEventListener('submit', handleAddStock);
  removeForm.addEventListener('submit', handleRemoveStock);
  removeProductSelect.addEventListener('change', updateRemoveAvailability);

  searchForm.addEventListener('submit', (event) => {
    event.preventDefault();
    state.search = searchInput.value;
    renderStock();
  });

  searchInput.addEventListener('input', () => {
    state.search = searchInput.value;
    renderStock();
  });

  resetSearchButton.addEventListener('click', () => {
    searchForm.reset();
    state.search = '';
    renderStock();
    searchInput.focus();
  });

  tableBody.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-action]');

    if (!button) {
      return;
    }

    if (button.dataset.action === 'add') {
      openAddStockDialog(button.dataset.productId);
    }

    if (button.dataset.action === 'remove') {
      openRemoveStockDialog(button.dataset.productId);
    }
  });
}

async function initializeStockPage () {
  bindEvents();

  try {
    state.currentUser = await requireRole(ROLE_COMMON);

    if (!state.currentUser) {
      return;
    }

    setText(usernameElement, state.currentUser.username);
    setText(
      branchElement,
      state.currentUser.branch?.name ??
        state.currentUser.branch_name ??
        'Branche non renseignée'
    );

    await loadStockData();
  } catch (error) {
    showAlert(errorContainer, errorMessage, getApiErrorMessage(error));
    setVisible(loadingElement, false);
  }
}

initializeStockPage();
