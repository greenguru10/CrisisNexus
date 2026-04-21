import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
const auth = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
const userRole = () => localStorage.getItem('role');

const RANK_STYLES = [
  { bg: 'linear-gradient(135deg,#f59e0b,#d97706)', text: '#fff', label: '🥇' },
  { bg: 'linear-gradient(135deg,#94a3b8,#64748b)', text: '#fff', label: '🥈' },
  { bg: 'linear-gradient(135deg,#cd7f32,#a85e21)', text: '#fff', label: '🥉' },
];

export default function Leaderboard() {
  const isAdmin = userRole() === 'admin';
  const ngoId   = localStorage.getItem('ngo_id');
  const ngoName = localStorage.getItem('ngo_name');

  const [ngoOptions, setNgoOptions]   = useState([]);
  const [ngoFilter, setNgoFilter]     = useState(ngoId || '');
  const [data, setData]               = useState(null);
  const [loading, setLoading]         = useState(true);

  // Fetch NGO names for admin filter dropdown
  useEffect(() => {
    if (isAdmin) {
      axios.get(`${API}/api/ngo/names`, auth()).then(r => setNgoOptions(r.data)).catch(() => {});
    }
  }, [isAdmin]);

  const fetchLeaderboard = async (id) => {
    setLoading(true);
    try {
      const params = id ? `?ngo_id=${id}` : '';
      const lb = await axios.get(`${API}/api/gamification/leaderboard${params}`, auth());
      setData(lb.data);
    } catch { }
    setLoading(false);
  };

  useEffect(() => { fetchLeaderboard(ngoFilter); }, [ngoFilter]);

  return (
    <div style={{ color: '#1e293b', fontFamily: 'Inter, sans-serif' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '0.25rem', color: '#0f172a' }}>🏆 Leaderboard</h1>
          <p style={{ color: '#64748b' }}>NGO-scoped volunteer rankings by tasks completed and performance.</p>
        </div>

        {/* Admin NGO filter */}
        {isAdmin && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, color: '#64748b' }}>Filter by NGO:</label>
            <select
              value={ngoFilter}
              onChange={e => setNgoFilter(e.target.value)}
              style={{ padding: '0.55rem 1rem', borderRadius: '10px', border: '1.5px solid #e2e8f0', background: '#fff', color: '#1e293b', fontSize: '0.875rem', fontFamily: 'inherit', cursor: 'pointer', minWidth: '220px', outline: 'none' }}
            >
              <option value="">🌐 Global (All NGOs)</option>
              {ngoOptions.map(n => (
                <option key={n.id} value={n.id}>{n.name}</option>
              ))}
            </select>
            {ngoFilter && (
              <button onClick={() => setNgoFilter('')}
                style={{ padding: '0.5rem 0.875rem', borderRadius: '8px', border: '1px solid #e2e8f0', background: '#fff', color: '#64748b', cursor: 'pointer', fontSize: '0.82rem', fontFamily: 'inherit' }}>
                Clear ✕
              </button>
            )}
          </div>
        )}
      </div>

      {/* NGO context banner */}
      {ngoName && !isAdmin && (
        <div style={{ padding: '0.75rem 1.25rem', borderRadius: '10px', background: '#eff6ff', border: '1px solid #bfdbfe', color: '#1e40af', fontSize: '0.875rem', marginBottom: '1.5rem', fontWeight: 500 }}>
          🏢 Showing leaderboard for: <strong>{ngoName}</strong>
        </div>
      )}
      {isAdmin && ngoFilter && (
        <div style={{ padding: '0.75rem 1.25rem', borderRadius: '10px', background: '#eff6ff', border: '1px solid #bfdbfe', color: '#1e40af', fontSize: '0.875rem', marginBottom: '1.5rem', fontWeight: 500 }}>
          🏢 Showing leaderboard for: <strong>{ngoOptions.find(n => String(n.id) === String(ngoFilter))?.name || `NGO #${ngoFilter}`}</strong>
        </div>
      )}

      {loading && (
        <div style={{ textAlign: 'center', paddingTop: '2rem', color: '#94a3b8' }}>Loading leaderboard…</div>
      )}

      {/* Leaderboard rows */}
      {!loading && data?.leaderboard && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
          {data.leaderboard.length === 0 && (
            <div style={{ background: '#fff', border: '1.5px solid #f1f5f9', borderRadius: '16px', padding: '3rem', textAlign: 'center', color: '#94a3b8', boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
              No volunteers ranked yet in this scope.
            </div>
          )}
          {data.leaderboard.map((v, i) => {
            const rs = RANK_STYLES[i] || { bg: '#f8fafc', text: '#64748b', label: `#${v.rank}` };
            const isTop = i < 3;
            return (
              <div key={v.volunteer_id}
                style={{
                  background: '#fff',
                  border: `1.5px solid ${i === 0 ? '#fde68a' : i === 1 ? '#e2e8f0' : i === 2 ? '#fed7aa' : '#f1f5f9'}`,
                  borderRadius: '14px', padding: '1.25rem 1.5rem',
                  display: 'flex', alignItems: 'center', gap: '1.25rem',
                  boxShadow: isTop ? '0 4px 16px rgba(0,0,0,0.07)' : '0 1px 4px rgba(0,0,0,0.03)',
                  transition: 'transform 0.15s, box-shadow 0.15s',
                }}
                onMouseOver={e => { e.currentTarget.style.transform = 'translateX(4px)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(0,0,0,0.1)'; }}
                onMouseOut={e => { e.currentTarget.style.transform = 'translateX(0)'; e.currentTarget.style.boxShadow = isTop ? '0 4px 16px rgba(0,0,0,0.07)' : '0 1px 4px rgba(0,0,0,0.03)'; }}>

                {/* Rank badge */}
                <div style={{
                  width: '44px', height: '44px', borderRadius: '12px',
                  background: rs.bg, display: 'flex', alignItems: 'center',
                  justifyContent: 'center', fontSize: isTop ? '1.4rem' : '1rem',
                  fontWeight: 800, color: rs.text, flexShrink: 0,
                }}>
                  {rs.label}
                </div>

                {/* Info */}
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: '1rem', color: '#0f172a', marginBottom: '0.35rem' }}>{v.name}</div>
                  <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                    <span style={{ color: '#6366f1', fontSize: '0.85rem', fontWeight: 600 }}>✅ {v.tasks_completed} tasks</span>
                    <span style={{ color: '#f59e0b', fontSize: '0.85rem' }}>⭐ {v.rating?.toFixed(1) || '—'}</span>
                    <span style={{ color: v.availability ? '#10b981' : '#ef4444', fontSize: '0.82rem', fontWeight: 500 }}>
                      {v.availability ? '🟢 Available' : '🔴 Busy'}
                    </span>
                  </div>
                </div>

                {/* Score */}
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 800, color: isTop ? '#f59e0b' : '#6366f1' }}>{v.tasks_completed}</div>
                  <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 500 }}>tasks done</div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
