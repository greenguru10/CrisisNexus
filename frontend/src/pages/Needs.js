import React, { useEffect, useState, useCallback } from 'react';
import api from '../services/api';
import TaskTrailPanel from '../components/TaskTrailPanel';
import CrisisMap from '../components/CrisisMap';
import {
  Search, Plus, Upload, Eye, Users, CheckCircle, XCircle,
  Zap, List, Clock, AlertTriangle, ChevronRight, Map, LayoutList,
  CheckCircle2
} from 'lucide-react';

function TabButton({ label, count, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`px-5 py-2.5 border-b-2 font-bold text-sm transition-all flex items-center gap-2 outline-none whitespace-nowrap shrink-0 ${
        active
          ? 'border-indigo-600 text-indigo-600'
          : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'
      }`}
    >
      {label}
      <span
        className={`text-[10px] font-black px-2 py-0.5 rounded-full ${
          active ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'
        }`}
      >
        {count}
      </span>
    </button>
  );
}

const ROLE = () => localStorage.getItem('role');
const NGO_ID = () => localStorage.getItem('ngo_id');

function UrgencyBadge({ level }) {
  const map = {
    HIGH: { bg: 'bg-red-50', text: 'text-red-600', dot: 'bg-red-500' },
    MEDIUM: { bg: 'bg-amber-50', text: 'text-amber-600', dot: 'bg-amber-500' },
    LOW: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500' },
  };
  const s = map[level?.toUpperCase()] || map.MEDIUM;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full ${s.bg} ${s.text} text-xs font-bold`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
      {level || 'MEDIUM'}
    </span>
  );
}

function StatusBadge({ status }) {
  const map = {
    pending: 'bg-slate-100 text-slate-600',
    assigned: 'bg-blue-50 text-blue-600',
    accepted: 'bg-emerald-50 text-emerald-700',
    in_progress: 'bg-purple-50 text-purple-600',
    completed: 'bg-emerald-50 text-emerald-700',
    rejected: 'bg-red-50 text-red-600',
  };
  const c = map[status?.toLowerCase()] || map.pending;
  return (
    <span className={`px-3 py-1 rounded-full ${c} text-[10px] font-black uppercase tracking-wider`}>
      {status?.replace(/_/g, ' ')}
    </span>
  );
}

function AssignBadge({ status }) {
  if (!status) return null;
  const map = { pending: 'bg-amber-50 text-amber-600', accepted: 'bg-emerald-50 text-emerald-600', rejected: 'bg-red-50 text-red-600' };
  const c = map[status] || 'bg-slate-100 text-slate-500';
  return (
    <span className={`px-2.5 py-1 rounded-full ${c} text-[10px] font-black uppercase tracking-wider`}>
      {status}
    </span>
  );
}

export default function Needs() {
  const role = ROLE();
  const isAdmin = role === 'admin';
  const isNgo = role === 'ngo';

  const [needs, setNeeds] = useState([]);
  const [assignedNeeds, setAssigned] = useState([]);
  const [ngoOptions, setNgoOptions] = useState([]);
  const [myVolunteers, setMyVols] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [ngoTab, setNgoTab] = useState('active'); // 'active' | 'submitted' | 'completed'
  const [adminTab, setAdminTab] = useState('all'); // 'all' | 'completed'
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'map'

  // Trail panel
  const [trailNeed, setTrailNeed] = useState(null); // { id, title }

  // Admin: assign-to-NGOs modal
  const [assignModal, setAssignModal] = useState(null); // need object
  const [selectedNgos, setSelectedNgos] = useState([]);
  const [assignNote, setAssignNote] = useState('');
  const [assigning, setAssigning] = useState(false);

  // NGO: assign-volunteers modal
  const [volModal, setVolModal] = useState(null); // need object
  const [selectedVols, setSelectedVols] = useState([]);
  const [assigningVols, setAssigningVols] = useState(false);

  const [statusUpdating, setStatusUpdating] = useState(null);

  const fetchNeeds = useCallback(async () => {
    setLoading(true);
    try {
      if (isAdmin) {
        const [needsRes, ngoRes] = await Promise.all([
          api.get('/api/needs'),
          api.get('/api/ngo/names'),
        ]);
        setNeeds(needsRes.data);
        setNgoOptions(ngoRes.data);
      } else if (isNgo) {
        const [allRes, assignedRes, volRes] = await Promise.all([
          api.get('/api/needs'),
          api.get('/api/ngo/needs/assigned').catch(() => ({ data: [] })),
          api.get('/api/volunteers').catch(() => ({ data: [] })),
        ]);
        setNeeds(allRes.data.filter(n => !n.assigned_by_admin || n.ngo_id === parseInt(NGO_ID())));
        setAssigned(assignedRes.data);
        setMyVols(volRes.data);
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  }, [isAdmin, isNgo]);

  useEffect(() => { fetchNeeds(); }, [fetchNeeds]);

  const handleAssignNgos = async () => {
    if (!selectedNgos.length || !assignModal) return;
    setAssigning(true);
    try {
      await api.post(`/api/admin/needs/${assignModal.id}/assign-to-ngos`, {
        ngo_ids: selectedNgos.map(Number),
        note: assignNote || null,
      });
      setAssignModal(null); setSelectedNgos([]); setAssignNote('');
      fetchNeeds();
    } catch (err) {
      alert(err.response?.data?.detail || 'Assignment failed');
    }
    setAssigning(false);
  };

  const handleNgoAction = async (needId, action) => {
    setStatusUpdating(needId);
    try {
      await api.post(`/api/ngo/needs/${needId}/${action}-assignment`);
      fetchNeeds();
    } catch (err) {
      alert(err.response?.data?.detail || 'Action failed');
    }
    setStatusUpdating(null);
  };

  const handleAutoAssign = async (needId) => {
    setStatusUpdating(needId);
    try {
      await api.post(`/api/match/${needId}`);
      fetchNeeds();
    } catch (err) {
      alert(err.response?.data?.detail || 'Auto-assign failed');
    }
    setStatusUpdating(null);
  };

  const handleVolAssign = async () => {
    if (!selectedVols.length || !volModal) return;
    setAssigningVols(true);
    try {
      await api.post(`/api/ngo/needs/${volModal.id}/assign-volunteers`, {
        volunteer_ids: selectedVols.map(Number),
      });
      setVolModal(null); setSelectedVols([]);
      fetchNeeds();
    } catch (err) {
      alert(err.response?.data?.detail || 'Volunteer assignment failed');
    }
    setAssigningVols(false);
  };

  const handleStatusChange = async (needId, status) => {
    setStatusUpdating(needId);
    try {
      await api.put(`/api/needs/${needId}/status`, { status });
      fetchNeeds();
    } catch { }
    setStatusUpdating(null);
  };

  const filterFn = n =>
    (n.category || '').toLowerCase().includes(filter.toLowerCase()) ||
    (n.location || '').toLowerCase().includes(filter.toLowerCase()) ||
    (n.description || '').toLowerCase().includes(filter.toLowerCase());

  let displayNeeds = [];
  if (isAdmin) {
    if (adminTab === 'completed') {
      displayNeeds = needs.filter(n => n.status === 'completed');
    } else {
      displayNeeds = needs.filter(n => n.status !== 'completed');
    }
  } else if (isNgo) {
    if (ngoTab === 'completed') {
      displayNeeds = [...assignedNeeds, ...needs].filter(n => n.status === 'completed');
      const seen = new Set();
      displayNeeds = displayNeeds.filter(n => {
        if (seen.has(n.id)) return false;
        seen.add(n.id);
        return true;
      });
    } else if (ngoTab === 'submitted') {
      displayNeeds = needs.filter(n => n.status !== 'completed');
    } else {
      displayNeeds = assignedNeeds.filter(n => n.status !== 'completed');
    }
  }
  displayNeeds = displayNeeds.filter(filterFn);

  return (
    <div className="font-sans text-slate-900 animate-fade-in-up min-h-screen pb-12">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {isAdmin ? '📋 All Needs' : '📋 My NGO Tasks'}
          </h1>
          <p className="text-slate-500 font-medium mt-1">
            {isAdmin ? `${needs.length} needs · Click a row to view Task Trail`
              : `${assignedNeeds.length} assigned · Click row for Task Trail`}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex bg-slate-100 p-1 rounded-xl">
            <button
              onClick={() => setViewMode('list')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                viewMode === 'list' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <LayoutList size={16} /> List
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                viewMode === 'map' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Map size={16} /> Map
            </button>
          </div>
          <div className="relative w-full sm:w-auto">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              value={filter}
              onChange={e => setFilter(e.target.value)}
              placeholder="Search needs…"
              className="pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-medium outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 transition-all w-full sm:w-64"
            />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex overflow-x-auto gap-2 mb-6 border-b border-slate-200 hide-scrollbar">
        {isAdmin ? (
          <>
            <TabButton active={adminTab === 'all'} onClick={() => setAdminTab('all')} label="📋 Active Needs" count={needs.filter(n => n.status !== 'completed').length} />
            <TabButton active={adminTab === 'completed'} onClick={() => setAdminTab('completed')} label="✅ Completed Tasks" count={needs.filter(n => n.status === 'completed').length} />
          </>
        ) : (
          <>
            <TabButton active={ngoTab === 'active'} onClick={() => setNgoTab('active')} label="📤 Assigned to Me" count={assignedNeeds.filter(n => n.status !== 'completed').length} />
            <TabButton active={ngoTab === 'submitted'} onClick={() => setNgoTab('submitted')} label="📝 My Submitted" count={needs.filter(n => n.status !== 'completed').length} />
            <TabButton active={ngoTab === 'completed'} onClick={() => setNgoTab('completed')} label="✅ Completed" count={[...assignedNeeds, ...needs].filter(n => n.status === 'completed').length} />
          </>
        )}
      </div>

      {loading && (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-200 border-t-indigo-600"></div>
        </div>
      )}

      {!loading && displayNeeds.length === 0 && (
        <div className="bg-white border border-slate-200 rounded-3xl p-16 text-center shadow-sm">
          <span className="text-4xl block mb-4">📭</span>
          <h3 className="text-xl font-bold text-slate-900 mb-2">No needs found</h3>
          <p className="text-slate-500">There are no tasks matching your current filters.</p>
        </div>
      )}

      {/* Needs content: Map or List */}
      {!loading && displayNeeds.length > 0 && viewMode === 'map' && (
        <div className="mt-4 rounded-3xl overflow-hidden border border-slate-200 shadow-sm">
          <CrisisMap needs={displayNeeds} loading={loading} />
        </div>
      )}

      {!loading && displayNeeds.length > 0 && viewMode === 'list' && (
        <div className="bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  {['#', 'Category', 'Location', 'Urgency', 'Status',
                    isNgo && (ngoTab === 'active' || ngoTab === 'completed') ? 'Assignment' : null,
                    'Actions'].filter(Boolean).map(h => (
                      <th key={h} className="py-4 px-6 text-xs font-extrabold text-slate-500 uppercase tracking-wider">{h}</th>
                    ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {displayNeeds.map(need => (
                  <tr
                    key={need.id}
                    onClick={() => setTrailNeed({ id: need.id, title: need.category })}
                    className="hover:bg-slate-50 transition-colors cursor-pointer group"
                  >
                    <td className="py-4 px-6 text-sm font-bold text-slate-400 group-hover:text-indigo-500 transition-colors">#{need.id}</td>
                    <td className="py-4 px-6">
                      <div className="font-bold text-slate-900 text-sm mb-1">{need.category}</div>
                      <div className="text-xs text-slate-500 max-w-[200px] truncate">{need.description}</div>
                    </td>
                    <td className="py-4 px-6 text-sm font-medium text-slate-600">{need.location || '—'}</td>
                    <td className="py-4 px-6"><UrgencyBadge level={need.urgency} /></td>
                    <td className="py-4 px-6"><StatusBadge status={need.status} /></td>
                    {isNgo && (ngoTab === 'active' || ngoTab === 'completed') && (
                      <td className="py-4 px-6"><AssignBadge status={need.ngo_assignment_status} /></td>
                    )}

                    {/* Actions cell */}
                    <td className="py-4 px-6" onClick={e => e.stopPropagation()}>
                      <div className="flex flex-wrap items-center gap-2">
                        {/* Admin: assign to NGOs */}
                        {isAdmin && need.status !== 'completed' && (
                          <>
                            <button
                              onClick={() => { setAssignModal(need); setSelectedNgos(need.assigned_ngo_ids || []); setAssignNote(''); }}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-600 text-xs font-bold transition-colors"
                            >
                              <Users size={14} /> Assign NGO(s)
                            </button>
                            <select
                              defaultValue=""
                              onChange={e => e.target.value && handleStatusChange(need.id, e.target.value)}
                              className="px-2 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-bold text-slate-600 outline-none hover:border-slate-300 transition-colors cursor-pointer"
                            >
                              <option value="">Status…</option>
                              {['pending', 'assigned', 'in_progress', 'completed'].map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
                            </select>
                          </>
                        )}
                        {isAdmin && need.status === 'completed' && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-600 text-xs font-bold">
                            <CheckCircle2 size={14} /> Completed
                          </span>
                        )}

                        {/* NGO active tab */}
                        {isNgo && ngoTab === 'active' && (
                          <>
                            {need.ngo_assignment_status === 'pending' && (
                              <>
                                <button disabled={statusUpdating === need.id} onClick={() => handleNgoAction(need.id, 'accept')} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-600 text-xs font-bold transition-colors disabled:opacity-50">
                                  <CheckCircle size={14} /> Accept
                                </button>
                                <button disabled={statusUpdating === need.id} onClick={() => handleNgoAction(need.id, 'reject')} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-50 hover:bg-red-100 text-red-600 text-xs font-bold transition-colors disabled:opacity-50">
                                  <XCircle size={14} /> Reject
                                </button>
                              </>
                            )}
                            {need.ngo_assignment_status === 'accepted' && need.status !== 'completed' && (
                              <>
                                {!need.has_manual_assignments && (
                                  <button disabled={statusUpdating === need.id} onClick={() => handleAutoAssign(need.id)} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-600 text-xs font-bold transition-colors disabled:opacity-50">
                                    <Zap size={14} /> Auto Assign
                                  </button>
                                )}
                                <button onClick={() => { setVolModal(need); setSelectedVols([]); }} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-600 text-xs font-bold transition-colors">
                                  <List size={14} /> {need.has_manual_assignments ? 'Edit Team' : 'Manual Assign'}
                                </button>
                              </>
                            )}
                          </>
                        )}

                        {isNgo && ngoTab === 'completed' && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-600 text-xs font-bold">
                            <CheckCircle2 size={14} /> Completed
                          </span>
                        )}

                        {/* Trail icon always */}
                        <button
                          onClick={() => setTrailNeed({ id: need.id, title: need.category })}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 text-xs font-bold transition-colors"
                        >
                          <Eye size={14} /> {need.status === 'completed' ? 'Details' : 'Trail'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── ADMIN: Assign to NGOs modal ───────────────────────────── */}
      {assignModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in" onClick={() => setAssignModal(null)}>
          <div className="bg-white rounded-[2rem] p-8 w-full max-w-[500px] shadow-2xl animate-fade-in-up" onClick={e => e.stopPropagation()}>
            <h3 className="text-2xl font-extrabold text-slate-900 mb-2">Assign Need to NGO(s)</h3>
            <p className="text-sm font-medium text-slate-500 mb-6 flex flex-wrap items-center gap-2">
              Need #{assignModal.id} • {assignModal.category} • <UrgencyBadge level={assignModal.urgency} />
            </p>

            <p className="text-sm font-bold text-slate-700 mb-3">Select NGO(s) to assign:</p>
            <div className="max-h-60 overflow-y-auto border border-slate-200 rounded-2xl mb-5 divide-y divide-slate-100">
              {ngoOptions.map(n => (
                <label key={n.id} className="flex items-center gap-3 p-4 hover:bg-slate-50 cursor-pointer transition-colors group">
                  <input
                    type="checkbox"
                    checked={selectedNgos.includes(n.id)}
                    onChange={e => setSelectedNgos(prev => e.target.checked ? [...prev, n.id] : prev.filter(id => id !== n.id))}
                    className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500 border-slate-300"
                  />
                  <span className="text-sm font-bold text-slate-700 group-hover:text-slate-900">{n.name}</span>
                </label>
              ))}
              {ngoOptions.length === 0 && <p className="p-4 text-slate-500 text-sm text-center font-medium">No approved NGOs found.</p>}
            </div>

            <label className="block text-sm font-bold text-slate-700 mb-2">Admin Note (optional)</label>
            <input
              value={assignNote}
              onChange={e => setAssignNote(e.target.value)}
              placeholder="Instructions for NGO…"
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-indigo-500/30 focus:bg-white transition-all mb-8"
            />

            <div className="flex justify-end gap-3">
              <button onClick={() => setAssignModal(null)} className="px-5 py-2.5 bg-white border border-slate-200 text-slate-600 rounded-xl font-bold hover:bg-slate-50 transition-colors">Cancel</button>
              <button
                onClick={handleAssignNgos}
                disabled={assigning || !selectedNgos.length}
                className="px-6 py-2.5 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-600/20"
              >
                {assigning ? 'Assigning…' : `Assign to ${selectedNgos.length} NGO(s)`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── NGO: Volunteer assign modal ───────────────────────────── */}
      {volModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in" onClick={() => setVolModal(null)}>
          <div className="bg-white rounded-[2rem] p-8 w-full max-w-[500px] shadow-2xl animate-fade-in-up" onClick={e => e.stopPropagation()}>
            <h3 className="text-2xl font-extrabold text-slate-900 mb-2">Assign Volunteers</h3>
            <p className="text-sm font-medium text-slate-500 mb-6">
              Need #{volModal.id} • {volModal.category} — Select one or more volunteers for a team assignment.
            </p>

            <div className="max-h-60 overflow-y-auto border border-slate-200 rounded-2xl mb-8 divide-y divide-slate-100">
              {myVolunteers.filter(v => v.availability).map(v => (
                <label key={v.id} className="flex items-start gap-4 p-4 hover:bg-slate-50 cursor-pointer transition-colors group">
                  <input
                    type="checkbox"
                    checked={selectedVols.includes(v.id)}
                    onChange={e => setSelectedVols(prev => e.target.checked ? [...prev, v.id] : prev.filter(id => id !== v.id))}
                    className="w-4 h-4 text-amber-500 rounded focus:ring-amber-500 border-slate-300 mt-1"
                  />
                  <div>
                    <div className="text-sm font-bold text-slate-900">{v.name}</div>
                    <div className="text-xs text-slate-500 font-medium mt-1">{(v.skills || []).join(', ')}</div>
                  </div>
                </label>
              ))}
              {myVolunteers.filter(v => v.availability).length === 0 && (
                <p className="p-6 text-slate-500 text-sm text-center font-medium">No available volunteers in your NGO.</p>
              )}
            </div>

            <div className="flex justify-end gap-3">
              <button onClick={() => setVolModal(null)} className="px-5 py-2.5 bg-white border border-slate-200 text-slate-600 rounded-xl font-bold hover:bg-slate-50 transition-colors">Cancel</button>
              <button
                onClick={handleVolAssign}
                disabled={assigningVols || !selectedVols.length}
                className="px-6 py-2.5 bg-amber-500 text-white rounded-xl font-bold hover:bg-amber-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-amber-500/20"
              >
                {assigningVols ? 'Assigning…' : `Assign ${selectedVols.length} Volunteer(s)`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Task Trail Panel ──────────────────────────────────────── */}
      {trailNeed && (
        <TaskTrailPanel needId={trailNeed.id} needTitle={trailNeed.title} onClose={() => setTrailNeed(null)} />
      )}
    </div>
  );
}
