import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { HeartPulse, Users, Activity, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const { data } = await api.get('/api/dashboard');
        setData(data);
      } catch (err) {
        console.error('Dashboard fetch failed:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-32 rounded-xl animate-shimmer"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!data) return <div className="text-center py-12 text-gray-500">Failed to load dashboard</div>;

  const stats = [
    {
      label: 'Total Needs',
      value: data.total_needs,
      icon: HeartPulse,
      color: 'text-red-600',
      bg: 'bg-red-50',
      border: 'border-red-100',
    },
    {
      label: 'Active Volunteers',
      value: data.available_volunteers,
      sub: `of ${data.total_volunteers} total`,
      icon: Users,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
      border: 'border-blue-100',
    },
    {
      label: 'High Priority',
      value: data.high_priority_needs,
      icon: AlertTriangle,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
      border: 'border-amber-100',
    },
    {
      label: 'Avg Priority Score',
      value: data.average_priority_score,
      icon: TrendingUp,
      color: 'text-green-600',
      bg: 'bg-green-50',
      border: 'border-green-100',
    },
  ];

  const categoryColors = {
    food: 'bg-orange-400',
    medical: 'bg-red-400',
    water: 'bg-blue-400',
    shelter: 'bg-indigo-400',
    education: 'bg-purple-400',
    logistics: 'bg-teal-400',
    general: 'bg-gray-400',
  };

  const urgencyColors = {
    high: 'bg-red-500',
    medium: 'bg-amber-500',
    low: 'bg-green-500',
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <header>
        <h1 className="text-2xl font-bold text-gray-900">System Overview</h1>
        <p className="text-gray-500">Real-time engagement and operational readiness</p>
      </header>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className={`p-6 bg-white rounded-xl shadow-sm border ${stat.border} hover:shadow-md transition-shadow`}>
            <div className={`w-12 h-12 ${stat.bg} ${stat.color} rounded-lg flex items-center justify-center mb-4`}>
              <stat.icon size={24} />
            </div>
            <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">{stat.label}</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">{stat.value}</p>
            {stat.sub && <p className="text-xs text-gray-400 mt-1">{stat.sub}</p>}
          </div>
        ))}
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-white rounded-xl border border-gray-100 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-3 h-3 bg-amber-400 rounded-full"></div>
            <span className="text-sm font-semibold text-gray-700">Pending</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{data.pending_needs}</p>
        </div>
        <div className="p-6 bg-white rounded-xl border border-gray-100 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
            <span className="text-sm font-semibold text-gray-700">Assigned</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{data.assigned_needs}</p>
        </div>
        <div className="p-6 bg-white rounded-xl border border-gray-100 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-3 h-3 bg-green-400 rounded-full"></div>
            <span className="text-sm font-semibold text-gray-700">Completed</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{data.completed_needs}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="p-6 bg-white rounded-xl border border-gray-100 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Category Breakdown</h2>
          <div className="space-y-3">
            {Object.entries(data.category_breakdown || {}).map(([cat, count]) => (
              <div key={cat} className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${categoryColors[cat] || 'bg-gray-400'}`}></div>
                <span className="text-sm text-gray-600 capitalize flex-1">{cat}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${categoryColors[cat] || 'bg-gray-400'}`}
                    style={{ width: `${Math.min(100, (count / data.total_needs) * 100)}%` }}
                  ></div>
                </div>
                <span className="text-sm font-semibold text-gray-700 w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Urgency Breakdown */}
        <div className="p-6 bg-white rounded-xl border border-gray-100 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Urgency Distribution</h2>
          <div className="space-y-4">
            {Object.entries(data.urgency_breakdown || {}).map(([urgency, count]) => (
              <div key={urgency} className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${urgencyColors[urgency] || 'bg-gray-400'}`}></div>
                <span className="text-sm text-gray-600 capitalize flex-1">{urgency}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${urgencyColors[urgency] || 'bg-gray-400'}`}
                    style={{ width: `${Math.min(100, (count / data.total_needs) * 100)}%` }}
                  ></div>
                </div>
                <span className="text-sm font-semibold text-gray-700 w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
