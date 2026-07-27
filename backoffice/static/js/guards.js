import { ApiError } from './api.js';
import { getCurrentUser } from './auth.js';
import { ROLE_ADMIN, ROLE_COMMON } from './config.js';

const PAGE_BY_ROLE = {
  [ROLE_ADMIN]: './users.html',
  [ROLE_COMMON]: './stock.html'
};

export function redirectToLogin () {
  window.location.replace('./login.html');
}

export function redirectByRole (role) {
  const target = PAGE_BY_ROLE[role];

  if (!target) {
    redirectToLogin();
    return;
  }

  window.location.replace(target);
}

export async function requireRole (requiredRole) {
  try {
    const user = await getCurrentUser();

    if (
      !user ||
      user.is_deleted === true ||
      user.deleted === true ||
      user.active === false
    ) {
      redirectToLogin();
      return null;
    }

    if (user.role !== requiredRole) {
      redirectByRole(user.role);
      return null;
    }

    return user;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      redirectToLogin();
      return null;
    }

    throw error;
  }
}

export async function redirectAuthenticatedUser () {
  try {
    const user = await getCurrentUser();

    if (user?.role) {
      redirectByRole(user.role);
      return true;
    }
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 401) {
      return false;
    }
  }

  return false;
}
