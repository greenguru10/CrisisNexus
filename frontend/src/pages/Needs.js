/**
 * Needs.js – Role-aware view for Admin and NGO Coordinator.
 *
 * Admin:  See all needs. Click row → Trail panel. "Assign to NGO(s)" button.
 * NGO:    Tabs — "Assigned to Me" (from Admin) | "My Submitted Needs".
 *         Accept/Reject assignments. Assign volunteers (auto or manual multi-select).
 *         Click row → Trail panel.
 */
import React, { useEffect, useState, useCallback } from 'react';
import api from '../services/api';
import TaskTrailPanel from '../components/TaskTrailPanel';
import {
  Search, Plus, Upload, Eye, Users, CheckCircle, XCircle,
  Zap, List, Clock, AlertTriangle, ChevronRight
} from 'lucide-react';

const ROLE = () => localStorage.getItem('role');
const NGO_ID = () => localStorage.getItem('ngo_id');

// ── Urgency badge ─────────────────────────────────────────────────────────────
function UrgencyBadge({ level }) {
  const map = { HIGH: { bg: '#fef2f2', text: '#dc2626', dot: '#ef4444' }, MEDIUM: { bg: '#fffbeb', text: '#d97706', dot: '#f59e0b' }, LOW: { bg: '#f0fdf4', text: '#15803d', dot: '#22c55e' } };
  const s = map[level?.toUpperCase()] || map.MEDIUM;
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', padding: '0.2rem 0.6rem', borderRadius: '999px', background: s.bg, color: s.text, fontSize: '0.72rem', fontWeight: 700 }}>
      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: s.dot }} />
      {level || 'MEDIUM'}
    </span>
  );
}

// ── Status badge ─────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const map = {
    pending:     { bg: '#f8fafc', text: '#64748b' },
    assigned:    { bg: '#eff6ff', text: '#2563eb' },
    accepted:    { bg: '#f0fdf4', text: '#15803d' },
    in_progress: { bg: '#fffbeb', text: '#d97706' },
    completed:   { bg: '#f0fdf4', text: '#15803d' },
    rejected:    { bg: '#fef2f2', text: '#dc2626' },
  };
  const s = map[status?.toLowerCase()] || map.pending;
  return (
    <span style={{ padding: '0.2rem 0.65rem', borderRadius: '999px', background: s.bg, color: s.text, fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
      {status?.replace(/_/g, ' ')}
    </span>
  );
}

// ── NgoAssignment badge ───────────────────────────────────────────────────────
function AssignBadge({ status }) {
  if (!status) return null;
  const map = { pending: '#f59e0b', accepted: '#10b981', rejected: '#ef4444' };
  return (
    <span style={{ padding: '0.15rem 0.55rem', borderRadius: '999px', background: (map[status] || '#64748b') + '18', color: map[status] || '#64748b', fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase' }}>
      {status}
    </span>
  );
}

export default function Needs() {
  const role = ROLE();
  const isAdmin = role === 'admin';
  const isNgo = role === 'ngo';

  const [needs, setNeeds]               = useState([]);
  const [assignedNeeds, setAssigned]    = useState([]);
  const [ngoOptions, setNgoOptions]     = useState([]);
  const [myVolunteers, setMyVols]       = useState([]);
  const [loading, setLoading]           = useState(true);
  const [filter, setFilter]             = useState('');
  const [ngoTab, setNgoTab]             = useState('assigned'); // 'assigned' | 'submitted'

  // Trail panel
  const [trailNeed, setTrailNeed]       = useState(null); // { id, title }

  // Admin: assign-to-NGOs modal
  const [assignModal, setAssignModal]   = useState(null); // need object
  const [selectedNgos, setSelectedNgos] = useState([]);
  const [assignNote, setAssignNote]     = useState('');
  const [assigning, setAssigning]       = useState(false);

  // NGO: assign-volunteers modal
  const [volModal, setVolModal]         = useState(null); // need object
  const [selectedVols, setSelectedVols] = useState([]);
  const [assigningVols, setAssigningVols] = useState(false);

  const [statusUpdating, setStatusUpdating] = useState(null);

  // ── Data fetching ───────────────────────────────────────────────
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

  // ── Admin: assign to NGOs ───────────────────────────────────────
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

  // ── NGO: accept / reject ────────────────────────────────────────
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

  // ── NGO: auto-assign volunteer ──────────────────────────────────
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

  // ── NGO: manual multi-volunteer assign ──────────────────────────
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

  // ── Status update (admin) ────────────────────────────────────────
  const handleStatusChange = async (needId, status) => {
    setStatusUpdating(needId);
    try {
      await api.put(`/api/needs/${needId}/status`, { status });
      fetchNeeds();
    } catch { }
    setStatusUpdating(null);
  };

  // ── Derived lists ────────────────────────────────────────────────
  const filterFn = n =>
    (n.category || '').toLowerCase().includes(filter.toLowerCase()) ||
    (n.location || '').toLowerCase().includes(filter.toLowerCase()) ||
    (n.description || '').toLowerCase().includes(filter.toLowerCase());

  const displayNeeds = isNgo && ngoTab === 'assigned'
    ? assignedNeeds.filter(filterFn)
    : needs.filter(filterFn);

  // ── Render ───────────────────────────────────────────────────────
  return (
    <div style={{ color: '#1e293b', fontFamily: 'Inter, sans-serif' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontWeight: 800, fontSize: '1.6rem', color: '#0f172a', marginBottom: '0.2rem' }}>
            {isAdmin ? '📋 All Needs' : '📋 My NGO Tasks'}
          </h1>
          <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
            {isAdmin ? `${needs.length} needs · Click a row to view Task Trail`
              : `${assignedNeeds.length} assigned · Click row for Task Trail`}
          </p>
        </div>
        <div style={{ position: 'relative' }}>
          <Search style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} size={16} />
          <input
            value={filter} onChange={e => setFilter(e.target.value)}
            placeholder="Search needs…"
            style={{ paddingLeft: '2.25rem', paddingRight: '1rem', paddingTop: '0.6rem', paddingBottom: '0.6rem', border: '1.5px solid #e2e8f0', borderRadius: '10px', fontFamily: 'inherit', fontSize: '0.875rem', outline: 'none', minWidth: '220px' }}
          />
        </div>
      </div>

      {/* NGO Tabs */}
      {isNgo && (
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', borderBottom: '1px solid #e2e8f0', paddingBottom: 0 }}>
          {[['assigned', '📤 Assigned to Me', assignedNeeds.length], ['submitted', '📝 My Submitted', needs.length]].map(([tab, label, cnt]) => (
            <button key={tab} onClick={() => setNgoTab(tab)}
              style={{ padding: '0.6rem 1.25rem', border: 'none', borderBottom: `2px solid ${ngoTab === tab ? '#6366f1' : 'transparent'}`, background: 'none', color: ngoTab === tab ? '#6366f1' : '#64748b', fontWeight: 600, fontSize: '0.875rem', cursor: 'pointer', fontFamily: 'inherit', transition: 'all 0.15s', position: 'relative', bottom: '-1px' }}>
              {label}
              <span style={{ marginLeft: '0.5rem', background: ngoTab === tab ? '#6366f1' : '#f1f5f9', color: ngoTab === tab ? '#fff' : '#64748b', fontSize: '0.7rem', fontWeight: 700, padding: '0.1rem 0.45rem', borderRadius: '999px' }}>{cnt}</span>
            </button>
          ))}
        </div>
      )}

      {loading && <p style={{ color: '#94a3b8', textAlign: 'center', padding: '3rem' }}>Loading needs…</p>}

      {!loading && displayNeeds.length === 0 && (
        <div style={{ textAlign: 'center', padding: '4rem', background: '#fff', borderRadius: '16px', border: '1.5px solid #f1f5f9' }}>
          <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📭</p>
          <p style={{ color: '#64748b' }}>No needs found.</p>
        </div>
      )}

      {/* Needs table */}
      {!loading && displayNeeds.length > 0 && (
        <div style={{ background: '#fff', borderRadius: '16px', border: '1.5px solid #f1f5f9', overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f8fafc' }}>
                {['#', 'Category', 'Location', 'Urgency', 'Status',
                  isNgo && ngoTab === 'assigned' ? 'My Status' : null,
                  'Actions'].filter(Boolean).map(h => (
                  <th key={h} style={{ padding: '0.8rem 1rem', textAlign: 'left', fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {displayNeeds.map(need => (
                <tr key={need.id}
                  onClick={() => setTrailNeed({ id: need.id, title: need.category })}
                  style={{ borderTop: '1px solid #f1f5f9', cursor: 'pointer', transition: 'background 0.1s' }}
                  onMouseOver={e => e.currentTarget.style.background = '#f8fafc'}
                  onMouseOut={e => e.currentTarget.style.background = 'transparent'}
                >
                  <td style={{ padding: '0.875rem 1rem', color: '#94a3b8', fontSize: '0.82rem' }}>#{need.id}</td>
                  <td style={{ padding: '0.875rem 1rem' }}>
                    <div style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.875rem' }}>{need.category}</div>
                    <div style={{ color: '#94a3b8', fontSize: '0.75rem', marginTop: '0.1rem', maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{need.description}</div>
                  </td>
                  <td style={{ padding: '0.875rem 1rem', color: '#64748b', fontSize: '0.82rem' }}>{need.location || '—'}</td>
                  <td style={{ padding: '0.875rem 1rem' }}><UrgencyBadge level={need.urgency} /></td>
                  <td style={{ padding: '0.875rem 1rem' }}><StatusBadge status={need.status} /></td>
                  {isNgo && ngoTab === 'assigned' && (
                    <td style={{ padding: '0.875rem 1rem' }}><AssignBadge status={need.ngo_assignment_status} /></td>
                  )}

                  {/* Actions cell */}
                  <td style={{ padding: '0.875rem 1rem' }} onClick={e => e.stopPropagation()}>
                    <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                      {/* Admin: assign to NGOs */}
                      {isAdmin && (
                        <>
                          <button
                            onClick={() => { setAssignModal(need); setSelectedNgos([]); setAssignNote(''); }}
                            style={actionBtn('#3b82f6')}>
                            <Users size={13} /> Assign NGO(s)
                          </button>
                          <select
                            defaultValue=""
                            onChange={e => e.target.value && handleStatusChange(need.id, e.target.value)}
                            style={{ fontSize: '0.72rem', padding: '0.28rem 0.5rem', borderRadius: '6px', border: '1px solid #e2e8f0', fontFamily: 'inherit', cursor: 'pointer', color: '#475569' }}
                          >
                            <option value="">Status…</option>
                            {['pending','assigned','in_progress','completed'].map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
                          </select>
                        </>
                      )}

                      {/* NGO assigned tab */}
                      {isNgo && ngoTab === 'assigned' && (
                        <>
                          {need.ngo_assignment_status === 'pending' && (
                            <>
                              <button disabled={statusUpdating === need.id} onClick={() => handleNgoAction(need.id, 'accept')} style={actionBtn('#10b981')}>
                                <CheckCircle size={13} /> Accept
                              </button>
                              <button disabled={statusUpdating === need.id} onClick={() => handleNgoAction(need.id, 'reject')} style={actionBtn('#ef4444')}>
                                <XCircle size={13} /> Reject
                              </button>
                            </>
                          )}
                          {need.ngo_assignment_status === 'accepted' && (
                            <>
                              <button disabled={statusUpdating === need.id} onClick={() => handleAutoAssign(need.id)} style={actionBtn('#8b5cf6')}>
                                <Zap size={13} /> Auto Assign
                              </button>
                              <button onClick={() => { setVolModal(need); setSelectedVols([]); }} style={actionBtn('#f59e0b')}>
                                <List size={13} /> Manual Assign
                              </button>
                            </>
                          )}
                        </>
                      )}

                      {/* Trail icon always */}
                      <button onClick={() => setTrailNeed({ id: need.id, title: need.category })} style={{ ...actionBtn('#6366f1'), background: 'transparent', border: '1px solid #e2e8f0', color: '#64748b' }}>
                        <Eye size={13} /> Trail
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── ADMIN: Assign to NGOs modal ───────────────────────────── */}
      {assignModal && (
        <div style={modalOverlay} onClick={() => setAssignModal(null)}>
          <div style={modalBox} onClick={e => e.stopPropagation()}>
            <h3 style={{ fontWeight: 800, fontSize: '1.1rem', marginBottom: '0.25rem', color: '#0f172a' }}>Assign Need to NGO(s)</h3>
            <p style={{ color: '#64748b', fontSize: '0.82rem', marginBottom: '1.25rem' }}>
              Need #{assignModal.id} · {assignModal.category} · <UrgencyBadge level={assignModal.urgency} />
            </p>

            <p style={{ fontWeight: 600, fontSize: '0.78rem', color: '#475569', marginBottom: '0.5rem' }}>Select NGO(s) to assign:</p>
            <div style={{ maxHeight: '220px', overflowY: 'auto', border: '1.5px solid #e2e8f0', borderRadius: '10px', marginBottom: '1rem' }}>
              {ngoOptions.map(n => (
                <label key={n.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.65rem 1rem', borderBottom: '1px solid #f1f5f9', cursor: 'pointer' }}
                  onMouseOver={e => e.currentTarget.style.background = '#f8fafc'}
                  onMouseOut={e => e.currentTarget.style.background = 'transparent'}>
                  <input type="checkbox" checked={selectedNgos.includes(n.id)} onChange={e => setSelectedNgos(prev => e.target.checked ? [...prev, n.id] : prev.filter(id => id !== n.id))} />
                  <span style={{ fontWeight: 500, fontSize: '0.875rem' }}>{n.name}</span>
                </label>
              ))}
              {ngoOptions.length === 0 && <p style={{ padding: '1rem', color: '#94a3b8', fontSize: '0.82rem' }}>No approved NGOs found.</p>}
            </div>

            <label style={{ display: 'block', fontWeight: 600, fontSize: '0.78rem', color: '#475569', marginBottom: '0.4rem' }}>Admin Note (optional)</label>
            <input value={assignNote} onChange={e => setAssignNote(e.target.value)} placeholder="Instructions for NGO…"
              style={{ width: '100%', padding: '0.625rem 0.875rem', border: '1.5px solid #e2e8f0', borderRadius: '8px', fontSize: '0.875rem', fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box', marginBottom: '1.25rem' }} />

            <div style={{ display: 'flex', gap: '0.625rem', justifyContent: 'flex-end' }}>
              <button onClick={() => setAssignModal(null)} style={cancelBtn}>Cancel</button>
              <button onClick={handleAssignNgos} disabled={assigning || !selectedNgos.length} style={{ ...primaryBtn('#3b82f6'), opacity: (!selectedNgos.length || assigning) ? 0.6 : 1 }}>
                {assigning ? 'Assigning…' : `Assign to ${selectedNgos.length} NGO(s)`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── NGO: Volunteer assign modal ───────────────────────────── */}
      {volModal && (
        <div style={modalOverlay} onClick={() => setVolModal(null)}>
          <div style={modalBox} onClick={e => e.stopPropagation()}>
            <h3 style={{ fontWeight: 800, fontSize: '1.1rem', marginBottom: '0.25rem', color: '#0f172a' }}>Assign Volunteers</h3>
            <p style={{ color: '#64748b', fontSize: '0.82rem', marginBottom: '1.25rem' }}>
              Need #{volModal.id} · {volModal.category} — Select one or more volunteers (team assignment)
            </p>

            <div style={{ maxHeight: '240px', overflowY: 'auto', border: '1.5px solid #e2e8f0', borderRadius: '10px', marginBottom: '1.25rem' }}>
              {myVolunteers.filter(v => v.availability).map(v => (
                <label key={v.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.65rem 1rem', borderBottom: '1px solid #f1f5f9', cursor: 'pointer' }}
                  onMouseOver={e => e.currentTarget.style.background = '#f8fafc'}
                  onMouseOut={e => e.currentTarget.style.background = 'transparent'}>
                  <input type="checkbox" checked={selectedVols.includes(v.id)} onChange={e => setSelectedVols(prev => e.target.checked ? [...prev, v.id] : prev.filter(id => id !== v.id))} />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{v.name}</div>
                    <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>{(v.skills || []).join(', ')}</div>
                  </div>
                </label>
              ))}
              {myVolunteers.filter(v => v.availability).length === 0 && (
                <p style={{ padding: '1.25rem', color: '#94a3b8', fontSize: '0.82rem', textAlign: 'center' }}>No available volunteers in your NGO.</p>
              )}
            </div>

            <div style={{ display: 'flex', gap: '0.625rem', justifyContent: 'flex-end' }}>
              <button onClick={() => setVolModal(null)} style={cancelBtn}>Cancel</button>
              <button onClick={handleVolAssign} disabled={assigningVols || !selectedVols.length} style={{ ...primaryBtn('#f59e0b'), opacity: (!selectedVols.length || assigningVols) ? 0.6 : 1 }}>
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

// ── Style helpers ─────────────────────────────────────────────────────────────
const actionBtn = (color) => ({
  display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
  padding: '0.3rem 0.65rem', borderRadius: '6px', border: 'none',
  background: color + '15', color, fontWeight: 600, fontSize: '0.72rem',
  cursor: 'pointer', fontFamily: 'inherit', transition: 'background 0.15s',
});
const modalOverlay = {
  position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.4)', zIndex: 300,
  display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem',
  backdropFilter: 'blur(4px)',
};
const modalBox = {
  background: '#fff', borderRadius: '20px', padding: '1.75rem',
  width: '100%', maxWidth: '480px', boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
};
const cancelBtn = {
  padding: '0.6rem 1.25rem', border: '1.5px solid #e2e8f0', background: '#fff',
  borderRadius: '10px', fontWeight: 600, fontSize: '0.875rem', cursor: 'pointer', fontFamily: 'inherit', color: '#64748b',
};
const primaryBtn = (color) => ({
  padding: '0.6rem 1.25rem', border: 'none', background: color,
  borderRadius: '10px', fontWeight: 700, fontSize: '0.875rem',
  cursor: 'pointer', fontFamily: 'inherit', color: '#fff',
});
