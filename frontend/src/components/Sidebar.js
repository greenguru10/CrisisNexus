import React from 'react';
import {
  LayoutDashboard, HeartPulse, Users, Upload, HelpCircle, LogOut,
  Building2, Package, Share2, BarChart3, Trophy, ClipboardList
} from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { getRole } from '../utils/auth';

const Sidebar = () => {
  const role = getRole();
  const location = useLocation();
  const ngoName = localStorage.getItem('ngo_name');

  const allNavItems = [
    // ── Shared ──────────────────────────────────────────────────
    { label: 'Dashboard',     icon: LayoutDashboard, path: '/dashboard',      roles: ['admin', 'ngo', 'volunteer'] },
    { label: 'My Tasks',      icon: ClipboardList,   path: '/tasks',           roles: ['volunteer'] },
    { label: 'Upload Report', icon: Upload,           path: '/upload',          roles: ['admin', 'ngo', 'volunteer'] },

    // ── Admin + NGO ──────────────────────────────────────────────
    { label: 'Needs',         icon: HeartPulse,      path: '/needs',           roles: ['admin', 'ngo'] },
    { label: 'Volunteers',    icon: Users,            path: '/volunteers',      roles: ['admin', 'ngo'] },
    { label: 'Analytics',     icon: BarChart3,        path: '/analytics',       roles: ['admin', 'ngo'] },
    { label: 'Resources',     icon: Package,          path: '/resources',       roles: ['admin', 'ngo'] },
    { label: 'Pool Requests', icon: Share2,           path: '/pool-requests',   roles: ['admin', 'ngo'] },

    // ── Admin only ───────────────────────────────────────────────
    { label: 'NGO Management',icon: Building2,        path: '/ngo-management',  roles: ['admin'] },

    // ── All roles ────────────────────────────────────────────────
    { label: 'Leaderboard',   icon: Trophy,           path: '/leaderboard',     roles: ['admin', 'ngo', 'volunteer'] },
  ];

  const navItems = allNavItems.filter(item => item.roles.includes(role));

  const handleLogout = () => {
    ['token', 'role', 'ngo_id', 'ngo_name'].forEach(k => localStorage.removeItem(k));
    window.location.href = '/';
  };

  // Section separator helper
  const sections = [
    { title: null,          items: navItems.filter(n => ['Dashboard','My Tasks','Upload Report'].includes(n.label)) },
    { title: 'Operations',  items: navItems.filter(n => ['Needs','Volunteers'].includes(n.label)) },
    { title: 'Federation',  items: navItems.filter(n => ['Analytics','Resources','Pool Requests','NGO Management'].includes(n.label)) },
    { title: 'Community',   items: navItems.filter(n => ['Leaderboard'].includes(n.label)) },
  ].filter(s => s.items.length > 0);

  return (
    <div className="w-64 bg-white border-r border-gray-100 flex flex-col h-full shadow-lg shadow-gray-100/50 z-50">
      {/* Brand */}
      <div className="p-6 border-b border-gray-50">
        <h1 className="text-xl font-bold text-blue-600 tracking-tight">🌍 CommunitySync</h1>
        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1">
          {role === 'admin' ? 'System Administrator' : role === 'ngo' ? (ngoName || 'NGO Coordinator') : 'Volunteer'}
        </p>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-4 py-4 overflow-y-auto space-y-4">
        {sections.map((section, si) => (
          <div key={si}>
            {section.title && (
              <p className="text-[10px] font-bold text-gray-300 uppercase tracking-widest px-4 mb-1">
                {section.title}
              </p>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.label}
                    to={item.path}
                    className={`flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all text-sm ${
                      isActive
                        ? 'bg-blue-50 text-blue-600 font-semibold'
                        : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                    }`}
                  >
                    <item.icon size={18} />
                    <span>{item.label}</span>
                    {item.label === 'NGO Management' && (
                      <span className="ml-auto text-[10px] font-bold bg-amber-100 text-amber-600 px-1.5 py-0.5 rounded-full">Admin</span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-50 space-y-1">
        <Link to="/profile" className="w-full flex items-center gap-3 px-4 py-2.5 text-gray-500 hover:bg-gray-50 rounded-xl transition-all text-sm">
          <HelpCircle size={18} /> Profile & Settings
        </Link>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-2.5 text-red-400 hover:bg-red-50 hover:text-red-500 rounded-xl transition-all text-sm"
        >
          <LogOut size={18} /> Log Out
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
