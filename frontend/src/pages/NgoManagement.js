import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Users, FileText, CheckCircle, XCircle, Clock, Building2 } from 'lucide-react';

const STATUS_COLORS = {
  pending: { bg: '#fef3c7', text: '#92400e', border: '#fbbf24' },
  approved: { bg: '#d1fae5', text: '#065f46', border: '#34d399' },
  rejected: { bg: '#fee2e2', text: '#991b1b', border: '#f87171' },
  suspended: { bg: '#f1f5f9', text: '#475569', border: '#94a3b8' },
};

function StatusBadge({ status }) {
  const c = STATUS_COLORS[status] || STATUS_COLORS.suspended;
  return (
    <span style={{
      padding: '0.2rem 0.7rem', borderRadius: '999px', fontSize: '0.75rem',
      fontWeight: 700, background: c.bg, color: c.text, border: '1px solid ' + c.border,
      textTransform: 'capitalize',
    }}>{status}</span>
  );
}

function ActionBtn({ children, color, bg, onClick }) {
  return (
    <button onClick={onClick}
      style={{ padding: '0.3rem 0.8rem', borderRadius: '6px', border: '1px solid ' + color + '44', background: bg || (color + '11'), color: color, cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600, transition: 'background 0.15s' }}
      onMouseOver={e => e.target.style.background = color + '22'}
      onMouseOut={e => e.target.style.background = bg || (color + '11')}>
      {children}
    </button>
  );
}

export default function NgoManagement() {
  const [ngos, setNgos] = useState([]);
  const [filter, setFilter] = useState('all');
  const [selected, setSelected] = useState(null);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const fetchNgos = async () => {
    try {
      const params = filter !== 'all' ? '?status=' + filter : '';
      const res = await api.get('/api/ngo' + params);
      setNgos(res.data);
    } catch (e) { console.error(e); }
  };

  useEffect(() => { fetchNgos(); }, [filter]);

  const act = async (ngoId, action) => {
    setLoading(true); setMsg('');
    try {
      await api.post('/api/ngo/' + ngoId + '/' + action, { admin_notes: notes });
      setMsg('NGO successfully ' + action + 'd.');
      setSelected(null); setNotes('');
      fetchNgos();
    } catch (e) {
      setMsg(e.response?.data?.detail || 'Failed to ' + action);
    } finally { setLoading(false); }
  };

  const filtered = filter === 'all' ? ngos : ngos.filter(n => n.status === filter);
  const counts = {
    all: ngos.length,
    pending: ngos.filter(n => n.status === 'pending').length,
    approved: ngos.filter(n => n.status === 'approved').length,
    rejected: ngos.filter(n => n.status === 'rejected').length,
  };

  const card = { background: '#fff', border: '1px solid #e2e8f0', borderRadius: '16px', padding: '1.5rem' };

  return (
    <div style={{ fontFamily: 'Inter, sans-serif', color: '#0f172a' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Building2 size={24} style={{ color: '#6366f1' }} /> NGO Management
        </h1>
        <p style={{ color: '#64748b', marginTop: '0.25rem', fontSize: '0.92rem' }}>
          Approve, reject, and oversee all registered NGOs.
        </p>
      </div>

      {/* Filter pills */}
      <div style={{ display: 'flex', gap: '0.6rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
        {Object.entries(counts).map(([k, v]) => (
          <button key={k} onClick={() => setFilter(k)}
            style={{
              padding: '0.4rem 1rem', borderRadius: '999px', fontWeight: 600, fontSize: '0.83rem', cursor: 'pointer', border: '1.5px solid',
              borderColor: filter === k ? '#6366f1' : '#e2e8f0',
              background: filter === k ? '#ede9fe' : '#fff',
              color: filter === k ? '#4f46e5' : '#64748b',
              transition: 'all 0.15s',
            }}>
            {k.charAt(0).toUpperCase() + k.slice(1)} ({v})
          </button>
        ))}
      </div>

      {msg && (
        <div style={{
          padding: '0.75rem 1rem', borderRadius: '10px', marginBottom: '1rem', fontSize: '0.88rem',
          background: msg.toLowerCase().includes('fail') ? '#fef2f2' : '#f0fdf4',
          border: '1px solid ' + (msg.toLowerCase().includes('fail') ? '#fecaca' : '#bbf7d0'),
          color: msg.toLowerCase().includes('fail') ? '#dc2626' : '#15803d',
        }}>{msg}</div>
      )}

      {/* Table */}
      <div style={card}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #f1f5f9' }}>
                {['NGO Name', 'Type', 'Location', 'Volunteers', 'Needs', 'Status', 'Actions'].map(h => (
                  <th key={h} style={{ padding: '0.75rem 1rem', textAlign: 'left', color: '#64748b', fontWeight: 700, fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr><td colSpan={7} style={{ padding: '2.5rem', textAlign: 'center', color: '#94a3b8' }}>No NGOs found</td></tr>
              )}
              {filtered.map(ngo => (
                <tr key={ngo.id} style={{ borderBottom: '1px solid #f8fafc', transition: 'background 0.12s' }}
                  onMouseOver={e => e.currentTarget.style.background = '#f8fafc'}
                  onMouseOut={e => e.currentTarget.style.background = 'transparent'}>
                  <td style={{ padding: '1rem', fontWeight: 700, color: '#1e293b' }}>{ngo.name}</td>
                  <td style={{ padding: '1rem', color: '#64748b' }}>{ngo.ngo_type?.replace(/_/g, ' ')}</td>
                  <td style={{ padding: '1rem', color: '#64748b' }}>{ngo.location || '—'}</td>
                  <td style={{ padding: '1rem' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', padding: '0.2rem 0.6rem', borderRadius: '8px', background: '#eff6ff', color: '#2563eb', fontWeight: 700, fontSize: '0.85rem' }}>
                      <Users size={13} />{ngo.volunteer_count ?? 0}
                    </span>
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', padding: '0.2rem 0.6rem', borderRadius: '8px', background: '#f5f3ff', color: '#7c3aed', fontWeight: 700, fontSize: '0.85rem' }}>
                      <FileText size={13} />{ngo.need_count ?? 0}
                    </span>
                  </td>
                  <td style={{ padding: '1rem' }}><StatusBadge status={ngo.status} /></td>
                  <td style={{ padding: '1rem' }}>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      {ngo.status === 'pending' && (
                        <>
                          <ActionBtn color="#10b981" onClick={() => setSelected({ id: ngo.id, action: 'approve', name: ngo.name })}>
                            Approve
                          </ActionBtn>
                          <ActionBtn color="#ef4444" onClick={() => setSelected({ id: ngo.id, action: 'reject', name: ngo.name })}>
                            Reject
                          </ActionBtn>
                        </>
                      )}
                      {ngo.status === 'approved' && (
                        <ActionBtn color="#ef4444" onClick={() => setSelected({ id: ngo.id, action: 'reject', name: ngo.name })}>
                          Suspend
                        </ActionBtn>
                      )}
                      {ngo.status === 'rejected' && (
                        <ActionBtn color="#10b981" onClick={() => setSelected({ id: ngo.id, action: 'approve', name: ngo.name })}>
                          Re-approve
                        </ActionBtn>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Confirmation modal */}
      {selected && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(15,23,42,0.5)', backdropFilter: 'blur(4px)' }}>
          <div style={{ background: '#fff', borderRadius: '16px', padding: '2rem', width: '420px', maxWidth: '95vw', boxShadow: '0 20px 60px rgba(0,0,0,0.15)', border: '1px solid #e2e8f0' }}>
            <h3 style={{ fontWeight: 700, marginBottom: '0.5rem', textTransform: 'capitalize', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0f172a' }}>
              {selected.action === 'approve' ? <CheckCircle size={20} color="#10b981" /> : <XCircle size={20} color="#ef4444" />}
              {selected.action} NGO
            </h3>
            <p style={{ color: '#64748b', marginBottom: '1.25rem', fontSize: '0.9rem' }}>
              {selected.action === 'approve' ? 'Approving' : 'Rejecting'} <strong style={{ color: '#1e293b' }}>{selected.name}</strong>.<br />
              The NGO coordinator will be notified.
            </p>
            <textarea value={notes} onChange={e => setNotes(e.target.value)}
              placeholder="Add notes (optional)..." rows={3}
              style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1.5px solid #e2e8f0', background: '#f8fafc', color: '#1e293b', fontSize: '0.9rem', resize: 'vertical', boxSizing: 'border-box', marginBottom: '1.25rem', outline: 'none', fontFamily: 'inherit' }}
            />
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button onClick={() => { setSelected(null); setNotes(''); }}
                style={{ padding: '0.6rem 1.25rem', borderRadius: '8px', border: '1.5px solid #e2e8f0', background: '#fff', color: '#64748b', cursor: 'pointer', fontWeight: 600 }}>
                Cancel
              </button>
              <button onClick={() => act(selected.id, selected.action)} disabled={loading}
                style={{ padding: '0.6rem 1.5rem', borderRadius: '8px', border: 'none', background: selected.action === 'approve' ? '#10b981' : '#ef4444', color: '#fff', cursor: 'pointer', fontWeight: 700, opacity: loading ? 0.7 : 1, fontFamily: 'inherit' }}>
                {loading ? 'Processing...' : 'Confirm ' + selected.action}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
