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
  const [lendingRequests, setLendingRequests] = useState([]);
  const [allVolunteers, setAllVolunteers] = useState([]); // Raw list
  const [tab, setTab] = useState(isAdmin ? 'all' : 'my'); // 'all', 'my', 'lending'
  const [assignedNeeds, setAssignedNeeds] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [approveModal, setApproveModal] = useState(null);
  const [selectedVolIds, setSelectedVolIds] = useState([]);
  const [form, setForm] = useState({ need_id:'', required_skills:'', volunteers_needed:1, reason:'', duration_days:7 });
  const [approveForm, setApproveForm] = useState({ admin_notes:'' });
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (isAdmin) {
        const [reqs, vols] = await Promise.all([
          axios.get(`${API}/api/pool/requests`, auth()),
          axios.get(`${API}/api/volunteers`, auth()) // Need list for selection
        ]);
        setRequests(reqs.data);
        setAllVolunteers(vols.data || []);
      } else {
        const [my, lending, needs] = await Promise.all([
          axios.get(`${API}/api/pool/my-requests`, auth()),
          axios.get(`${API}/api/pool/lending-requests`, auth()),
          axios.get(`${API}/api/ngo/needs/assigned`, auth())
        ]);
        setMyRequests(my.data);
        setLendingRequests(lending.data);
        setAssignedNeeds((needs.data || []).filter(n => n.ngo_assignment_status === 'accepted'));
      }
    } catch(e) {}
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const handleSubmit = async e => {
    e.preventDefault(); setLoading(true); setMsg('');
    try {
      await axios.post(`${API}/api/pool/request`, {
        need_id: form.need_id ? parseInt(form.need_id) : null,
        required_skills: form.required_skills ? form.required_skills.split(',').map(s=>s.trim()).filter(Boolean) : [],
        volunteers_needed: parseInt(form.volunteers_needed),
        reason: form.reason,
        duration_days: parseInt(form.duration_days),
      }, auth());
      setMsg('Pool request submitted!');
      setShowForm(false);
      setForm({ need_id:'', required_skills:'', volunteers_needed:1, reason:'', duration_days:7 });
      fetchData();
    } catch(e) { setMsg(e.response?.data?.detail || 'Request failed'); }
    finally { setLoading(false); }
  };

  const handleApprove = async e => {
    e.preventDefault(); setLoading(true);
    try {
      if (selectedVolIds.length === 0) {
        setMsg('Please select at least one volunteer');
        setLoading(false); return;
      }
      await axios.post(`${API}/api/pool/request/${approveModal.id}/approve`, { 
        volunteer_ids: selectedVolIds, 
        admin_notes: approveForm.admin_notes 
      }, auth());
      setMsg('Selection sent to lending NGOs!'); setApproveModal(null); setSelectedVolIds([]); fetchData();
    } catch(e) { setMsg(e.response?.data?.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  const handleLendingAction = async (id, action) => {
    try {
      await axios.post(`${API}/api/pool/assignment/${id}/${action}`, {}, auth());
      setMsg(`Lending ${action === 'approve' ? 'approved' : 'rejected'}`);
      fetchData();
    } catch(e) { setMsg(e.response?.data?.detail || 'Action failed'); }
  };

  const handleReject = async (id) => {
    await axios.post(`${API}/api/pool/request/${id}/reject`, { admin_notes:'Rejected by admin' }, auth()).catch(()=>{});
    fetchData();
  };

  const list = isAdmin ? requests : myRequests;

  return (
    <div style={{ color:'#f1f5f9', fontFamily:'Inter, sans-serif' }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:'2rem', flexWrap:'wrap', gap:'1rem' }}>
        <div>
          <h1 style={{ fontSize:'1.75rem', fontWeight:800, marginBottom:'0.25rem' }}>🤝 Volunteer Pool Requests</h1>
          <p style={{ color:'#64748b' }}>{isAdmin ? 'Review and approve cross-NGO volunteer pool requests.' : 'Request volunteers from the global pool to help with your tasks.'}</p>
        </div>
        {!isAdmin && (
          <button onClick={() => setShowForm(true)} style={{ padding:'0.6rem 1.25rem', borderRadius:'10px', border:'none', background:'#a855f7', color:'#fff', cursor:'pointer', fontWeight:600 }}>+ New Pool Request</button>
        )}
      </div>

      {msg && <div style={{ padding:'0.875rem', borderRadius:'10px', marginBottom:'1rem', background:msg.toLowerCase().includes('fail')||msg.toLowerCase().includes('error')?'rgba(239,68,68,0.1)':'rgba(16,185,129,0.1)', border:`1px solid ${msg.toLowerCase().includes('fail')||msg.toLowerCase().includes('error')?'#ef4444':'#10b981'}44`, color:msg.toLowerCase().includes('fail')||msg.toLowerCase().includes('error')?'#f87171':'#6ee7b7', fontSize:'0.9rem' }}>{msg}</div>}

      {!isAdmin && (
        <div style={{ display:'flex', gap:'1rem', borderBottom:'1px solid rgba(255,255,255,0.05)', marginBottom:'1.5rem' }}>
          <TabBtn active={tab==='my'} onClick={()=>setTab('my')}>My Borrow Requests</TabBtn>
          <TabBtn active={tab==='lending'} onClick={()=>setTab('lending')}>
            Lending Requests {lendingRequests.length > 0 && <span style={dot}>{lendingRequests.length}</span>}
          </TabBtn>
        </div>
      )}

      <div style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
        {tab === 'lending' && lendingRequests.map(a => (
          <div key={a.assignment_id} style={{ background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.08)', borderRadius:'16px', padding:'1.5rem' }}>
             <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <div>
                   <p style={{ margin:0, fontWeight:700 }}>{a.volunteer_name} <span style={{color:'#64748b', fontWeight:400}}>requested by</span> {a.borrower_name}</p>
                   <p style={{ margin:'0.25rem 0 0', fontSize:'0.85rem', color:'#94a3b8' }}>Reason: {a.reason}</p>
                   <p style={{ margin:'0.25rem 0 0', fontSize:'0.75rem', color:'#6366f1' }}>Expires: {new Date(a.ends_at).toLocaleDateString()}</p>
                </div>
                <div style={{ display:'flex', gap:'0.5rem' }}>
                   <button onClick={()=>handleLendingAction(a.assignment_id, 'approve')} style={actionBtn('#10b981')}>Approve</button>
                   <button onClick={()=>handleLendingAction(a.assignment_id, 'reject')} style={actionBtn('#ef4444')}>Reject</button>
                </div>
             </div>
          </div>
        ))}

        {tab !== 'lending' && (isAdmin ? requests : myRequests).length === 0 && (
          <div style={{ background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.08)', borderRadius:'16px', padding:'3rem', textAlign:'center', color:'#475569' }}>
            {isAdmin ? 'No pool requests to review.' : 'No pool requests submitted yet.'}
          </div>
        )}
        
        {tab !== 'lending' && (isAdmin ? requests : myRequests).map(r => (
          <div key={r.id} style={{ background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.08)', borderRadius:'16px', padding:'1.5rem' }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:'0.75rem' }}>
              <div style={{ flex:1 }}>
                <div style={{ display:'flex', alignItems:'center', gap:'0.75rem', marginBottom:'0.5rem', flexWrap:'wrap' }}>
                  <span style={{ fontWeight:700 }}>Request #{r.id}</span>
                  <span style={{ padding:'0.2rem 0.6rem', borderRadius:'999px', fontSize:'0.7rem', fontWeight:600, background:`${REQ_COLORS[r.status] || '#64748b'}22`, color:REQ_COLORS[r.status] || '#64748b', border:`1px solid ${REQ_COLORS[r.status] || '#64748b'}44` }}>
                    {(r.status || 'unknown').replace('_',' ').toUpperCase()}
                  </span>
                  {r.need_id && (
                    <span style={{ padding:'0.2rem 0.6rem', borderRadius:'999px', fontSize:'0.7rem', fontWeight:600, background:'#6366f122', color:'#818cf8', border:'1px solid #6366f144' }}>
                      📋 Task #{r.need_id}
                    </span>
                  )}
                </div>
                <p style={{ color:'#94a3b8', fontSize:'0.9rem', margin:'0 0 0.75rem' }}>{r.reason}</p>
                <div style={{ display:'flex', gap:'1.5rem', flexWrap:'wrap' }}>
                  <Stat label="Volunteers Needed" value={r.volunteers_needed} />
                  <Stat label="Duration" value={`${r.duration_days} days`} />
                  {r.required_skills?.length > 0 && <Stat label="Skills" value={r.required_skills.join(', ')} />}
                </div>
                {r.assigned_volunteer_ids?.length > 0 && (
                  <div style={{ marginTop:'0.75rem', padding:'0.5rem 0.875rem', borderRadius:'8px', background:'rgba(16,185,129,0.1)', border:'1px solid #10b98122', fontSize:'0.85rem', color:'#6ee7b7' }}>
                    {r.status === 'pending_lenders' 
                      ? `🕒 Pending NGO Approval (${r.assigned_volunteer_ids.length} approved so far)` 
                      : '✅ Assigned Volunteers IDs: ' + r.assigned_volunteer_ids.join(', ')}
                  </div>
                )}
                {r.admin_notes && <div style={{ marginTop:'0.5rem', fontSize:'0.85rem', color:'#64748b' }}>📝 Admin: {r.admin_notes}</div>}
              </div>
              {isAdmin && r.status === 'pending' && (
                <div style={{ display:'flex', gap:'0.5rem' }}>
                  <button onClick={() => { setApproveModal(r); fetchData(); }} style={{ padding:'0.4rem 0.875rem', borderRadius:'6px', border:'1px solid #10b98144', background:'#10b98111', color:'#10b981', cursor:'pointer', fontWeight:600, fontSize:'0.85rem' }}>Select & Approve</button>
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
            <FRow label="Link to Task (optional)">
              <select value={form.need_id} onChange={e=>setForm({...form,need_id:e.target.value})} style={inS}>
                <option value="">— No specific task —</option>
                {assignedNeeds.map(n => (
                  <option key={n.id} value={n.id}>#{n.id} · {n.category} ({n.location || 'N/A'})</option>
                ))}
              </select>
            </FRow>
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
      {approveModal && (() => {
        const filtered = allVolunteers.filter(v => 
          Boolean(v.availability) && 
          String(v.ngo_id || "") !== String(approveModal.requesting_ngo_id)
        );
        return (
        <Modal onClose={() => setApproveModal(null)} title={`Review Pool Request #${approveModal.id}`}>
          <p style={{ color:'#94a3b8', fontSize:'0.9rem', marginBottom:'1rem' }}>
            Select up to <strong>{approveModal.volunteers_needed}</strong> volunteer(s) to fulfill this request.
            <span style={{ fontSize:'0.7rem', display:'block', color:'#475569', marginTop:'0.25rem' }}>
              (Found {allVolunteers.length} total, {filtered.length} borrowable)
            </span>
          </p>
          <div style={{ maxHeight:'250px', overflowY:'auto', border:'1px solid rgba(255,255,255,0.1)', borderRadius:'8px', padding:'0.5rem', marginBottom:'1rem' }}>
            {filtered.length === 0 && <p style={{textAlign:'center', padding:'1rem', color:'#64748b'}}>No available volunteers found in other NGOs.</p>}
            {filtered.map(v => (
              <label key={v.id} style={{ display:'flex', alignItems:'center', gap:'0.75rem', padding:'0.6rem', borderRadius:'6px', cursor:'pointer', background:selectedVolIds.includes(v.id)?'rgba(16,185,129,0.1)':'transparent' }}>
                <input 
                  type="checkbox" 
                  checked={selectedVolIds.includes(v.id)} 
                  disabled={!selectedVolIds.includes(v.id) && selectedVolIds.length >= approveModal.volunteers_needed}
                  onChange={() => {
                    if (selectedVolIds.includes(v.id)) setSelectedVolIds(selectedVolIds.filter(id=>id!==v.id));
                    else setSelectedVolIds([...selectedVolIds, v.id]);
                  }}
                />
                <div style={{ flex:1 }}>
                  <p style={{ margin:0, fontWeight:600, fontSize:'0.9rem' }}>{v.name}</p>
                  <p style={{ margin:0, fontSize:'0.75rem', color:'#64748b' }}>NGO ID: {v.ngo_id} | Skills: {v.skills?.join(', ') || 'N/A'}</p>
                </div>
              </label>
            ))}
          </div>
          <form onSubmit={handleApprove} style={{ display:'flex', flexDirection:'column', gap:'0.875rem' }}>
            <FRow label="Admin Notes"><input value={approveForm.admin_notes} onChange={e=>setApproveForm({...approveForm,admin_notes:e.target.value})} style={inS} placeholder="e.g. Approved for emergency support" /></FRow>
            <button type="submit" disabled={loading || selectedVolIds.length === 0} style={{ padding:'0.75rem', borderRadius:'10px', border:'none', background:'#10b981', color:'#fff', cursor:'pointer', fontWeight:700 }}>
              {loading ? 'Processing...' : `Select ${selectedVolIds.length} & Notify NGOs`}
            </button>
          </form>
        </Modal>
        )})()}
    </div>
  );
}

const inS = { width:'100%', padding:'0.6rem 0.875rem', borderRadius:'8px', border:'1px solid rgba(255,255,255,0.1)', background:'rgba(255,255,255,0.05)', color:'#f1f5f9', fontSize:'0.9rem', boxSizing:'border-box', outline:'none' };
function Stat({ label, value }) { return <div><span style={{ color:'#64748b', fontSize:'0.75rem' }}>{label}: </span><span style={{ fontWeight:600, fontSize:'0.875rem', color:'#f1f5f9' }}>{value}</span></div>; }
function FRow({ label, children }) { return <div><label style={{ display:'block', fontSize:'0.8rem', color:'#94a3b8', marginBottom:'0.4rem', fontWeight:500 }}>{label}</label>{children}</div>; }
function TabBtn({ children, active, onClick }) { 
  return <button onClick={onClick} style={{ padding:'0.75rem 1.25rem', border:'none', background:'none', color:active?'#a855f7':'#64748b', cursor:'pointer', fontWeight:600, borderBottom:active?'2px solid #a855f7':'none', position:'relative' }}>{children}</button>; 
}
const dot = { background:'#ef4444', color:'#fff', fontSize:'0.65rem', padding:'0.1rem 0.35rem', borderRadius:'99px', marginLeft:'0.4rem', verticalAlign:'middle' };
const actionBtn = (c) => ({ padding:'0.4rem 0.875rem', borderRadius:'6px', border:`1px solid ${c}44`, background:`${c}11`, color:c, cursor:'pointer', fontWeight:600, fontSize:'0.85rem' });

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
