import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';

const Unauthorized = () => {
  return (
    <div className="flex flex-col items-center justify-center h-full animate-fade-in text-center p-6">
      <div className="w-24 h-24 bg-red-50 text-red-500 rounded-full flex items-center justify-center mb-6 shadow-sm">
        <ShieldAlert size={48} />
      </div>
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Access Denied</h1>
      <p className="text-gray-500 max-w-md mb-8">
        You do not have the required permissions to view this page. If you believe this is an error, please contact your system administrator.
      </p>
      
      <Link 
        to="/dashboard" 
        className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors shadow-sm"
      >
        Return to Dashboard
      </Link>
    </div>
  );
};

export default Unauthorized;
