import React from 'react';
import { LayoutDashboard, HeartPulse, Users, BarChart3, Upload, HelpCircle, LogOut } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

const Sidebar = () => {
  const role = localStorage.getItem('role') || 'volunteer';
  const location = useLocation();

  const allNavItems = [
    { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard', roles: ['admin', 'ngo', 'volunteer'] },
    { label: 'Needs', icon: HeartPulse, path: '/needs', roles: ['admin', 'ngo', 'volunteer'] },
    { label: 'Volunteers', icon: Users, path: '/volunteers', roles: ['admin', 'ngo'] },
    { label: 'Upload Report', icon: Upload, path: '/upload', roles: ['admin', 'ngo', 'volunteer'] },
  ];

  const navItems = allNavItems.filter(item => item.roles.includes(role));

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    window.location.href = '/login';
  };

  return (
    <div className="w-64 bg-white border-r border-gray-100 flex flex-col h-full shadow-lg shadow-gray-100/50 z-50">
      <div className="p-6">
        <h1 className="text-xl font-bold text-blue-600 tracking-tight">🌍 CommunitySync</h1>
        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1">Volunteer Coordination</p>
      </div>

      <nav className="flex-1 px-4 space-y-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.label}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                isActive ? 'bg-blue-50 text-blue-600 font-semibold' : 'text-gray-500 hover:bg-gray-50'
              }`}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-50 space-y-1">
        <button className="w-full flex items-center gap-3 px-4 py-3 text-gray-500 hover:bg-gray-50 rounded-xl transition-all">
          <HelpCircle size={20} /> Help Center
        </button>
        <button onClick={handleLogout} className="w-full flex items-center gap-3 px-4 py-3 text-red-500 hover:bg-red-50 rounded-xl transition-all">
          <LogOut size={20} /> Log Out
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
