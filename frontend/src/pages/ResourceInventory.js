/**
 * ResourceInventory.js
 * Admin: manage global inventory (name-based search for assign), see NGO contributions.
 * NGO: view inventory summary, submit requests (with task linkage), contribute items.
 */
import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { Plus, Search, Check, X, Package, ArrowUpCircle, ChevronDown } from 'lucide-react';

const ROLE = () => localStorage.getItem('role');
const RTColors = { food:'#10b981', water:'#3b82f6', medical:'#ef4444', shelter:'#f59e0b', equipment:'#8b5cf6', transport:'#06b6d4', clothing:'#ec4899', money:'#84cc16', others:'#64748b' };
const badge = (color, text) => (
  <span style={{ padding:'0.2rem 0.6rem', borderRadius:'999px', background:color+'18', color, fontSize:'0.72rem', fontWeight:700 }}>{text}</span>
);

export default function ResourceInventory() {
  const isAdmin = ROLE() === 'admin';

  // ── State ──────────────────────────────────────────────────────
  const [inventory, setInventory]         = useState([]);
  const [contributions, setContributions] = useState([]);
  const [myRequests, setMyRequests]       = useState([]);
  const [myContribs, setMyContribs]       = useState([]);
  const [assignedNeeds, setAssignedNeeds] = useState([]); // for task linkage
  const [tab, setTab]                     = useState(isAdmin ? 'inventory' : 'requests');
  const [loading, setLoading]             = useState(true);
  const [search, setSearch]               = useState('');

  // Add inventory item (admin)
  const [addModal, setAddModal]   = useState(false);
  const [addForm, setAddForm]     = useState({ name:'', resource_type:'food', quantity:'', unit:'units' });

  // Resource request (NGO)
  const [reqModal, setReqModal]   = useState(false);
  const [reqForm, setReqForm]     = useState({ resource_type:'food', quantity:'', unit:'units', reason:'', urgency:'medium', need_id:'' });

  // Contribute (NGO)
  const [ctbModal, setCtbModal]   = useState(false);
  const [ctbForm, setCtbForm]     = useState({ resource_type:'food', name:'', quantity:'', unit:'units', notes:'' });

  const [saving, setSaving]       = useState(false);

  // ── Fetch ───────────────────────────────────────────────────────
  const load = useCallback(async () => {
    setLoading(true);
    try {
      if (isAdmin) {
        const [inv, ctb] = await Promise.all([
          api.get('/api/resource'),
          api.get('/api/resource/contributions?status=pending'),
        ]);
        setInventory(inv.data);
        setContributions(ctb.data);
      } else {
        const [inv, reqs, ctbs, needs] = await Promise.all([
          api.get('/api/resource').catch(() => ({ data:[] })),
          api.get('/api/resource/my-requests').catch(() => ({ data:[] })),
          api.get('/api/resource/my-contributions').catch(() => ({ data:[] })),
          api.get('/api/ngo/needs/assigned').catch(() => ({ data:[] })),
        ]);
        setInventory(inv.data);
        setMyRequests(reqs.data);
        setMyContribs(ctbs.data);
        setAssignedNeeds(needs.data.filter(n => n.ngo_assignment_status === 'accepted'));
      }
    } catch(e) { console.error(e); }
    setLoading(false);
  }, [isAdmin]);

  useEffect(() => { load(); }, [load]);

  // ── Admin: add inventory ────────────────────────────────────────
  const handleAdd = async e => {
    e.preventDefault(); setSaving(true);
    try {
      await api.post('/api/resource', { ...addForm, quantity: parseFloat(addForm.quantity) });
      setAddModal(false); setAddForm({ name:'', resource_type:'food', quantity:'', unit:'units' });
      load();
    } catch(err) { alert(err.response?.data?.detail || 'Failed'); }
    setSaving(false);
  };

  // ── Admin: approve/reject contribution ─────────────────────────
  const handleContribAction = async (id, action) => {
    try {
      await api.post(`/api/resource/contributions/${id}/${action}`, { admin_notes: null });
      load();
    } catch(err) { alert(err.response?.data?.detail || 'Failed'); }
  };

  // ── NGO: submit request ─────────────────────────────────────────
  const handleRequest = async e => {
    e.preventDefault(); setSaving(true);
    try {
      const need = assignedNeeds.find(n => String(n.id) === String(reqForm.need_id));
      await api.post('/api/resource/request', {
        resource_type: reqForm.resource_type,
        quantity_requested: parseFloat(reqForm.quantity),
        unit: reqForm.unit,
        reason: reqForm.reason,
        urgency: reqForm.urgency,
        need_id: reqForm.need_id ? parseInt(reqForm.need_id) : null,
        need_description: need ? need.category : null,
      });
      setReqModal(false); setReqForm({ resource_type:'food', quantity:'', unit:'units', reason:'', urgency:'medium', need_id:'' });
      load();
    } catch(err) { alert(err.response?.data?.detail || 'Failed'); }
    setSaving(false);
  };

  // ── NGO: contribute ─────────────────────────────────────────────
  const handleContribute = async e => {
    e.preventDefault(); setSaving(true);
    try {
      await api.post('/api/resource/contribute', { ...ctbForm, quantity: parseFloat(ctbForm.quantity) });
      setCtbModal(false); setCtbForm({ resource_type:'food', name:'', quantity:'', unit:'units', notes:'' });
      load();
    } catch(err) { alert(err.response?.data?.detail || 'Failed'); }
    setSaving(false);
  };

  const filteredInv = inventory.filter(i =>
    (i.name || '').toLowerCase().includes(search.toLowerCase()) ||
    (i.resource_type || '').toLowerCase().includes(search.toLowerCase())
  );

  const TABS_ADMIN = [['inventory','📦 Inventory'], ['contributions','🔔 Contributions']];
  const TABS_NGO   = [['requests','📤 My Requests'], ['inventory','📦 Inventory'], ['contributions','🤝 My Contributions']];
  const TABS = isAdmin ? TABS_ADMIN : TABS_NGO;

  return (
    <div style={{ color:'#1e293b', fontFamily:'Inter, sans-serif' }}>
      {/* Header */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'1.5rem', flexWrap:'wrap', gap:'1rem' }}>
        <div>
          <h1 style={{ fontWeight:800, fontSize:'1.6rem', color:'#0f172a', marginBottom:'0.2rem' }}>📦 Resource Inventory</h1>
          <p style={{ color:'#64748b', fontSize:'0.875rem' }}>{isAdmin ? `${inventory.length} items · ${contributions.length} pending contributions` : 'Global inventory & your NGO resource requests'}</p>
        </div>
        <div style={{ display:'flex', gap:'0.5rem' }}>
          {isAdmin && (
            <button onClick={() => setAddModal(true)} style={primaryBtn('#10b981')}>
              <Plus size={15} /> Add Item
            </button>
          )}
          {!isAdmin && (
            <>
              <button onClick={() => setReqModal(true)} style={primaryBtn('#3b82f6')}><Package size={15} /> Request Resource</button>
              <button onClick={() => setCtbModal(true)} style={primaryBtn('#8b5cf6')}><ArrowUpCircle size={15} /> Contribute</button>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display:'flex', gap:'0.5rem', borderBottom:'1px solid #e2e8f0', marginBottom:'1.5rem' }}>
        {TABS.map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)}
            style={{ padding:'0.6rem 1.1rem', border:'none', borderBottom:`2px solid ${tab===key ? '#6366f1':'transparent'}`, background:'none', color:tab===key ? '#6366f1':'#64748b', fontWeight:600, fontSize:'0.85rem', cursor:'pointer', fontFamily:'inherit', position:'relative', bottom:'-1px' }}>
            {label}
          </button>
        ))}
      </div>

      {loading && <p style={{ color:'#94a3b8', textAlign:'center', padding:'3rem' }}>Loading…</p>}

      {/* ── Inventory tab ── */}
      {!loading && tab === 'inventory' && (
        <>
          <div style={{ position:'relative', marginBottom:'1rem', maxWidth:'320px' }}>
            <Search style={{ position:'absolute', left:'0.75rem', top:'50%', transform:'translateY(-50%)', color:'#94a3b8' }} size={15} />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search inventory…" style={{ paddingLeft:'2.25rem', paddingRight:'1rem', paddingTop:'0.55rem', paddingBottom:'0.55rem', border:'1.5px solid #e2e8f0', borderRadius:'10px', fontFamily:'inherit', fontSize:'0.875rem', outline:'none', width:'100%' }} />
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(220px,1fr))', gap:'1rem' }}>
            {filteredInv.map(item => {
              const color = RTColors[item.resource_type] || '#64748b';
              const pct = Math.min(100, (item.quantity / (item.initial_quantity || Math.max(item.quantity, 1))) * 100);
              return (
                <div key={item.id} style={{ background:'#fff', border:'1.5px solid #f1f5f9', borderRadius:'14px', padding:'1.25rem', boxShadow:'0 2px 6px rgba(0,0,0,0.04)' }}>
                  <div style={{ display:'flex', justifyContent:'space-between', marginBottom:'0.75rem' }}>
                    <span style={{ fontSize:'1.5rem' }}>{{'food':'🍚','water':'💧','medical':'💊','shelter':'🏠','equipment':'🔧','transport':'🚛','clothing':'👗','money':'💰'}[item.resource_type] || '📦'}</span>
                    {badge(color, item.resource_type)}
                  </div>
                  <div style={{ fontWeight:700, fontSize:'0.95rem', marginBottom:'0.25rem' }}>{item.name}</div>
                  <div style={{ fontSize:'1.5rem', fontWeight:800, color }}>{item.quantity} <span style={{ fontSize:'0.8rem', color:'#94a3b8', fontWeight:400 }}>{item.unit}</span></div>
                  <div style={{ marginTop:'0.625rem', height:'6px', borderRadius:'999px', background:'#f1f5f9' }}>
                    <div style={{ height:'100%', width:`${pct}%`, background:color, borderRadius:'999px', transition:'width 0.5s' }} />
                  </div>
                  <div style={{ fontSize:'0.7rem', color:'#94a3b8', marginTop:'0.3rem' }}>
                    {item.status === 'depleted' ? '🔴 Depleted' : item.quantity < 10 ? '🟡 Low stock' : '🟢 In stock'}
                  </div>
                </div>
              );
            })}
            {filteredInv.length === 0 && <p style={{ color:'#94a3b8', gridColumn:'1/-1', padding:'2rem 0', textAlign:'center' }}>No inventory items found.</p>}
          </div>
        </>
      )}

      {/* ── NGO: My Requests tab ── */}
      {!loading && tab === 'requests' && (
        <div style={{ display:'flex', flexDirection:'column', gap:'0.75rem' }}>
          {myRequests.length === 0 && <p style={{ color:'#94a3b8', textAlign:'center', padding:'3rem' }}>No requests yet.</p>}
          {myRequests.map(r => (
            <div key={r.id} style={{ background:'#fff', border:'1.5px solid #f1f5f9', borderRadius:'12px', padding:'1rem 1.25rem', display:'flex', alignItems:'center', justifyContent:'space-between', flexWrap:'wrap', gap:'0.5rem' }}>
              <div>
                <span style={{ fontWeight:700, fontSize:'0.9rem' }}>{r.resource_type} — {r.quantity_requested} {r.unit}</span>
                {r.need_description && <span style={{ marginLeft:'0.5rem', fontSize:'0.75rem', color:'#6366f1', fontWeight:500 }}>for: {r.need_description}</span>}
                <p style={{ margin:'0.2rem 0 0', color:'#64748b', fontSize:'0.78rem' }}>{r.reason}</p>
              </div>
              <div style={{ display:'flex', flexDirection:'column', alignItems:'flex-end', gap:'0.25rem' }}>
                {badge(r.status==='approved' ? '#10b981' : r.status==='rejected' ? '#ef4444' : '#f59e0b', r.status.toUpperCase())}
                {r.quantity_allocated && <span style={{ fontSize:'0.72rem', color:'#64748b' }}>Allocated: {r.quantity_allocated} {r.unit}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Admin: Pending Contributions tab ── */}
      {/* ── NGO: My Contributions tab ── */}
      {!loading && tab === 'contributions' && (
        <div style={{ display:'flex', flexDirection:'column', gap:'0.75rem' }}>
          {(isAdmin ? contributions : myContribs).length === 0 && <p style={{ color:'#94a3b8', textAlign:'center', padding:'3rem' }}>{isAdmin ? 'No pending contributions.' : 'No contributions submitted yet.'}</p>}
          {(isAdmin ? contributions : myContribs).map(c => (
            <div key={c.id} style={{ background:'#fff', border:'1.5px solid #f1f5f9', borderRadius:'12px', padding:'1rem 1.25rem', display:'flex', alignItems:'center', justifyContent:'space-between', flexWrap:'wrap', gap:'0.5rem' }}>
              <div>
                <span style={{ fontWeight:700, fontSize:'0.9rem' }}>{c.name} — {c.quantity} {c.unit}</span>
                {isAdmin && <span style={{ marginLeft:'0.5rem', fontSize:'0.75rem', color:'#94a3b8' }}>from {c.ngo_name}</span>}
                {c.notes && <p style={{ margin:'0.2rem 0 0', color:'#64748b', fontSize:'0.78rem' }}>{c.notes}</p>}
              </div>
              <div style={{ display:'flex', alignItems:'center', gap:'0.5rem' }}>
                {badge(c.status==='approved' ? '#10b981' : c.status==='rejected' ? '#ef4444' : '#f59e0b', c.status.toUpperCase())}
                {isAdmin && c.status === 'pending' && (
                  <>
                    <button onClick={() => handleContribAction(c.id, 'approve')} style={{ ...actionBtn('#10b981') }}><Check size={13} /> Approve</button>
                    <button onClick={() => handleContribAction(c.id, 'reject')}  style={{ ...actionBtn('#ef4444') }}><X size={13} /> Reject</button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Admin: Add Item modal ── */}
      {addModal && (
        <div style={overlay} onClick={() => setAddModal(false)}>
          <div style={modalCard} onClick={e => e.stopPropagation()}>
            <h3 style={mHead}>Add Inventory Item</h3>
            <form onSubmit={handleAdd} style={{ display:'flex', flexDirection:'column', gap:'0.875rem' }}>
              {fld('Name', 'text', addForm.name, v => setAddForm({...addForm, name:v}), 'e.g. Rice Bags', true)}
              <div>
                <label style={lbl}>Type</label>
                <select value={addForm.resource_type} onChange={e => setAddForm({...addForm, resource_type:e.target.value})} style={sel}>
                  {Object.keys(RTColors).map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              {fld('Quantity', 'number', addForm.quantity, v => setAddForm({...addForm, quantity:v}), '0', true)}
              {fld('Unit', 'text', addForm.unit, v => setAddForm({...addForm, unit:v}), 'units')}
              <div style={{ display:'flex', gap:'0.5rem', justifyContent:'flex-end', marginTop:'0.5rem' }}>
                <button type="button" onClick={()=>setAddModal(false)} style={cancelB}>Cancel</button>
                <button type="submit" disabled={saving} style={submitB('#10b981')}>{saving?'Saving…':'Add Item'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── NGO: Request modal ── */}
      {reqModal && (
        <div style={overlay} onClick={() => setReqModal(false)}>
          <div style={modalCard} onClick={e => e.stopPropagation()}>
            <h3 style={mHead}>Request Resource from Admin</h3>
            <form onSubmit={handleRequest} style={{ display:'flex', flexDirection:'column', gap:'0.875rem' }}>
              <div>
                <label style={lbl}>Resource Type</label>
                <select value={reqForm.resource_type} onChange={e => setReqForm({...reqForm, resource_type:e.target.value})} style={sel}>
                  {Object.keys(RTColors).map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              {fld('Quantity', 'number', reqForm.quantity, v => setReqForm({...reqForm, quantity:v}), '0', true)}
              {fld('Unit', 'text', reqForm.unit, v => setReqForm({...reqForm, unit:v}), 'units')}
              <div>
                <label style={lbl}>Urgency</label>
                <select value={reqForm.urgency} onChange={e => setReqForm({...reqForm, urgency:e.target.value})} style={sel}>
                  {['low','medium','high'].map(u=><option key={u} value={u}>{u}</option>)}
                </select>
              </div>
              {fld('Reason *', 'text', reqForm.reason, v => setReqForm({...reqForm, reason:v}), 'Why do you need this?', true)}
              <div>
                <label style={lbl}>For Task (optional)</label>
                <select value={reqForm.need_id} onChange={e => setReqForm({...reqForm, need_id:e.target.value})} style={sel}>
                  <option value="">— No specific task —</option>
                  {assignedNeeds.map(n => <option key={n.id} value={n.id}>#{n.id} · {n.category} ({n.location || 'N/A'})</option>)}
                </select>
              </div>
              <div style={{ display:'flex', gap:'0.5rem', justifyContent:'flex-end', marginTop:'0.5rem' }}>
                <button type="button" onClick={()=>setReqModal(false)} style={cancelB}>Cancel</button>
                <button type="submit" disabled={saving} style={submitB('#3b82f6')}>{saving?'Submitting…':'Submit Request'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── NGO: Contribute modal ── */}
      {ctbModal && (
        <div style={overlay} onClick={() => setCtbModal(false)}>
          <div style={modalCard} onClick={e => e.stopPropagation()}>
            <h3 style={mHead}>Contribute to Global Inventory</h3>
            <p style={{ fontSize:'0.82rem', color:'#64748b', marginBottom:'1rem' }}>Suggest items to donate. Admin will review and merge into inventory.</p>
            <form onSubmit={handleContribute} style={{ display:'flex', flexDirection:'column', gap:'0.875rem' }}>
              <div>
                <label style={lbl}>Type</label>
                <select value={ctbForm.resource_type} onChange={e => setCtbForm({...ctbForm, resource_type:e.target.value})} style={sel}>
                  {Object.keys(RTColors).map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              {fld('Item Name *', 'text', ctbForm.name, v => setCtbForm({...ctbForm, name:v}), 'Must match existing item name to merge', true)}
              {fld('Quantity *', 'number', ctbForm.quantity, v => setCtbForm({...ctbForm, quantity:v}), '0', true)}
              {fld('Unit', 'text', ctbForm.unit, v => setCtbForm({...ctbForm, unit:v}), 'units')}
              {fld('Notes', 'text', ctbForm.notes, v => setCtbForm({...ctbForm, notes:v}), 'Optional details')}
              <div style={{ display:'flex', gap:'0.5rem', justifyContent:'flex-end', marginTop:'0.5rem' }}>
                <button type="button" onClick={()=>setCtbModal(false)} style={cancelB}>Cancel</button>
                <button type="submit" disabled={saving} style={submitB('#8b5cf6')}>{saving?'Submitting…':'Submit Contribution'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Style helpers ───────────────────────────────────────────────────────────
const lbl     = { display:'block', fontSize:'0.78rem', fontWeight:600, color:'#475569', marginBottom:'0.35rem' };
const inp     = { width:'100%', padding:'0.6rem 0.875rem', border:'1.5px solid #e2e8f0', borderRadius:'8px', fontSize:'0.875rem', fontFamily:'inherit', outline:'none', boxSizing:'border-box' };
const sel     = { width:'100%', padding:'0.6rem 0.875rem', border:'1.5px solid #e2e8f0', borderRadius:'8px', fontSize:'0.875rem', fontFamily:'inherit', outline:'none', boxSizing:'border-box', cursor:'pointer' };
const overlay = { position:'fixed', inset:0, background:'rgba(15,23,42,0.4)', zIndex:300, display:'flex', alignItems:'center', justifyContent:'center', padding:'1rem', backdropFilter:'blur(4px)' };
const modalCard = { background:'#fff', borderRadius:'20px', padding:'1.75rem', width:'100%', maxWidth:'440px', boxShadow:'0 20px 60px rgba(0,0,0,0.15)' };
const mHead   = { fontWeight:800, fontSize:'1.1rem', color:'#0f172a', marginBottom:'1.25rem', marginTop:0 };
const cancelB = { padding:'0.6rem 1.1rem', border:'1.5px solid #e2e8f0', background:'#fff', borderRadius:'10px', fontWeight:600, fontSize:'0.85rem', cursor:'pointer', fontFamily:'inherit', color:'#64748b' };
const submitB = color => ({ padding:'0.6rem 1.25rem', border:'none', background:color, borderRadius:'10px', fontWeight:700, fontSize:'0.85rem', cursor:'pointer', fontFamily:'inherit', color:'#fff' });
const primaryBtn = color => ({ display:'inline-flex', alignItems:'center', gap:'0.4rem', padding:'0.6rem 1.1rem', border:'none', background:color, color:'#fff', borderRadius:'10px', fontWeight:600, fontSize:'0.85rem', cursor:'pointer', fontFamily:'inherit' });
const actionBtn  = color => ({ display:'inline-flex', alignItems:'center', gap:'0.3rem', padding:'0.3rem 0.65rem', border:'none', background:color+'18', color, borderRadius:'6px', fontWeight:600, fontSize:'0.72rem', cursor:'pointer', fontFamily:'inherit' });
const fld = (label, type, value, onChange, placeholder, required) => (
  <div>
    <label style={lbl}>{label}</label>
    <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} required={required} style={inp} />
  </div>
);
