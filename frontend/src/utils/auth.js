/**
 * Role-Based Access Control and Authentication Helpers
 */

export const getRole = () => {
  return localStorage.getItem('role') || null;
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('token');
};

export const isAdmin = () => {
  return getRole() === 'admin';
};

export const isNGO = () => {
  return getRole() === 'ngo';
};

export const isVolunteer = () => {
  return getRole() === 'volunteer';
};
