import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
const auth = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
const role = () => localStorage.getItem('role');
const REQ_COLORS = { pending:'#f59e0b', approved:'#10b981', rejected:'#ef4444', expired:'#64748b', completed:'#6366f1' };

export default function PoolRequests() {
  const isAdmin = role() === 'admin';
  const [requests, setRequests] = useState([]);
  const [myRequests, setMyRequests] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [approveModal, setApproveModal] = useState(null);
  const [form, setForm] = useState({ source_ngo_id:'', required_skills:'', volunteers_needed:1, reason:'', duration_days:7 });
  const [approveForm, setApproveForm] = useState({ volunteer_ids:'', admin_notes:'' });
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const fetch = async () => {
    if (isAdmin) {
      axios.get(`${API}/api/pool/requests`, auth()).then(r => setRequests(r.data)).catch(()=>{});
    } else {
      axios.get(`${API}/api/pool/my-requests`, auth()).then(r => setMyRequests(r.data)).catch(()=>{});
    }
  };

  useEffect(() => { fetch(); }, []);

  const handleSubmit = async e => {
    e.preventDefault(); setLoading(true); setMsg('');
    try {
      await axios.post(`${API}/api/pool/request`, {
        source_ngo_id: form.source_ngo_id ? parseInt(form.source_ngo_id) : null,
        required_skills: form.required_skills ? form.required_skills.split(',').map(s=>s.trim()).filter(Boolean) : [],
        volunteers_needed: parseInt(form.volunteers_needed),
        reason: form.reason,
        duration_days: parseInt(form.duration_days),
      }, auth());
      setMsg('Pool request submitted!'); setShowForm(false); fetch();
    } catch(e) { setMsg(e.response?.data?.detail || 'Request failed'); }
    finally { setLoading(false); }
  };

  const handleApprove = async e => {
    e.preventDefault(); setLoading(true);
    try {
      const ids = approveForm.volunteer_ids.split(',').map(s=>parseInt(s.trim())).filter(Boolean);
      await axios.post(`${API}/api/pool/request/${approveModal.id}/approve`, { volunteer_ids:ids, admin_notes:approveForm.admin_notes }, auth());
      setMsg('Pool request approved!'); setApproveModal(null); fetch();
    } catch(e) { setMsg(e.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  const handleReject = async (id) => {
    await axios.post(`${API}/api/pool/request/${id}/reject`, { admin_notes:'Rejected by admin' }, auth()).catch(()=>{});
    fetch();
  };

  const list = isAdmin ? requests : myRequests;

  return (
    <div style={{ color:'#f1f5f9', fontFamily:'Inter, sans-serif' }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:'2rem', flexWrap:'wrap', gap:'1rem' }}>
        <div>
          <h1 style={{ fontSize:'1.75rem', fontWeight:800, marginBottom:'0.25rem' }}>🤝 Volunteer Pool Requests</h1>
          <p style={{ color:'#64748b' }}>{isAdmin ? 'Review and approve cross-NGO volunteer pool requests.' : 'Request volunteers from other NGOs or the global pool.'}</p>
        </div>
        {!isAdmin && (
          <button onClick={() => setShowForm(true)} style={{ padding:'0.6rem 1.25rem', borderRadius:'10px', border:'none', background:'#a855f7', color:'#fff', cursor:'pointer', fontWeight:600 }}>+ New Pool Request</button>
        )}
      </div>

      {msg && <div style={{ padding:'0.875rem', borderRadius:'10px', marginBottom:'1rem', background:msg.includes('fail')?'rgba(239,68,68,0.1)':'rgba(16,185,129,0.1)', border:`1px solid ${msg.includes('fail')?'#ef4444':'#10b981'}44`, color:msg.includes('fail')?'#f87171':'#6ee7b7', fontSize:'0.9rem' }}>{msg}</div>}

      <div style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
        {list.length === 0 && (
          <div style={{ background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.08)', borderRadius:'16px', padding:'3rem', textAlign:'center', color:'#475569' }}>
            {isAdmin ? 'No pool requests to review.' : 'No pool requests submitted yet.'}
          </div>
        )}
        {list.map(r => (
          <div key={r.id} style={{ background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.08)', borderRadius:'16px', padding:'1.5rem' }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:'0.75rem' }}>
              <div style={{ flex:1 }}>
                <div style={{ display:'flex', alignItems:'center', gap:'0.75rem', marginBottom:'0.5rem' }}>
                  <span style={{ fontWeight:700 }}>Request #{r.id}</span>
                  <span style={{ padding:'0.2rem 0.6rem', borderRadius:'999px', fontSize:'0.7rem', fontWeight:600, background:`${REQ_COLORS[r.status]}22`, color:REQ_COLORS[r.status], border:`1px solid ${REQ_COLORS[r.status]}44` }}>{r.status}</span>
                </div>
                <p style={{ color:'#94a3b8', fontSize:'0.9rem', margin:'0 0 0.75rem' }}>{r.reason}</p>
                <div style={{ display:'flex', gap:'1.5rem', flexWrap:'wrap' }}>
                  <Stat label="Volunteers Needed" value={r.volunteers_needed} />
                  <Stat label="Duration" value={`${r.duration_days} days`} />
                  {r.source_ngo_id && <Stat label="From NGO" value={`#${r.source_ngo_id}`} />}
                  {r.required_skills?.length > 0 && <Stat label="Skills" value={r.required_skills.join(', ')} />}
                </div>
                {r.assigned_volunteer_ids?.length > 0 && (
                  <div style={{ marginTop:'0.75rem', padding:'0.5rem 0.875rem', borderRadius:'8px', background:'rgba(16,185,129,0.1)', border:'1px solid #10b98122', fontSize:'0.85rem', color:'#6ee7b7' }}>
                    ✅ Assigned Volunteers: {r.assigned_volunteer_ids.join(', ')}
                  </div>
                )}
                {r.admin_notes && <div style={{ marginTop:'0.5rem', fontSize:'0.85rem', color:'#64748b' }}>📝 {r.admin_notes}</div>}
              </div>
              {isAdmin && r.status === 'pending' && (
                <div style={{ display:'flex', gap:'0.5rem' }}>
                  <button onClick={() => setApproveModal(r)} style={{ padding:'0.4rem 0.875rem', borderRadius:'6px', border:'1px solid #10b98144', background:'#10b98111', color:'#10b981', cursor:'pointer', fontWeight:600, fontSize:'0.85rem' }}>Approve</button>
                  <button onClick={() => handleReject(r.id)} style={{ padding:'0.4rem 0.875rem', borderRadius:'6px', border:'1px solid #ef444444', background:'#ef444411', color:'#ef4444', cursor:'pointer', fontWeight:600, fontSize:'0.85rem' }}>Reject</button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* New Request Modal */}
      {showForm && (
        <Modal onClose={() => setShowForm(false)} title="Request Volunteer Pool">
          <form onSubmit={handleSubmit} style={{ display:'flex', flexDirection:'column', gap:'0.875rem' }}>
            <FRow label="Source NGO ID (leave blank for global pool)"><input type="number" value={form.source_ngo_id} onChange={e=>setForm({...form,source_ngo_id:e.target.value})} style={inS} placeholder="Optional — NGO to borrow from" /></FRow>
            <FRow label="Skills Required (comma-separated)"><input value={form.required_skills} onChange={e=>setForm({...form,required_skills:e.target.value})} style={inS} placeholder="medical, logistics, first_aid" /></FRow>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0.75rem' }}>
              <FRow label="Volunteers Needed"><input type="number" value={form.volunteers_needed} onChange={e=>setForm({...form,volunteers_needed:e.target.value})} min={1} required style={inS} /></FRow>
              <FRow label="Duration (days)"><input type="number" value={form.duration_days} onChange={e=>setForm({...form,duration_days:e.target.value})} min={1} max={90} required style={inS} /></FRow>
            </div>
            <FRow label="Reason *"><textarea value={form.reason} onChange={e=>setForm({...form,reason:e.target.value})} required rows={3} style={{...inS, resize:'vertical'}} placeholder="Why you need these volunteers..." /></FRow>
            <button type="submit" disabled={loading} style={{ padding:'0.75rem', borderRadius:'10px', border:'none', background:'#a855f7', color:'#fff', cursor:'pointer', fontWeight:700 }}>{loading ? 'Submitting...' : 'Submit Request'}</button>
          </form>
        </Modal>
      )}

      {/* Approve Modal */}
      {approveModal && (
        <Modal onClose={() => setApproveModal(null)} title={`Approve Pool Request #${approveModal.id}`}>
          <p style={{ color:'#94a3b8', fontSize:'0.9rem', marginBottom:'1rem' }}>Assign volunteers to NGO #{approveModal.requesting_ngo_id}. They need <strong>{approveModal.volunteers_needed}</strong> volunteer(s).</p>
          <form onSubmit={handleApprove} style={{ display:'flex', flexDirection:'column', gap:'0.875rem' }}>
            <FRow label="Volunteer IDs (comma-separated) *"><input value={approveForm.volunteer_ids} onChange={e=>setApproveForm({...approveForm,volunteer_ids:e.target.value})} required style={inS} placeholder="e.g. 3, 7, 12" /></FRow>
            <FRow label="Admin Notes"><input value={approveForm.admin_notes} onChange={e=>setApproveForm({...approveForm,admin_notes:e.target.value})} style={inS} /></FRow>
            <button type="submit" disabled={loading} style={{ padding:'0.75rem', borderRadius:'10px', border:'none', background:'#10b981', color:'#fff', cursor:'pointer', fontWeight:700 }}>{loading ? 'Approving...' : 'Approve & Assign'}</button>
          </form>
        </Modal>
      )}
    </div>
  );
}

const inS = { width:'100%', padding:'0.6rem 0.875rem', borderRadius:'8px', border:'1px solid rgba(255,255,255,0.1)', background:'rgba(255,255,255,0.05)', color:'#f1f5f9', fontSize:'0.9rem', boxSizing:'border-box', outline:'none' };
function Stat({ label, value }) { return <div><span style={{ color:'#64748b', fontSize:'0.75rem' }}>{label}: </span><span style={{ fontWeight:600, fontSize:'0.875rem' }}>{value}</span></div>; }
function FRow({ label, children }) { return <div><label style={{ display:'block', fontSize:'0.8rem', color:'#94a3b8', marginBottom:'0.4rem', fontWeight:500 }}>{label}</label>{children}</div>; }
function Modal({ children, onClose, title }) {
  return (
    <div style={{ position:'fixed', inset:0, zIndex:50, display:'flex', alignItems:'center', justifyContent:'center', background:'rgba(0,0,0,0.6)', backdropFilter:'blur(6px)' }} onClick={e => e.target===e.currentTarget && onClose()}>
      <div style={{ background:'#1e1b4b', border:'1px solid rgba(255,255,255,0.1)', borderRadius:'16px', padding:'2rem', width:'460px', maxWidth:'95vw', maxHeight:'90vh', overflowY:'auto' }}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'1.5rem' }}>
          <h3 style={{ fontWeight:700, margin:0 }}>{title}</h3>
          <button onClick={onClose} style={{ background:'none', border:'none', color:'#64748b', cursor:'pointer', fontSize:'1.2rem' }}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}
