export const API_ROUTES = Object.freeze({
  login: '/auth/login',
  currentUser: '/auth/me',
  logout: '/auth/logout',
  stock: '/stock',
  addStock: '/stock/add',
  removeStock: '/stock/remove',
  products: '/products',
  users: '/users',
  branches: '/branches',
  user (userId) {
    return `/users/${encodeURIComponent(userId)}`;
  },
  userPassword (userId) {
    return `/users/${encodeURIComponent(userId)}/password`;
  }
});
