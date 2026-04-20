import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { isAuthenticated, getRole } from '../utils/auth';

const ProtectedRoute = ({ children, allowedRoles }) => {
  const location = useLocation();
  const auth = isAuthenticated();
  const role = getRole();

  if (!auth) {
    // Redirect to login if not authenticated
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(role)) {
    // Redirect to unauthorized if authenticated but missing the required role
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
};

export default ProtectedRoute;
