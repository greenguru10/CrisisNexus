import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Bell, User } from 'lucide-react';
import { Link } from 'react-router-dom';

const TopBar = () => {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const { data } = await api.get('/auth/me');
        setUser(data);
      } catch (err) {
        // Not logged in or token expired
      }
    };
    fetchUser();
  }, []);

  return (
    <div className="h-16 bg-white border-b border-gray-100 flex items-center justify-between px-6 shadow-sm">
      <div>
        <h2 className="text-sm font-semibold text-gray-800">Smart Resource Allocation</h2>
        <p className="text-xs text-gray-400">Data-Driven Volunteer Coordination</p>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors">
          <Bell size={20} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        <div className="flex items-center gap-3 pl-4 border-l border-gray-100">
          <Link to="/profile" className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center hover:bg-blue-200 transition-colors">
            <User size={16} />
          </Link>
          <div className="flex flex-col">
            <Link to="/profile" className="text-sm font-medium text-gray-700 hover:text-blue-600 hover:underline">
              {user?.email || 'Loading...'}
            </Link>
            <p className="text-xs text-gray-400 capitalize">{user?.role || ''}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TopBar;
