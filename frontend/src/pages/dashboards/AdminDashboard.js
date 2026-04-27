import React, { useEffect, useState } from 'react';
import api from '../../services/api';
import { HeartPulse, Users, Activity, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

const AdminDashboard = () => {
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
    <div className="space-y-8 animate-fade-in-up">
      <header className="mb-10">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight mb-2">System Overview</h1>
        <p className="text-slate-500 font-medium">Real-time engagement and operational readiness across all NGOs</p>
      </header>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className={`p-6 bg-white rounded-2xl shadow-sm border ${stat.border} hover:shadow-xl hover:-translate-y-1 transition-all duration-300 relative overflow-hidden group`}>
            <div className={`absolute top-0 right-0 w-32 h-32 ${stat.bg} rounded-full blur-3xl -mr-16 -mt-16 opacity-50 group-hover:opacity-80 transition-opacity`}></div>
            <div className="relative z-10">
              <div className={`w-14 h-14 ${stat.bg} ${stat.color} rounded-2xl flex items-center justify-center mb-6 shadow-sm`}>
                <stat.icon size={26} strokeWidth={2.5} />
              </div>
              <p className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-1">{stat.label}</p>
              <p className="text-4xl font-black text-slate-900 tracking-tight">{stat.value}</p>
              {stat.sub && <p className="text-sm font-medium text-slate-400 mt-2">{stat.sub}</p>}
            </div>
          </div>
        ))}
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { label: 'Pending', count: data.pending_needs, color: 'bg-slate-400', ring: 'ring-slate-100' },
          { label: 'Assigned', count: data.assigned_needs, color: 'bg-amber-400', ring: 'ring-amber-100' },
          { label: 'Accepted', count: data.accepted_needs, color: 'bg-blue-500', ring: 'ring-blue-100' },
          { label: 'In Progress', count: data.in_progress_needs, color: 'bg-purple-500', ring: 'ring-purple-100', pulse: true },
          { label: 'Completed', count: data.completed_needs, color: 'bg-emerald-500', ring: 'ring-emerald-100' }
        ].map((s, i) => (
          <div key={i} className="p-5 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-all">
            <div className="flex items-center gap-3 mb-3">
              <div className={`w-3 h-3 ${s.color} rounded-full ring-4 ${s.ring} ${s.pulse ? 'animate-pulse' : ''}`}></div>
              <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">{s.label}</span>
            </div>
            <p className="text-3xl font-extrabold text-slate-900">{s.count || 0}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="p-8 bg-white rounded-3xl border border-slate-100 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900 mb-6">Category Breakdown</h2>
          <div className="space-y-4">
            {Object.entries(data.category_breakdown || {}).map(([cat, count]) => (
              <div key={cat} className="flex items-center gap-4">
                <div className={`w-3.5 h-3.5 rounded-full ${categoryColors[cat] || 'bg-slate-400'} shadow-sm`}></div>
                <span className="text-sm font-semibold text-slate-700 capitalize w-24">{cat}</span>
                <div className="flex-1 bg-slate-100 rounded-full h-3 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${categoryColors[cat] || 'bg-slate-400'} transition-all duration-1000`}
                    style={{ width: `${Math.min(100, (count / data.total_needs) * 100)}%` }}
                  ></div>
                </div>
                <span className="text-sm font-black text-slate-900 w-10 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Urgency Breakdown */}
        <div className="p-8 bg-white rounded-3xl border border-slate-100 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900 mb-6">Urgency Distribution</h2>
          <div className="space-y-5">
            {Object.entries(data.urgency_breakdown || {}).map(([urgency, count]) => (
              <div key={urgency} className="flex items-center gap-4">
                <div className={`w-3.5 h-3.5 rounded-full ${urgencyColors[urgency] || 'bg-slate-400'} shadow-sm`}></div>
                <span className="text-sm font-semibold text-slate-700 capitalize w-20">{urgency}</span>
                <div className="flex-1 bg-slate-100 rounded-full h-3 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${urgencyColors[urgency] || 'bg-slate-400'} transition-all duration-1000`}
                    style={{ width: `${Math.min(100, (count / data.total_needs) * 100)}%` }}
                  ></div>
                </div>
                <span className="text-sm font-black text-slate-900 w-10 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
