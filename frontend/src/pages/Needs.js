import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Search, Filter, CheckCircle2, X, AlertTriangle, UserMinus, RefreshCw } from 'lucide-react';

const urgencyBadge = (urgency) => {
  const styles = {
    high: 'bg-red-100 text-red-700',
    medium: 'bg-amber-100 text-amber-700',
    low: 'bg-green-100 text-green-700',
  };
  return styles[urgency] || 'bg-gray-100 text-gray-700';
};

const statusBadge = (status) => {
  const styles = {
    pending: 'bg-amber-50 text-amber-600 border-amber-200',
    assigned: 'bg-blue-50 text-blue-600 border-blue-200',
    completed: 'bg-green-50 text-green-600 border-green-200',
  };
  return styles[status] || 'bg-gray-50 text-gray-600 border-gray-200';
};

const Needs = () => {
  const [needs, setNeeds] = useState([]);
  const [volunteers, setVolunteers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [matchResult, setMatchResult] = useState(null);
  const [matching, setMatching] = useState(null);
  const [filter, setFilter] = useState('');
  const [manualMatchModalOpen, setManualMatchModalOpen] = useState(null);
  const [selectedVolunteer, setSelectedVolunteer] = useState('');
  
  const role = localStorage.getItem('role') || 'volunteer';
  const canMatch = role === 'admin' || role === 'ngo';

  useEffect(() => {
    fetchNeeds();
    if (canMatch) fetchVolunteers();
  }, [canMatch]);

  const fetchVolunteers = async () => {
    try {
      const { data } = await api.get('/api/volunteers?available=true');
      setVolunteers(data);
    } catch (err) { }
  };

  const fetchNeeds = async () => {
    try {
      const { data } = await api.get('/api/needs');
      setNeeds(data);
    } catch (err) {
      console.error('Failed to fetch needs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMatch = async (id) => {
    setMatching(id);
    try {
      const { data } = await api.post(`/api/match/${id}`);
      setMatchResult(data);
      fetchNeeds(); // Refresh list
    } catch (err) {
      const detail = err.response?.data?.detail || 'Matching failed';
      alert(detail);
    } finally {
      setMatching(null);
    }
  };

  const handleUnassign = async (needId) => {
    if (!window.confirm('Unassign the volunteer from this need? The need will go back to Pending.')) return;
    try {
      await api.post(`/api/match/${needId}/unassign`);
      fetchNeeds();
      if (canMatch) fetchVolunteers();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to unassign');
    }
  };

  const handleManualMatch = async (e) => {
    e.preventDefault();
    setMatching(manualMatchModalOpen);
    try {
      await api.post(`/api/match/${manualMatchModalOpen}/manual`, { volunteer_id: parseInt(selectedVolunteer) });
      setManualMatchModalOpen(null);
      setSelectedVolunteer('');
      fetchNeeds(); // Refresh list
      if (canMatch) fetchVolunteers();
      alert("Manual match successful!");
    } catch(err) {
       alert(err.response?.data?.detail || 'Matching failed');
    } finally {
       setMatching(null);
    }
  };

  const filtered = needs.filter(n =>
    (n.category || '').toLowerCase().includes(filter.toLowerCase()) ||
    (n.location || '').toLowerCase().includes(filter.toLowerCase()) ||
    (n.urgency || '').toLowerCase().includes(filter.toLowerCase())
  );

  if (loading) {
    return (
      <div className="space-y-4 animate-fade-in">
        {[1, 2, 3, 4].map(i => <div key={i} className="h-16 rounded-xl animate-shimmer"></div>)}
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Community Needs</h1>
          <p className="text-gray-500 text-sm">{needs.length} total needs tracked</p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input
              className="pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none bg-white w-64 transition-all"
              placeholder="Search by category, location..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">ID</th>
              <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Category</th>
              <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Location</th>
              <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Urgency</th>
              <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">People</th>
              <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Priority</th>
              <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Status / Assigned To</th>
              <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-12 text-center text-gray-400">
                  No needs found. Upload a report to get started.
                </td>
              </tr>
            ) : (
              filtered.map(need => (
                <tr key={need.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4 text-sm text-gray-400 font-mono">#{need.id}</td>
                  <td className="px-6 py-4 font-medium text-gray-900 capitalize">{need.category || 'N/A'}</td>
                  <td className="px-6 py-4 text-gray-600 text-sm">{need.location || 'Unknown'}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase ${urgencyBadge(need.urgency)}`}>
                      {need.urgency}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-700 font-medium">{need.people_affected || 0}</td>
                  <td className="px-6 py-4">
                    <span className="text-sm font-bold text-gray-800">{need.priority_score?.toFixed(1)}</span>
                    <span className="text-xs text-gray-400">/100</span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border w-fit ${statusBadge(need.status)}`}>
                        {need.status}
                      </span>
                      {need.assigned_volunteer_name && (
                        <span className="text-xs text-blue-600 font-medium">→ {need.assigned_volunteer_name}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    {need.status === 'pending' ? (
                      canMatch ? (
                        <div className="flex justify-end gap-2">
                           <button
                             onClick={() => handleMatch(need.id)}
                             disabled={matching === need.id}
                             title="Auto-Match using AI Scoring"
                             className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-all shadow-sm shadow-blue-600/20"
                           >
                             {matching === need.id ? 'Loading...' : 'Auto Match'}
                           </button>
                           <button
                             onClick={() => setManualMatchModalOpen(need.id)}
                             disabled={matching === need.id}
                             title="Pick Volunteer Manually"
                             className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 disabled:opacity-50 transition-all shadow-sm border border-gray-200"
                           >
                             Manual
                           </button>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-500 font-medium">Pending Match</span>
                      )
                    ) : need.status === 'assigned' && canMatch ? (
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => handleUnassign(need.id)}
                          title="Remove volunteer from this need"
                          className="px-3 py-2 bg-red-50 text-red-600 rounded-lg text-sm font-medium hover:bg-red-100 transition-all border border-red-100"
                        >
                          <UserMinus size={14} className="inline mr-1" /> Unassign
                        </button>
                        <button
                          onClick={() => {
                            handleUnassign(need.id);
                            setTimeout(() => setManualMatchModalOpen(need.id), 500);
                          }}
                          title="Replace with a different volunteer"
                          className="px-3 py-2 bg-amber-50 text-amber-700 rounded-lg text-sm font-medium hover:bg-amber-100 transition-all border border-amber-100"
                        >
                          <RefreshCw size={14} className="inline mr-1" /> Reassign
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-gray-400 capitalize">{need.status}</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Match Result Modal */}
      {matchResult && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-white rounded-2xl p-8 max-w-lg w-full shadow-2xl animate-slide-up">
            <div className="flex justify-between items-start mb-6">
              <div className="w-14 h-14 bg-green-100 text-green-600 rounded-full flex items-center justify-center">
                <CheckCircle2 size={28} />
              </div>
              <button onClick={() => setMatchResult(null)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Volunteer Matched!</h3>
            <p className="text-gray-500 mb-6">{matchResult.message}</p>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="p-4 bg-gray-50 rounded-xl text-center">
                <p className="text-xs text-gray-400 uppercase font-bold mb-1">Volunteer</p>
                <p className="text-lg font-bold text-gray-900">{matchResult.volunteer_name}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl text-center">
                <p className="text-xs text-gray-400 uppercase font-bold mb-1">Match Score</p>
                <p className="text-lg font-bold text-blue-600">{(matchResult.match_score * 100).toFixed(1)}%</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl text-center">
                <p className="text-xs text-gray-400 uppercase font-bold mb-1">Distance</p>
                <p className="text-lg font-bold text-gray-900">{matchResult.distance_km?.toFixed(1)} km</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-xl text-center">
                <p className="text-xs text-gray-400 uppercase font-bold mb-1">Skill Match</p>
                <p className="text-lg font-bold text-green-600">{(matchResult.skill_match * 100).toFixed(1)}%</p>
              </div>
            </div>
            <button
              onClick={() => setMatchResult(null)}
              className="w-full py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      )}

      {/* Manual Match Modal */}
      {manualMatchModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-gray-900">Manual Assign</h3>
              <button 
                onClick={() => {
                  setManualMatchModalOpen(null); 
                  setSelectedVolunteer('');
                }} 
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
            <p className="text-sm text-gray-500 mb-6">Select from currently available volunteers.</p>
            <form onSubmit={handleManualMatch} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Pick Volunteer</label>
                <select 
                  required 
                  value={selectedVolunteer} 
                  onChange={e => setSelectedVolunteer(e.target.value)} 
                  className="w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="" disabled>Select...</option>
                  {volunteers.map(v => (
                    <option key={v.id} value={v.id}>{v.name} ({v.skills?.join(', ') || 'no skills'})</option>
                  ))}
                </select>
              </div>
              <button type="submit" disabled={matching || !selectedVolunteer} className="w-full py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 mt-2">
                {matching ? 'Assigning...' : 'Assign User'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Needs;
