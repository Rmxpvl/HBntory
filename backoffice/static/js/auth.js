import { apiRequest } from './api.js';
import { API_ROUTES } from './routes.js';

export async function login (username, password) {
  return apiRequest(API_ROUTES.login, {
    method: 'POST',
    body: JSON.stringify({
      username,
      password
    })
  });
}

export async function getCurrentUser () {
  const data = await apiRequest(API_ROUTES.currentUser);
  return data?.user ?? data;
}

export async function logout () {
  return apiRequest(API_ROUTES.logout, {
    method: 'POST'
  });
}
