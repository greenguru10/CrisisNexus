// TaskTrailPanel — right-side slide-in panel showing the full audit trail for a need.
// Usage: <TaskTrailPanel needId={id} onClose={() => setTrailNeed(null)} />
import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { X, Clock } from 'lucide-react';

const ACTION_META = {
  created:            { icon: '📋', label: 'Need Created',           color: '#6366f1' },
  submitted_by_ngo:   { icon: '🏢', label: 'Submitted by NGO',       color: '#8b5cf6' },
  approved_by_admin:  { icon: '✅', label: 'Approved by Admin',       color: '#10b981' },
  assigned_to_ngo:    { icon: '📤', label: 'Assigned to NGO(s)',      color: '#3b82f6' },
  ngo_accepted:       { icon: '🤝', label: 'NGO Accepted',            color: '#10b981' },
  ngo_rejected:       { icon: '❌', label: 'NGO Rejected',            color: '#ef4444' },
  volunteer_assigned: { icon: '👤', label: 'Volunteer(s) Assigned',   color: '#f59e0b' },
  status_changed:     { icon: '🔄', label: 'Status Updated',          color: '#64748b' },
  completed:          { icon: '🎉', label: 'Task Completed',          color: '#10b981' },
  resource_requested: { icon: '📦', label: 'Resource Requested',      color: '#f59e0b' },
  resource_allocated: { icon: '✅', label: 'Resource Allocated',      color: '#10b981' },
  pool_assigned:      { icon: '🤝', label: 'Pool Volunteers Added',   color: '#3b82f6' },
};

function fmtTime(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
  } catch (e) { return iso; }
}

function DetailPill({ label, value }) {
  if (!value) return null;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
      padding: '0.2rem 0.6rem', borderRadius: '999px', background: '#f1f5f9',
      fontSize: '0.75rem', color: '#475569', fontWeight: 500,
      marginRight: '0.35rem', marginTop: '0.35rem',
    }}>
      {label}: <strong>{value}</strong>
    </span>
  );
}

export default function TaskTrailPanel({ needId, needTitle, onClose }) {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [note, setNote] = useState('');
  const [posting, setPosting] = useState(false);
  const role = localStorage.getItem('role');
  const canNote = role === 'admin' || role === 'ngo';

  useEffect(() => {
    if (!needId) return;
    setLoading(true);
    api.get('/api/needs/' + needId + '/trail')
      .then(r => setEntries(r.data))
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, [needId]);

  const addNote = async () => {
    if (!note.trim()) return;
    setPosting(true);
    try {
      const r = await api.post('/api/needs/' + needId + '/trail/note', { note: note });
      setEntries(function(prev) { return [...prev, r.data]; });
      setNote('');
    } catch (e) { /* silent */ }
    setPosting(false);
  };

  const panelStyle = {
    position: 'fixed', top: 0, right: 0, bottom: 0,
    width: '480px', maxWidth: '100vw',
    background: '#fff', zIndex: 201, display: 'flex',
    flexDirection: 'column', boxShadow: '-8px 0 40px rgba(0,0,0,0.12)',
  };

  return (
    <React.Fragment>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.3)', zIndex: 200, backdropFilter: 'blur(2px)' }} />

      <div style={panelStyle}>
        {/* Header */}
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexShrink: 0 }}>
          <div>
            <p style={{ fontSize: '0.72rem', fontWeight: 700, color: '#6366f1', letterSpacing: '0.06em', marginBottom: '0.25rem' }}>TASK TRAIL</p>
            <h3 style={{ fontWeight: 800, fontSize: '1rem', color: '#0f172a', margin: 0 }}>
              Need #{needId}{needTitle ? ' — ' + needTitle : ''}
            </h3>
          </div>
          <button onClick={onClose} style={{ border: 'none', background: '#f1f5f9', borderRadius: '8px', width: '32px', height: '32px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
            <X size={16} />
          </button>
        </div>

        {/* Timeline */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem' }}>
          {loading && <p style={{ color: '#94a3b8', textAlign: 'center', paddingTop: '2rem' }}>Loading trail...</p>}

          {!loading && entries.length > 0 && (
            <div style={{ marginBottom: '2rem', padding: '1rem', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              <p style={{ fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Task Origin</p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>Created on {fmtTime(entries[0].created_at)}</span>
                <span style={{ fontSize: '0.82rem', color: '#6366f1', fontWeight: 600 }}>by {entries[0].actor_name || entries[0].actor_role}</span>
              </div>
            </div>
          )}

          {!loading && entries.length === 0 && (
            <div style={{ textAlign: 'center', paddingTop: '3rem', color: '#94a3b8' }}>
              <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📋</p>
              <p>No trail entries yet.</p>
            </div>
          )}

          {entries.map((entry, i) => {
            const meta = ACTION_META[entry.action] || { icon: '•', label: entry.action, color: '#94a3b8' };
            const d = entry.detail_json || {};
            return (
              <div key={entry.id} style={{ display: 'flex', gap: '0.875rem', position: 'relative', marginBottom: '1.25rem' }}>
                {i < entries.length - 1 && (
                  <div style={{ position: 'absolute', left: '17px', top: '36px', bottom: '-1.25rem', width: '2px', background: '#f1f5f9' }} />
                )}
                <div style={{ width: '34px', height: '34px', borderRadius: '50%', background: meta.color + '15', border: '2px solid ' + meta.color + '30', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem', flexShrink: 0 }}>
                  {meta.icon}
                </div>
                <div style={{ flex: 1, paddingTop: '0.1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.875rem', color: '#0f172a' }}>{meta.label}</span>
                    <span style={{ fontSize: '0.72rem', color: '#94a3b8', flexShrink: 0, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Clock size={11} />{fmtTime(entry.created_at)}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: '#64748b', margin: '0.2rem 0 0.4rem' }}>
                    by <strong>{entry.actor_name || entry.actor_role}</strong>
                  </p>
                  <div style={{ display: 'flex', flexWrap: 'wrap' }}>
                    {d.ngo_names && d.ngo_names.length > 0 && <DetailPill label="NGOs" value={d.ngo_names.join(', ')} />}
                    {d.volunteer_names && d.volunteer_names.length > 0 && <DetailPill label="Volunteers" value={d.volunteer_names.join(', ')} />}
                    {d.note && <DetailPill label="Note" value={d.note} />}
                    {d.old_status && d.new_status && <DetailPill label="Status" value={d.old_status + ' to ' + d.new_status} />}
                    {d.resource_name && <DetailPill label="Resource" value={d.resource_name + ' (' + (d.quantity || d.qty || 0) + ' ' + (d.unit || '') + ')'} />}
                    {d.feedback_rating && <DetailPill label="Rating" value={d.feedback_rating + ' / 5'} />}
                    {d.fully_completed && <DetailPill label="Final" value="Task Fully Closed" />}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Add note */}
        {canNote && (
          <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid #e2e8f0', flexShrink: 0 }}>
            <p style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', marginBottom: '0.5rem' }}>Add a note</p>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                value={note}
                onChange={function(e) { setNote(e.target.value); }}
                onKeyDown={function(e) { if (e.key === 'Enter') addNote(); }}
                placeholder="Type a note and press Enter..."
                style={{ flex: 1, padding: '0.6rem 0.875rem', borderRadius: '8px', border: '1.5px solid #e2e8f0', fontSize: '0.85rem', outline: 'none', fontFamily: 'inherit' }}
              />
              <button
                onClick={addNote}
                disabled={posting || !note.trim()}
                style={{ padding: '0.6rem 1rem', borderRadius: '8px', border: 'none', background: '#6366f1', color: '#fff', fontWeight: 600, fontSize: '0.82rem', cursor: 'pointer', opacity: (posting ? 0.6 : 1), fontFamily: 'inherit' }}
              >
                Post
              </button>
            </div>
          </div>
        )}
      </div>
    </React.Fragment>
  );
}
