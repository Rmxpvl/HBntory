import { ApiError, apiRequest } from './api.js';
import { logout } from './auth.js';
import { ROLE_ADMIN } from './config.js';
import { redirectToLogin, requireRole } from './guards.js';
import { API_ROUTES } from './routes.js';
import {
  bindDialogCloseButtons,
  closeDialog,
  getApiErrorMessage,
  hideAlert,
  openDialog,
  setButtonBusy,
  setText,
  setVisible,
  showAlert,
  showToast
} from './ui.js';

const state = {
  currentUser: null,
  users: [],
  branches: [],
  filters: {
    search: '',
    branchId: '',
    status: ''
  }
};

const usernameElement = document.querySelector('#current-username');
const logoutButton = document.querySelector('#logout-button');

const filterForm = document.querySelector('#users-filter-form');
const searchInput = document.querySelector('#users-search');
const branchFilter = document.querySelector('#branch-filter');
const statusFilter = document.querySelector('#status-filter');
const resetFiltersButton = document.querySelector('#reset-users-filters');

const loadingElement = document.querySelector('#users-loading');
const errorContainer = document.querySelector('#users-error');
const errorMessage = document.querySelector('#users-error-message');
const retryButton = document.querySelector('#retry-users-loading');
const emptyElement = document.querySelector('#users-empty');
const tableContainer = document.querySelector('#users-table-container');
const tableBody = document.querySelector('#users-table-body');

const notificationContainer = document.querySelector('#users-notification');
const notificationMessage = document.querySelector(
  '#users-notification-message'
);

const createDialog = document.querySelector('#create-user-dialog');
const openCreateButton = document.querySelector('#open-create-user-dialog');
const createForm = document.querySelector('#create-user-form');
const createUsernameInput = document.querySelector('#create-username');
const createBranchSelect = document.querySelector('#create-branch-id');
const createPasswordInput = document.querySelector('#create-password');
const createPasswordConfirmationInput = document.querySelector(
  '#create-password-confirmation'
);
const createSubmitButton = document.querySelector('#create-user-submit');
const createLoadingElement = document.querySelector('#create-user-loading');
const createErrorContainer = document.querySelector('#create-user-error');
const createErrorMessage = document.querySelector('#create-user-error-message');

const editDialog = document.querySelector('#edit-user-dialog');
const editForm = document.querySelector('#edit-user-form');
const editUserIdInput = document.querySelector('#edit-user-id');
const editUsernameInput = document.querySelector('#edit-username');
const editBranchSelect = document.querySelector('#edit-branch-id');
const editSubmitButton = document.querySelector('#edit-user-submit');
const editErrorContainer = document.querySelector('#edit-user-error');
const editErrorMessage = document.querySelector('#edit-user-error-message');

const passwordDialog = document.querySelector('#password-dialog');
const passwordForm = document.querySelector('#password-form');
const passwordUserIdInput = document.querySelector('#password-user-id');
const passwordUsernameElement = document.querySelector('#password-username');
const newPasswordInput = document.querySelector('#new-password');
const newPasswordConfirmationInput = document.querySelector(
  '#new-password-confirmation'
);
const passwordSubmitButton = document.querySelector('#password-submit');
const passwordErrorContainer = document.querySelector('#password-form-error');
const passwordErrorMessage = document.querySelector(
  '#password-form-error-message'
);

const deleteDialog = document.querySelector('#delete-user-dialog');
const deleteForm = document.querySelector('#delete-user-form');
const deleteUserIdInput = document.querySelector('#delete-user-id');
const deleteUsernameElement = document.querySelector('#delete-username');
const deleteSubmitButton = document.querySelector('#delete-user-submit');
const deleteErrorContainer = document.querySelector('#delete-user-error');
const deleteErrorMessage = document.querySelector('#delete-user-error-message');

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

function getUserId (user) {
  return String(user?.id ?? user?.user_id ?? '');
}

function getBranchId (branchOrUser) {
  return String(
    branchOrUser?.branch_id ??
      branchOrUser?.branch?.id ??
      branchOrUser?.id ??
      ''
  );
}

function parseIdentifier (value) {
  return /^\d+$/.test(value) ? Number(value) : value;
}

function userIsDeleted (user) {
  return (
    user.is_deleted === true ||
    user.deleted === true ||
    user.active === false ||
    user.status === 'deleted' ||
    user.status === 'inactive'
  );
}

function normalizeUsers (data) {
  return extractArray(data, ['users', 'items', 'results']).filter((user) =>
    getUserId(user)
  );
}

function normalizeBranches (data) {
  return extractArray(data, ['branches', 'items', 'results']).filter((branch) =>
    getBranchId(branch)
  );
}

function getBranchName (user) {
  if (user.branch?.name) {
    return user.branch.name;
  }

  const branch = state.branches.find(
    (item) => getBranchId(item) === getBranchId(user)
  );

  return branch?.name ?? user.branch_name ?? 'Aucune';
}

function getFilteredUsers () {
  const search = state.filters.search.trim().toLowerCase();

  return state.users.filter((user) => {
    const deleted = userIsDeleted(user);
    const username = String(user.username ?? user.name ?? '').toLowerCase();
    const branchId = getBranchId(user);

    const searchMatches =
      !search ||
      username.includes(search) ||
      getBranchName(user).toLowerCase().includes(search);
    const branchMatches =
      !state.filters.branchId || branchId === state.filters.branchId;
    const statusMatches =
      !state.filters.status ||
      (state.filters.status === 'active' && !deleted) ||
      (state.filters.status === 'deleted' && deleted);

    return searchMatches && branchMatches && statusMatches;
  });
}

function createCell (text) {
  const cell = document.createElement('td');
  cell.textContent = String(text);
  return cell;
}

function createUserCell (user) {
  const cell = document.createElement('td');
  const container = document.createElement('div');
  const username = document.createElement('span');
  const identifier = document.createElement('span');

  container.className = 'user-cell';
  username.className = 'user-cell__name';
  identifier.className = 'user-cell__identifier';

  username.textContent = user.username ?? user.name ?? 'Utilisateur';
  identifier.textContent = `Identifiant interne : ${getUserId(user)}`;

  container.append(username, identifier);
  cell.append(container);
  return cell;
}

function createRoleCell (user) {
  const cell = document.createElement('td');
  const badge = document.createElement('span');
  const isAdmin = user.role === ROLE_ADMIN;

  badge.className = isAdmin ? 'role-badge role-badge--admin' : 'role-badge';
  badge.textContent = isAdmin ? 'Administrateur' : 'Utilisateur commun';

  cell.append(badge);
  return cell;
}

function createStatusCell (user) {
  const cell = document.createElement('td');
  const badge = document.createElement('span');
  const deleted = userIsDeleted(user);

  badge.className = deleted
    ? 'status-badge status-badge--deleted'
    : 'status-badge status-badge--active';
  badge.textContent = deleted ? 'Désactivé' : 'Actif';

  cell.append(badge);
  return cell;
}

function createActionButton (label, action, userId, danger = false) {
  const button = document.createElement('button');

  button.type = 'button';
  button.className = danger
    ? 'table-action table-action--danger'
    : 'table-action';
  button.dataset.action = action;
  button.dataset.userId = userId;
  button.textContent = label;

  return button;
}

function createActionsCell (user) {
  const cell = document.createElement('td');

  if (user.role === ROLE_ADMIN) {
    cell.textContent = 'Compte administrateur';
    return cell;
  }

  if (userIsDeleted(user)) {
    cell.textContent = 'Aucune action disponible';
    return cell;
  }

  const actions = document.createElement('div');
  const userId = getUserId(user);

  actions.className = 'data-table__actions';
  actions.append(
    createActionButton('Modifier', 'edit', userId),
    createActionButton('Mot de passe', 'password', userId),
    createActionButton('Désactiver', 'delete', userId, true)
  );

  cell.append(actions);
  return cell;
}

function createUserRow (user) {
  const row = document.createElement('tr');

  row.dataset.userId = getUserId(user);
  row.dataset.status = userIsDeleted(user) ? 'deleted' : 'active';
  row.append(
    createUserCell(user),
    createRoleCell(user),
    createCell(getBranchName(user)),
    createStatusCell(user),
    createActionsCell(user)
  );

  return row;
}

function renderUsers () {
  const filteredUsers = getFilteredUsers();

  tableBody.replaceChildren(
    ...filteredUsers.map((user) => createUserRow(user))
  );

  setVisible(emptyElement, filteredUsers.length === 0);
  setVisible(tableContainer, filteredUsers.length > 0);
}

function replaceBranchOptions (
  select,
  {
    includeAll = false,
    selectedValue = '',
    placeholder = 'Sélectionnez une branche'
  } = {}
) {
  const firstOption = document.createElement('option');

  firstOption.value = '';
  firstOption.textContent = includeAll ? 'Toutes les branches' : placeholder;
  select.replaceChildren(firstOption);

  state.branches.forEach((branch) => {
    const option = document.createElement('option');

    option.value = getBranchId(branch);
    option.textContent = branch.name ?? `Branche ${getBranchId(branch)}`;
    select.append(option);
  });

  select.value = selectedValue;
}

function populateBranchSelects () {
  replaceBranchOptions(branchFilter, {
    includeAll: true,
    selectedValue: state.filters.branchId
  });
  replaceBranchOptions(createBranchSelect);
  replaceBranchOptions(editBranchSelect);
}

function findUser (userId) {
  return state.users.find((user) => getUserId(user) === String(userId));
}

function openCreateUserDialog () {
  createForm.reset();
  hideAlert(createErrorContainer);
  replaceBranchOptions(createBranchSelect);
  openDialog(createDialog);
  createUsernameInput.focus();
}

function openEditUserDialog (userId) {
  const user = findUser(userId);

  if (!user || user.role === ROLE_ADMIN || userIsDeleted(user)) {
    return;
  }

  editForm.reset();
  hideAlert(editErrorContainer);
  editUserIdInput.value = getUserId(user);
  editUsernameInput.value = user.username ?? user.name ?? '';
  replaceBranchOptions(editBranchSelect, {
    selectedValue: getBranchId(user)
  });
  openDialog(editDialog);
  editUsernameInput.focus();
}

function openPasswordDialog (userId) {
  const user = findUser(userId);

  if (!user || user.role === ROLE_ADMIN || userIsDeleted(user)) {
    return;
  }

  passwordForm.reset();
  hideAlert(passwordErrorContainer);
  passwordUserIdInput.value = getUserId(user);
  setText(passwordUsernameElement, user.username ?? user.name);
  openDialog(passwordDialog);
  newPasswordInput.focus();
}

function openDeleteUserDialog (userId) {
  const user = findUser(userId);

  if (!user || user.role === ROLE_ADMIN || userIsDeleted(user)) {
    return;
  }

  deleteForm.reset();
  hideAlert(deleteErrorContainer);
  deleteUserIdInput.value = getUserId(user);
  setText(deleteUsernameElement, user.username ?? user.name);
  openDialog(deleteDialog);
  deleteSubmitButton.focus();
}

function validateMatchingPasswords (password, confirmation) {
  confirmation.setCustomValidity('');

  if (password.value !== confirmation.value) {
    confirmation.setCustomValidity(
      'Les deux mots de passe doivent être identiques.'
    );
    confirmation.reportValidity();
    return false;
  }

  return true;
}

async function loadUsersData () {
  setVisible(loadingElement, true);
  setVisible(errorContainer, false);
  setVisible(emptyElement, false);
  setVisible(tableContainer, false);

  try {
    const [usersData, branchesData] = await Promise.all([
      apiRequest(API_ROUTES.users),
      apiRequest(API_ROUTES.branches)
    ]);

    state.users = normalizeUsers(usersData);
    state.branches = normalizeBranches(branchesData);

    populateBranchSelects();
    renderUsers();
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

async function handleCreateUser (event) {
  event.preventDefault();
  hideAlert(createErrorContainer);

  if (!createForm.checkValidity()) {
    createForm.reportValidity();
    return;
  }

  if (
    !validateMatchingPasswords(
      createPasswordInput,
      createPasswordConfirmationInput
    )
  ) {
    return;
  }

  setButtonBusy(createSubmitButton, true, 'Création…');
  setVisible(createLoadingElement, true);

  try {
    await apiRequest(API_ROUTES.users, {
      method: 'POST',
      body: JSON.stringify({
        username: createUsernameInput.value.trim(),
        password: createPasswordInput.value,
        branch_id: parseIdentifier(createBranchSelect.value)
      })
    });

    closeDialog(createDialog);
    await loadUsersData();
    showToast(
      notificationContainer,
      notificationMessage,
      'L’utilisateur a été créé.'
    );
  } catch (error) {
    showAlert(
      createErrorContainer,
      createErrorMessage,
      getApiErrorMessage(error)
    );
  } finally {
    setButtonBusy(createSubmitButton, false);
    setVisible(createLoadingElement, false);
  }
}

async function handleEditUser (event) {
  event.preventDefault();
  hideAlert(editErrorContainer);

  if (!editForm.checkValidity()) {
    editForm.reportValidity();
    return;
  }

  setButtonBusy(editSubmitButton, true, 'Enregistrement…');

  try {
    await apiRequest(API_ROUTES.user(editUserIdInput.value), {
      method: 'PATCH',
      body: JSON.stringify({
        username: editUsernameInput.value.trim(),
        branch_id: parseIdentifier(editBranchSelect.value)
      })
    });

    closeDialog(editDialog);
    await loadUsersData();
    showToast(
      notificationContainer,
      notificationMessage,
      'Les informations de l’utilisateur ont été modifiées.'
    );
  } catch (error) {
    showAlert(editErrorContainer, editErrorMessage, getApiErrorMessage(error));
  } finally {
    setButtonBusy(editSubmitButton, false);
  }
}

async function handlePasswordChange (event) {
  event.preventDefault();
  hideAlert(passwordErrorContainer);

  if (!passwordForm.checkValidity()) {
    passwordForm.reportValidity();
    return;
  }

  if (
    !validateMatchingPasswords(newPasswordInput, newPasswordConfirmationInput)
  ) {
    return;
  }

  setButtonBusy(passwordSubmitButton, true, 'Modification…');

  try {
    await apiRequest(API_ROUTES.userPassword(passwordUserIdInput.value), {
      method: 'PATCH',
      body: JSON.stringify({
        password: newPasswordInput.value
      })
    });

    closeDialog(passwordDialog);
    showToast(
      notificationContainer,
      notificationMessage,
      'Le mot de passe a été modifié.'
    );
  } catch (error) {
    showAlert(
      passwordErrorContainer,
      passwordErrorMessage,
      getApiErrorMessage(error)
    );
  } finally {
    setButtonBusy(passwordSubmitButton, false);
  }
}

async function handleDeleteUser (event) {
  event.preventDefault();
  hideAlert(deleteErrorContainer);
  setButtonBusy(deleteSubmitButton, true, 'Désactivation…');

  try {
    await apiRequest(API_ROUTES.user(deleteUserIdInput.value), {
      method: 'DELETE'
    });

    closeDialog(deleteDialog);
    await loadUsersData();
    showToast(
      notificationContainer,
      notificationMessage,
      'L’utilisateur a été désactivé.'
    );
  } catch (error) {
    showAlert(
      deleteErrorContainer,
      deleteErrorMessage,
      getApiErrorMessage(error)
    );
  } finally {
    setButtonBusy(deleteSubmitButton, false);
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

function updateFilters () {
  state.filters.search = searchInput.value;
  state.filters.branchId = branchFilter.value;
  state.filters.status = statusFilter.value;
  renderUsers();
}

function bindEvents () {
  bindDialogCloseButtons();

  logoutButton.addEventListener('click', handleLogout);
  retryButton.addEventListener('click', loadUsersData);
  openCreateButton.addEventListener('click', openCreateUserDialog);

  createForm.addEventListener('submit', handleCreateUser);
  editForm.addEventListener('submit', handleEditUser);
  passwordForm.addEventListener('submit', handlePasswordChange);
  deleteForm.addEventListener('submit', handleDeleteUser);

  filterForm.addEventListener('submit', (event) => {
    event.preventDefault();
    updateFilters();
  });
  searchInput.addEventListener('input', updateFilters);
  branchFilter.addEventListener('change', updateFilters);
  statusFilter.addEventListener('change', updateFilters);

  resetFiltersButton.addEventListener('click', () => {
    filterForm.reset();
    state.filters = {
      search: '',
      branchId: '',
      status: ''
    };
    renderUsers();
    searchInput.focus();
  });

  tableBody.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-action]');

    if (!button) {
      return;
    }

    const { action, userId } = button.dataset;

    if (action === 'edit') {
      openEditUserDialog(userId);
    }

    if (action === 'password') {
      openPasswordDialog(userId);
    }

    if (action === 'delete') {
      openDeleteUserDialog(userId);
    }
  });
}

async function initializeUsersPage () {
  bindEvents();

  try {
    state.currentUser = await requireRole(ROLE_ADMIN);

    if (!state.currentUser) {
      return;
    }

    setText(usernameElement, state.currentUser.username);
    await loadUsersData();
  } catch (error) {
    showAlert(errorContainer, errorMessage, getApiErrorMessage(error));
    setVisible(loadingElement, false);
  }
}

initializeUsersPage();
