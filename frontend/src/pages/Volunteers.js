import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Search, MapPin, Phone, Mail, Star, CheckCircle, XCircle, Plus, Trash, X, Clock, ShieldCheck, ShieldX, Users } from 'lucide-react';

const Volunteers = () => {
  const [volunteers, setVolunteers] = useState([]);
  const [pendingVolunteers, setPendingVolunteers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('approved'); // 'approved' | 'pending'

  const role = localStorage.getItem('role');
  const isAdmin = role === 'admin';
  const isNgo = role === 'ngo';

  // Forms
  const [newVolEmail, setNewVolEmail] = useState('');
  const [newVolMobile, setNewVolMobile] = useState('');
  const [newVolSkills, setNewVolSkills] = useState('');
  const [newVolNgoId, setNewVolNgoId] = useState('');
  const [ngoOptions, setNgoOptions] = useState([]);
  const [saving, setSaving] = useState(false);

  // Action loading states
  const [approvingId, setApprovingId] = useState(null);
  const [rejectingId, setRejectingId] = useState(null);

  useEffect(() => {
    fetchVolunteers();
    if (isAdmin || isNgo) {
      fetchPending();
    }
    if (isAdmin) {
      // Fetch NGO list for volunteer creation (admin only — NGO auto-assigned)
      api.get('/api/ngo/names').then(r => setNgoOptions(r.data)).catch(() => {});
    }
  }, []);

  const fetchVolunteers = async () => {
    try {
      const { data } = await api.get('/api/volunteers');
      setVolunteers(data);
    } catch (err) {
      console.error('Failed to fetch volunteers:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPending = async () => {
    try {
      const { data } = await api.get('/api/volunteers/pending');
      setPendingVolunteers(data);
    } catch (err) {
      console.error('Failed to fetch pending volunteers:', err);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const skillsArray = newVolSkills.split(',').map(s => s.trim()).filter(s => s);
      await api.post('/api/volunteer', {
        email: newVolEmail,
        mobile_number: newVolMobile,
        skills: skillsArray,
        ngo_id: newVolNgoId ? parseInt(newVolNgoId) : undefined,
      });
      setCreateModalOpen(false);
      setNewVolEmail('');
      setNewVolMobile('');
      setNewVolSkills('');
      setNewVolNgoId('');
      fetchVolunteers();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create volunteer');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this volunteer? This action cannot be undone.')) return;
    try {
      await api.delete(`/api/volunteer/${id}`);
      fetchVolunteers();
      fetchPending();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete volunteer');
    }
  };

  const handleApprove = async (id) => {
    setApprovingId(id);
    try {
      await api.post(`/api/volunteer/${id}/approve`);
      // Move from pending to approved
      fetchVolunteers();
      fetchPending();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to approve volunteer');
    } finally {
      setApprovingId(null);
    }
  };

  const handleReject = async (id) => {
    if (!window.confirm('Are you sure you want to reject this volunteer?')) return;
    setRejectingId(id);
    try {
      await api.post(`/api/volunteer/${id}/reject`);
      fetchPending();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to reject volunteer');
    } finally {
      setRejectingId(null);
    }
  };

  const displayList = activeTab === 'approved' ? volunteers : pendingVolunteers;
  const filtered = displayList.filter(v =>
    (v.name || '').toLowerCase().includes(filter.toLowerCase()) ||
    (v.location || '').toLowerCase().includes(filter.toLowerCase()) ||
    (v.skills || []).some(s => s.toLowerCase().includes(filter.toLowerCase()))
  );

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in">
        {[1, 2, 3, 4, 5, 6].map(i => (
          <div key={i} className="h-48 rounded-xl animate-shimmer"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Volunteers</h1>
          <p className="text-gray-500 text-sm">{volunteers.length} approved volunteers</p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input
              className="pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none bg-white w-64 transition-all"
              placeholder="Search by name, skill..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>
          {(isAdmin || isNgo) && (
            <button
              onClick={() => setCreateModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 transition"
            >
              <Plus size={18} /> Add Volunteer
            </button>
          )}
        </div>
      </div>

      {/* TABS — Approved / Pending (Admin + NGO) */}
      {(isAdmin || isNgo) && (
        <div className="flex gap-2 border-b border-gray-200 pb-0">
          <button
            onClick={() => setActiveTab('approved')}
            className={`flex items-center gap-2 px-4 py-2.5 font-medium text-sm rounded-t-lg transition-all border-b-2 ${
              activeTab === 'approved'
                ? 'border-blue-600 text-blue-600 bg-blue-50/50'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Users size={16} />
            Approved
            <span className="ml-1 bg-blue-100 text-blue-700 text-xs font-bold px-2 py-0.5 rounded-full">
              {volunteers.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('pending')}
            className={`flex items-center gap-2 px-4 py-2.5 font-medium text-sm rounded-t-lg transition-all border-b-2 ${
              activeTab === 'pending'
                ? 'border-amber-500 text-amber-600 bg-amber-50/50'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Clock size={16} />
            Pending Approval
            {pendingVolunteers.length > 0 && (
              <span className="ml-1 bg-amber-100 text-amber-700 text-xs font-bold px-2 py-0.5 rounded-full animate-pulse">
                {pendingVolunteers.length}
              </span>
            )}
          </button>
        </div>
      )}

      {filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg">
            {activeTab === 'pending' ? 'No pending volunteers' : 'No volunteers found'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map(vol => (
            <div key={vol.id} className={`bg-white rounded-xl border shadow-sm p-6 relative hover:shadow-md transition-shadow group ${
              activeTab === 'pending' ? 'border-amber-200' : 'border-gray-100'
            }`}>
              {/* Delete button (admin, approved tab only) */}
              {isAdmin && activeTab === 'approved' && (
                <button 
                  onClick={() => handleDelete(vol.id)}
                  className="absolute top-4 right-4 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
                >
                  <Trash size={16} />
                </button>
              )}

              {/* Pending badge */}
              {activeTab === 'pending' && (
                <div className="absolute top-4 right-4">
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-amber-100 text-amber-700 text-xs font-medium rounded-full">
                    <Clock size={12} /> Pending
                  </span>
                </div>
              )}
              
              <div className="flex items-start justify-between mb-4 mt-2">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${
                    activeTab === 'pending' ? 'bg-amber-100 text-amber-600' : 'bg-blue-100 text-blue-600'
                  }`}>
                    {vol.name?.[0]?.toUpperCase() || '?'}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{vol.name}</h3>
                    <div className="flex items-center gap-1 mt-0.5">
                      {activeTab === 'approved' ? (
                        vol.availability ? (
                          <span className="flex items-center gap-1 text-xs text-green-600">
                            <CheckCircle size={12} /> Available
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-xs text-red-500">
                            <XCircle size={12} /> Unavailable
                          </span>
                        )
                      ) : (
                        <span className="flex items-center gap-1 text-xs text-amber-500">
                          <Clock size={12} /> Awaiting review
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-2 mb-4">
                {vol.email && (
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Mail size={14} className="text-gray-400" />
                    <span>{vol.email}</span>
                  </div>
                )}
                {vol.mobile_number && (
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Phone size={14} className="text-gray-400" />
                    <span>{vol.mobile_number}</span>
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-1.5 mb-4">
                {(vol.skills || []).map((skill, i) => (
                  <span key={i} className="px-2.5 py-1 bg-blue-50 text-blue-600 text-xs font-medium rounded-full">
                    {skill}
                  </span>
                ))}
                {(!vol.skills || vol.skills.length === 0) && (
                  <span className="text-xs text-gray-400 italic">No skills listed</span>
                )}
              </div>

              {/* Approve / Reject buttons (pending tab) */}
              {isAdmin && activeTab === 'pending' && (
                <div className="flex gap-2 pt-3 border-t border-gray-100">
                  <button
                    onClick={() => handleApprove(vol.id)}
                    disabled={approvingId === vol.id}
                    className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition disabled:opacity-50"
                  >
                    <ShieldCheck size={15} />
                    {approvingId === vol.id ? 'Approving...' : 'Approve'}
                  </button>
                  <button
                    onClick={() => handleReject(vol.id)}
                    disabled={rejectingId === vol.id}
                    className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-white text-red-600 text-sm font-medium rounded-lg border border-red-200 hover:bg-red-50 transition disabled:opacity-50"
                  >
                    <ShieldX size={15} />
                    {rejectingId === vol.id ? 'Rejecting...' : 'Reject'}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* CREATE MODAL */}
      {createModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-gray-900">Add New Volunteer</h3>
              <button onClick={() => setCreateModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <p className="text-sm text-gray-500 mb-2">Will auto-generate a secure password and send an email invitation.</p>
            <div className="bg-green-50 border border-green-100 rounded-lg p-2 mb-4">
              <p className="text-green-700 text-xs flex items-center gap-1"><ShieldCheck size={13} /> Auto-approved — no review needed</p>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input type="email" required value={newVolEmail} onChange={e => setNewVolEmail(e.target.value)} className="w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mobile Number</label>
                <input type="tel" placeholder="+1234567890" value={newVolMobile} onChange={e => setNewVolMobile(e.target.value)} className="w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              {isAdmin && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Assign to NGO *</label>
                  <select required value={newVolNgoId} onChange={e => setNewVolNgoId(e.target.value)} className="w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="">Select an NGO…</option>
                    {ngoOptions.map(n => (
                      <option key={n.id} value={n.id}>{n.name}</option>
                    ))}
                  </select>
                  {ngoOptions.length === 0 && <p className="text-xs text-amber-600 mt-1">No approved NGOs yet.</p>}
                </div>
              )}
              {isNgo && (
                <div className="px-3 py-2 bg-blue-50 border border-blue-100 rounded-lg text-sm text-blue-700">
                  Volunteer will be auto-assigned to your NGO.
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Skills (comma separated)</label>
                <input type="text" required placeholder="medical, driving" value={newVolSkills} onChange={e => setNewVolSkills(e.target.value)} className="w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <button type="submit" disabled={saving} className="w-full py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 mt-2">
                {saving ? 'Creating...' : 'Create & Invite'}
              </button>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default Volunteers;
