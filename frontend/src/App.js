import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Needs from './pages/Needs';
import Volunteers from './pages/Volunteers';
import Upload from './pages/Upload';
import Profile from './pages/Profile';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import VolunteerTasks from './pages/VolunteerTasks';
import ProtectedRoute from './components/ProtectedRoute';
import Unauthorized from './pages/Unauthorized';

// New multi-NGO pages
import NgoManagement from './pages/NgoManagement';
import ResourceInventory from './pages/ResourceInventory';
import PoolRequests from './pages/PoolRequests';
import Analytics from './pages/Analytics';
import Leaderboard from './pages/Leaderboard';

const ProtectedLayout = () => {
  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6">
          <Routes>
            <Route path="/dashboard" element={
              <ProtectedRoute allowedRoles={['admin', 'ngo', 'volunteer']}>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/needs" element={
              <ProtectedRoute allowedRoles={['admin', 'ngo']}>
                <Needs />
              </ProtectedRoute>
            } />
            <Route path="/profile" element={
              <ProtectedRoute allowedRoles={['admin', 'ngo', 'volunteer']}>
                <Profile />
              </ProtectedRoute>
            } />
            <Route path="/tasks" element={
              <ProtectedRoute allowedRoles={['volunteer']}>
                <VolunteerTasks />
              </ProtectedRoute>
            } />
            <Route path="/upload" element={
              <ProtectedRoute allowedRoles={['admin', 'ngo', 'volunteer']}>
                <Upload />
              </ProtectedRoute>
            } />
            <Route path="/volunteers" element={
              <ProtectedRoute allowedRoles={['admin', 'ngo']}>
                <Volunteers />
              </ProtectedRoute>
            } />

            {/* ── New Federation Routes ── */}
            <Route path="/ngo-management" element={
              <ProtectedRoute allowedRoles={['admin']}>
                <NgoManagement />
              </ProtectedRoute>
            } />
            <Route path="/resources" element={
              <ProtectedRoute allowedRoles={['admin', 'ngo']}>
                <ResourceInventory />
              </ProtectedRoute>
            } />
            <Route path="/pool-requests" element={
              <ProtectedRoute allowedRoles={['admin', 'ngo']}>
                <PoolRequests />
              </ProtectedRoute>
            } />
            <Route path="/analytics" element={
              <ProtectedRoute allowedRoles={['admin', 'ngo']}>
                <Analytics />
              </ProtectedRoute>
            } />
            <Route path="/leaderboard" element={
              <ProtectedRoute allowedRoles={['admin', 'ngo', 'volunteer']}>
                <Leaderboard />
              </ProtectedRoute>
            } />

            <Route path="/unauthorized" element={<Unauthorized />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

const App = () => {
  const isAuthenticated = !!localStorage.getItem('token');

  return (
    <Router>
      <Routes>
        {/* Public landing page */}
        <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route
          path="/*"
          element={
            isAuthenticated ? (
              <ProtectedLayout />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
      </Routes>
    </Router>
  );
};

export default App;
