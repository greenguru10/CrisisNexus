import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Search, MapPin, Phone, Mail, Star, CheckCircle, XCircle, Plus, Trash, X } from 'lucide-react';

const Volunteers = () => {
  const [volunteers, setVolunteers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  
  const role = localStorage.getItem('role');
  const isAdmin = role === 'admin';

  // Forms
  const [newVolEmail, setNewVolEmail] = useState('');
  const [newVolMobile, setNewVolMobile] = useState('');
  const [newVolSkills, setNewVolSkills] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchVolunteers();
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

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const skillsArray = newVolSkills.split(',').map(s => s.trim()).filter(s => s);
      await api.post('/api/volunteer', { email: newVolEmail, mobile_number: newVolMobile, skills: skillsArray });
      setCreateModalOpen(false);
      setNewVolEmail('');
      setNewVolMobile('');
      setNewVolSkills('');
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
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete volunteer');
    }
  };

  const filtered = volunteers.filter(v =>
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
          <p className="text-gray-500 text-sm">{volunteers.length} registered volunteers</p>
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
          {isAdmin && (
            <button
              onClick={() => setCreateModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 transition"
            >
              <Plus size={18} /> Add Volunteer
            </button>
          )}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg">No volunteers found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map(vol => (
            <div key={vol.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 relative hover:shadow-md transition-shadow group">
              {isAdmin && (
                <button 
                  onClick={() => handleDelete(vol.id)}
                  className="absolute top-4 right-4 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
                >
                  <Trash size={16} />
                </button>
              )}
              
              <div className="flex items-start justify-between mb-4 mt-2">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold text-lg">
                    {vol.name?.[0]?.toUpperCase() || '?'}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{vol.name}</h3>
                    <div className="flex items-center gap-1 mt-0.5">
                      {vol.availability ? (
                        <span className="flex items-center gap-1 text-xs text-green-600">
                          <CheckCircle size={12} /> Available
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs text-red-500">
                          <XCircle size={12} /> Unavailable
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

              <div className="flex flex-wrap gap-1.5">
                {(vol.skills || []).map((skill, i) => (
                  <span key={i} className="px-2.5 py-1 bg-blue-50 text-blue-600 text-xs font-medium rounded-full">
                    {skill}
                  </span>
                ))}
              </div>
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
            <p className="text-sm text-gray-500 mb-6">Will auto-generate a secure password and send an email invitation.</p>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input type="email" required value={newVolEmail} onChange={e => setNewVolEmail(e.target.value)} className="w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Mobile Number</label>
                <input type="tel" placeholder="+1234567890" value={newVolMobile} onChange={e => setNewVolMobile(e.target.value)} className="w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
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
