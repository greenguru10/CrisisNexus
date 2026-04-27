import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
const auth = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
const userRole = () => localStorage.getItem('role');

const Stat = ({ label, value, color = '#6366f1', icon }) => (
  <div style={{ background: '#fff', border: '1.5px solid #f1f5f9', borderRadius: '14px', padding: '1.25rem 1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
    <div style={{ color: '#94a3b8', fontSize: '0.78rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>{icon} {label}</div>
    <div style={{ fontSize: '2rem', fontWeight: 800, color }}>{value ?? '—'}</div>
  </div>
);

const Bar = ({ label, value, max, color = '#6366f1' }) => (
  <div style={{ marginBottom: '0.75rem' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem' }}>
      <span style={{ color: '#64748b', textTransform: 'capitalize' }}>{label?.replace(/_/g, ' ')}</span>
      <span style={{ fontWeight: 600, color: '#374151' }}>{value}</span>
    </div>
    <div style={{ height: '8px', borderRadius: '999px', background: '#f1f5f9', overflow: 'hidden' }}>
      <div style={{ height: '100%', width: `${max > 0 ? (value / max) * 100 : 0}%`, background: color, borderRadius: '999px', transition: 'width 0.6s ease' }} />
    </div>
  </div>
);

const Funnel = ({ stages }) => {
  const max = stages?.[0]?.count || 1;
  const colors = ['#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {stages?.map((s, i) => (
        <div key={s.stage} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: '110px', fontSize: '0.82rem', color: '#64748b', flexShrink: 0 }}>{s.stage}</div>
          <div style={{ flex: 1, height: '30px', background: '#f1f5f9', borderRadius: '6px', overflow: 'hidden', position: 'relative' }}>
            <div style={{ height: '100%', width: `${(s.count / max) * 100}%`, background: colors[i] || '#6366f1', borderRadius: '6px', display: 'flex', alignItems: 'center', paddingLeft: '0.75rem', transition: 'width 0.7s ease' }}>
              <span style={{ color: '#fff', fontWeight: 700, fontSize: '0.82rem' }}>{s.count}</span>
            </div>
          </div>
          <div style={{ width: '44px', textAlign: 'right', fontSize: '0.78rem', color: '#94a3b8' }}>
            {max > 0 ? Math.round((s.count / max) * 100) : 0}%
          </div>
        </div>
      ))}
    </div>
  );
};

const card = { background: '#fff', border: '1.5px solid #f1f5f9', borderRadius: '16px', padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' };

export default function Analytics() {
  const isAdmin = userRole() === 'admin';
  const myNgoId = localStorage.getItem('ngo_id');

  const [ngoOptions, setNgoOptions] = useState([]);
  const [selectedNgoId, setSelectedNgoId] = useState(''); // '' = all (admin) or own (ngo)

  const [overview, setOverview] = useState(null);
  const [funnel, setFunnel] = useState(null);
  const [efficiency, setEfficiency] = useState([]);
  const [loading, setLoading] = useState(true);

  // Load NGO name list for admin filter
  useEffect(() => {
    if (isAdmin) {
      axios.get(`${API}/api/ngo/names`, auth()).then(r => setNgoOptions(r.data)).catch(() => {});
    }
  }, [isAdmin]);

  // Fetch analytics whenever the NGO filter changes
  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      try {
        const ngoId = isAdmin ? selectedNgoId : myNgoId;
        const suffix = ngoId ? `?ngo_id=${ngoId}` : '';
        const [ov, fn, ef] = await Promise.all([
          axios.get(`${API}/api/analytics/overview${suffix}`, auth()),
          axios.get(`${API}/api/analytics/funnel${suffix}`, auth()),
          axios.get(`${API}/api/analytics/volunteer-efficiency${suffix}`, auth()),
        ]);
        setOverview(ov.data);
        setFunnel(fn.data);
        setEfficiency(ef.data);
      } catch { }
      setLoading(false);
    };
    fetchAll();
  }, [selectedNgoId, isAdmin, myNgoId]);

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px', color: '#94a3b8', fontFamily: 'Inter, sans-serif' }}>
      Loading analytics…
    </div>
  );

  const needs = overview?.needs;
  const vols  = overview?.volunteers;
  const catMax = needs?.category_breakdown ? Math.max(...Object.values(needs.category_breakdown)) : 1;
  const urgMax = needs?.urgency_breakdown  ? Math.max(...Object.values(needs.urgency_breakdown))  : 1;

  return (
    <div style={{ color: '#1e293b', fontFamily: 'Inter, sans-serif' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '0.25rem', color: '#0f172a' }}>📊 Analytics Dashboard</h1>
          <p style={{ color: '#64748b' }}>
            {isAdmin ? 'System-wide performance insights across all NGOs.' : 'Your NGO\'s performance and impact metrics.'}
          </p>
        </div>

        {/* Admin NGO filter dropdown */}
        {isAdmin && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, color: '#64748b' }}>Filter by NGO:</label>
            <select
              value={selectedNgoId}
              onChange={e => setSelectedNgoId(e.target.value)}
              style={{ padding: '0.55rem 1rem', borderRadius: '10px', border: '1.5px solid #e2e8f0', background: '#fff', color: '#1e293b', fontSize: '0.875rem', fontFamily: 'inherit', cursor: 'pointer', minWidth: '220px', outline: 'none' }}
            >
              <option value="">🌐 All NGOs (System-wide)</option>
              {ngoOptions.map(n => (
                <option key={n.id} value={n.id}>{n.name}</option>
              ))}
            </select>
            {selectedNgoId && (
              <button onClick={() => setSelectedNgoId('')}
                style={{ padding: '0.5rem 0.875rem', borderRadius: '8px', border: '1px solid #e2e8f0', background: '#fff', color: '#64748b', cursor: 'pointer', fontSize: '0.82rem', fontFamily: 'inherit' }}>
                Clear ✕
              </button>
            )}
          </div>
        )}
      </div>

      {/* NGO admin overview */}
      {isAdmin && !selectedNgoId && overview && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          <Stat icon="🏢" label="Total NGOs"      value={overview.total_ngos}   color="#8b5cf6" />
          <Stat icon="✅" label="Active NGOs"     value={overview.approved_ngos} color="#10b981" />
          <Stat icon="⏳" label="Pending Approval" value={overview.pending_ngos}  color="#f59e0b" />
        </div>
      )}

      {selectedNgoId && (
        <div style={{ padding: '0.75rem 1.25rem', borderRadius: '10px', background: '#eff6ff', border: '1px solid #bfdbfe', color: '#1e40af', fontSize: '0.875rem', marginBottom: '1.5rem', fontWeight: 500 }}>
          🏢 Showing data for: <strong>{ngoOptions.find(n => String(n.id) === String(selectedNgoId))?.name || `NGO #${selectedNgoId}`}</strong>
        </div>
      )}

      {/* Core need stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(155px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <Stat icon="📋" label="Total Needs" value={needs?.total_needs}  color="#6366f1" />
        <Stat icon="✅" label="Completed"   value={needs?.completed}    color="#10b981" />
        <Stat icon="⚡" label="In Progress" value={needs?.in_progress}  color="#f59e0b" />
        <Stat icon="🎯" label="Completion %" value={`${needs?.completion_rate_pct ?? 0}%`} color="#8b5cf6" />
        <Stat icon="👥" label="Volunteers"  value={vols?.total_volunteers}    color="#6366f1" />
        <Stat icon="🟢" label="Available"   value={vols?.available_volunteers} color="#10b981" />
        <Stat icon="⭐" label="Avg Rating"  value={vols?.average_rating?.toFixed(1)} color="#f59e0b" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Funnel */}
        <div style={card}>
          <h3 style={{ fontWeight: 700, marginBottom: '1.25rem', fontSize: '1rem', color: '#0f172a' }}>📉 Response Funnel</h3>
          <Funnel stages={funnel?.funnel} />
        </div>

        {/* Category */}
        <div style={card}>
          <h3 style={{ fontWeight: 700, marginBottom: '1.25rem', fontSize: '1rem', color: '#0f172a' }}>🗂️ Category Breakdown</h3>
          {Object.entries(needs?.category_breakdown || {}).map(([cat, count]) => (
            <Bar key={cat} label={cat} value={count} max={catMax} color="#6366f1" />
          ))}
          {Object.keys(needs?.category_breakdown || {}).length === 0 && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>No data available.</p>}
        </div>

        {/* Urgency */}
        <div style={card}>
          <h3 style={{ fontWeight: 700, marginBottom: '1.25rem', fontSize: '1rem', color: '#0f172a' }}>🚨 Urgency Distribution</h3>
          {Object.entries(needs?.urgency_breakdown || {}).map(([urg, count]) => {
            const colors = { high: '#ef4444', medium: '#f59e0b', low: '#10b981' };
            return <Bar key={urg} label={urg} value={count} max={urgMax} color={colors[urg] || '#6366f1'} />;
          })}
        </div>

        {/* Top Volunteers */}
        <div style={card}>
          <h3 style={{ fontWeight: 700, marginBottom: '1.25rem', fontSize: '1rem', color: '#0f172a' }}>🏆 Top Volunteers</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr>
                {['Name', 'Tasks', 'Rating', 'Available'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '0.5rem 0.75rem', color: '#94a3b8', fontWeight: 600, fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {efficiency.slice(0, 8).map(v => (
                <tr key={v.id} style={{ borderTop: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '0.6rem 0.75rem', fontWeight: 600, color: '#0f172a' }}>{v.name}</td>
                  <td style={{ padding: '0.6rem 0.75rem', color: '#6366f1', fontWeight: 700 }}>{v.tasks_completed}</td>
                  <td style={{ padding: '0.6rem 0.75rem', color: '#f59e0b' }}>
                    {'⭐'.repeat(Math.min(5, Math.round(v.rating || 0)))}{v.rating ? ` ${v.rating?.toFixed(1)}` : ' —'}
                  </td>
                  <td style={{ padding: '0.6rem 0.75rem' }}>
                    <span style={{ color: v.availability ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                      {v.availability ? 'Yes' : 'No'}
                    </span>
                  </td>
                </tr>
              ))}
              {efficiency.length === 0 && (
                <tr><td colSpan={4} style={{ padding: '1rem', textAlign: 'center', color: '#94a3b8' }}>No volunteer data yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
