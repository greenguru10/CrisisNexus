import React from 'react';
import { getRole } from '../utils/auth';
import AdminDashboard from './dashboards/AdminDashboard';
import NgoDashboard from './dashboards/NgoDashboard';
import VolunteerTasks from './VolunteerTasks';

const Dashboard = () => {
  const role = getRole();

  if (role === 'admin') {
    return <AdminDashboard />;
  } else if (role === 'ngo') {
    return <NgoDashboard />;
  } else if (role === 'volunteer') {
    // We utilize VolunteerTasks as the dashboard landing view for Volunteers.
    return <VolunteerTasks />;
  }

  // Fallback
  return (
    <div className="p-12 text-center text-gray-500">
      Unknown role or not logged in.
    </div>
  );
};

export default Dashboard;
