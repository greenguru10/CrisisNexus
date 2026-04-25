/**
 * ResourceInventory.js
 * Admin: manage global inventory (name-based search for assign), see NGO contributions.
 * NGO: view inventory summary, submit requests (with task linkage), contribute items.
 */
import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { Plus, Search, Check, X, Package, ArrowUpCircle } from 'lucide-react';

const ROLE = () => localStorage.getItem('role');

const RTColors = { 
  food: 'emerald', water: 'blue', medical: 'red', shelter: 'amber', 
  equipment: 'purple', transport: 'cyan', clothing: 'pink', money: 'lime', others: 'slate' 
};

const badge = (colorName, text) => (
  <span className={`px-2.5 py-1 rounded-full bg-${colorName}-100 text-${colorName}-600 text-xs font-bold uppercase tracking-wider`}>
    {text}
  </span>
);

export default function ResourceInventory() {
  const isAdmin = ROLE() === 'admin';

  // ── State ──────────────────────────────────────────────────────
  const [inventory, setInventory]         = useState([]);
  const [contributions, setContributions] = useState([]);
  const [myRequests, setMyRequests]       = useState([]);
  const [myContribs, setMyContribs]       = useState([]);
  const [assignedNeeds, setAssignedNeeds] = useState([]); // for task linkage
  const [ngoNames, setNgoNames]           = useState({});  // id → name map for admin
  const [tab, setTab]                     = useState(isAdmin ? 'inventory' : 'requests');
  const [loading, setLoading]             = useState(true);
  const [search, setSearch]               = useState('');

  // Add inventory item (admin)
  const [addModal, setAddModal]   = useState(false);
  const [addForm, setAddForm]     = useState({ name:'', resource_type:'food', quantity:'', unit:'units' });

  // Resource request (NGO)
  const [reqModal, setReqModal]   = useState(false);
  const [reqForm, setReqForm]     = useState({ resource_inventory_id: '', resource_type:'food', quantity:'', unit:'units', reason:'', urgency:'medium', need_id:'' });

  // Contribute (NGO)
  const [ctbModal, setCtbModal]   = useState(false);
  const [ctbForm, setCtbForm]     = useState({ resource_type:'food', name:'', quantity:'', unit:'units', notes:'' });

  const [saving, setSaving]       = useState(false);

  // ── Fetch ───────────────────────────────────────────────────────
  const load = useCallback(async () => {
    setLoading(true);
    try {
      if (isAdmin) {
        const [inv, ctb, reqs, ngos] = await Promise.all([
          api.get('/api/resource'),
          api.get('/api/resource/contributions?status=pending'),
          api.get('/api/resource/requests').catch(() => ({ data:[] })),
          api.get('/api/ngo/names').catch(() => ({ data:[] })),
        ]);
        setInventory(inv.data);
        setContributions(ctb.data);
        setMyRequests(reqs.data);
        const nameMap = {};
        (ngos.data || []).forEach(n => { nameMap[n.id] = n.name; });
        setNgoNames(nameMap);
      } else {
        const [inv, reqs, ctbs, needs] = await Promise.all([
          api.get('/api/resource').catch(() => ({ data:[] })),
          api.get('/api/resource/my-requests').catch(() => ({ data:[] })),
          api.get('/api/resource/my-contributions').catch(() => ({ data:[] })),
          api.get('/api/task/ngo/tasks').catch(() => ({ data:[] })),
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

  // ── Handlers ───────────────────────────────────────────────────
  const handleAdd = async e => {
    e.preventDefault(); setSaving(true);
    try {
      await api.post('/api/resource', { ...addForm, quantity: parseFloat(addForm.quantity) });
      setAddModal(false); setAddForm({ name:'', resource_type:'food', quantity:'', unit:'units' });
      load();
    } catch(err) { alert(err.response?.data?.detail || 'Failed'); }
    setSaving(false);
  };

  const handleRequestAction = async (id, action, inventoryId = null, quantity = null) => {
    try {
      if (action === 'approve') {
        if (!inventoryId) {
          alert("This request is missing a linked inventory item. Please reject it and ask the NGO to submit a new request using the updated inventory system.");
          return;
        }
        await api.post(`/api/resource/request/${id}/approve`, {
          resource_inventory_id: inventoryId,
          quantity_allocated: quantity,
          admin_notes: 'Automatically approved via inventory match'
        });
      } else {
        await api.post(`/api/resource/request/${id}/reject`, { admin_notes: 'Rejected by Admin' });
      }
      load();
    } catch(err) { 
      const detail = err.response?.data?.detail;
      alert(Array.isArray(detail) ? "Validation Error:\n" + detail.map(d => `- ${d.loc.slice(1).join(' ')}: ${d.msg}`).join('\n') : (detail || 'Operation failed'));
    }
  };

  const handleContribAction = async (id, action) => {
    try {
      await api.post(`/api/resource/contributions/${id}/${action}`, { admin_notes: null });
      load();
    } catch(err) { 
      const detail = err.response?.data?.detail;
      alert(Array.isArray(detail) ? "Validation Error:\n" + detail.map(d => `- ${d.loc.slice(1).join(' ')}: ${d.msg}`).join('\n') : (detail || 'Operation failed'));
    }
  };

  const handleRequest = async e => {
    e.preventDefault(); setSaving(true);
    try {
      const need = assignedNeeds.find(n => String(n.id) === String(reqForm.need_id));
      const invItem = inventory.find(i => String(i.id) === String(reqForm.resource_inventory_id));
      
      if (invItem && parseFloat(reqForm.quantity) > invItem.quantity) {
        alert(`Cannot request more than available quantity (${invItem.quantity} ${invItem.unit})`);
        setSaving(false);
        return;
      }

      await api.post('/api/resource/request', {
        resource_inventory_id: parseInt(reqForm.resource_inventory_id),
        resource_type: reqForm.resource_type,
        quantity_requested: parseFloat(reqForm.quantity),
        unit: reqForm.unit,
        reason: reqForm.reason,
        urgency: reqForm.urgency,
        need_id: reqForm.need_id ? parseInt(reqForm.need_id) : null,
        need_description: need ? need.category : null,
      });
      setReqModal(false); setReqForm({ resource_inventory_id: '', resource_type:'food', quantity:'', unit:'units', reason:'', urgency:'medium', need_id:'' });
      load();
    } catch(err) { 
      const detail = err.response?.data?.detail;
      alert(Array.isArray(detail) ? "Validation Error:\n" + detail.map(d => `- ${d.loc.slice(1).join(' ')}: ${d.msg}`).join('\n') : (detail || 'Operation failed'));
    }
    setSaving(false);
  };

  const handleContribute = async e => {
    e.preventDefault(); setSaving(true);
    try {
      await api.post('/api/resource/contribute', { ...ctbForm, quantity: parseFloat(ctbForm.quantity) });
      setCtbModal(false); setCtbForm({ resource_type:'food', name:'', quantity:'', unit:'units', notes:'' });
      load();
    } catch(err) { 
      const detail = err.response?.data?.detail;
      alert(Array.isArray(detail) ? "Validation Error:\n" + detail.map(d => `- ${d.loc.slice(1).join(' ')}: ${d.msg}`).join('\n') : (detail || 'Operation failed'));
    }
    setSaving(false);
  };

  const filteredInv = inventory.filter(i =>
    (i.name || '').toLowerCase().includes(search.toLowerCase()) ||
    (i.resource_type || '').toLowerCase().includes(search.toLowerCase())
  );

  const TABS_ADMIN = [['inventory','📦 Inventory'], ['requests','📤 Requests'], ['contributions','🔔 Contributions']];
  const TABS_NGO   = [['requests','📤 My Requests'], ['inventory','📦 Inventory'], ['contributions','🤝 My Contributions']];
  const TABS = isAdmin ? TABS_ADMIN : TABS_NGO;

  return (
    <div className="font-sans text-slate-900 animate-fade-in-up">
      {/* Header */}
      <div className="flex justify-between items-center mb-6 flex-wrap gap-4">
        <div>
          <h1 className="font-extrabold text-3xl text-slate-900 mb-1">📦 Resource Inventory</h1>
          <p className="text-slate-500 text-sm">{isAdmin ? `${inventory.length} items · ${contributions.length} pending contributions` : 'Global inventory & your NGO resource requests'}</p>
        </div>
        <div className="flex gap-2">
          {isAdmin && (
            <button onClick={() => setAddModal(true)} className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-bold text-sm transition-all shadow-sm">
              <Plus size={16} /> Add Item
            </button>
          )}
          {!isAdmin && (
            <>
              <button onClick={() => setReqModal(true)} className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-bold text-sm transition-all shadow-sm">
                <Package size={16} /> Request Resource
              </button>
              <button onClick={() => setCtbModal(true)} className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg font-bold text-sm transition-all shadow-sm">
                <ArrowUpCircle size={16} /> Contribute
              </button>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200 mb-6">
        {TABS.map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)}
            className={`px-4 py-2.5 font-bold text-sm outline-none transition-colors border-b-2 relative -bottom-[1px] ${tab === key ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}`}>
            {label}
          </button>
        ))}
      </div>

      {loading && <p className="text-slate-400 text-center py-12 animate-pulse">Loading…</p>}

      {/* ── Inventory tab ── */}
      {!loading && tab === 'inventory' && (
        <div className="animate-fade-in">
          <div className="relative mb-6 max-w-[320px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search inventory…" className="w-full pl-9 pr-4 py-2 border-2 border-slate-200 rounded-xl text-sm outline-none focus:border-indigo-500 transition-colors" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredInv.map(item => {
              const colorName = RTColors[item.resource_type] || 'slate';
              const pct = Math.min(100, (item.quantity / (item.initial_quantity || Math.max(item.quantity, 1))) * 100);
              return (
                <div key={item.id} className="bg-white border border-slate-100 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start mb-3">
                    <span className="text-3xl">{{'food':'🍚','water':'💧','medical':'💊','shelter':'🏠','equipment':'🔧','transport':'🚛','clothing':'👗','money':'💰'}[item.resource_type] || '📦'}</span>
                    {badge(colorName, item.resource_type)}
                  </div>
                  <div className="font-bold text-slate-900 text-[15px] mb-1">{item.name}</div>
                  <div className={`text-2xl font-extrabold text-${colorName}-500 flex items-baseline gap-1`}>
                    {item.quantity} <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">{item.unit}</span>
                  </div>
                  <div className="mt-3 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                    <div className={`h-full bg-${colorName}-500 transition-all duration-500 ease-out`} style={{ width: `${pct}%` }} />
                  </div>
                  <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mt-2">
                    {item.status === 'depleted' ? '🔴 Depleted' : item.quantity < 10 ? '🟡 Low stock' : '🟢 In stock'}
                  </div>
                </div>
              );
            })}
            {filteredInv.length === 0 && <p className="text-slate-400 col-span-full py-8 text-center font-medium">No inventory items found.</p>}
          </div>
        </div>
      )}

      {/* ── Admin & NGO: Requests tab ── */}
      {!loading && tab === 'requests' && (
        <div className="flex flex-col gap-3 animate-fade-in">
          {(isAdmin ? myRequests : myRequests).length === 0 && <p className="text-slate-400 text-center py-12 font-medium">No requests found.</p>}
          {(isAdmin ? myRequests : myRequests).map(r => (
            <div key={r.id} className="bg-white border border-slate-100 rounded-xl p-4 flex items-center justify-between flex-wrap gap-4 shadow-sm hover:shadow-md transition-shadow">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <span className="font-bold text-slate-800">{r.resource_type} — {r.quantity_requested} {r.unit}</span>
                  {badge(r.status === 'approved' ? 'emerald' : r.status === 'rejected' ? 'red' : 'amber', r.status)}
                </div>
                {isAdmin && <p className="text-xs font-semibold text-indigo-500">from {ngoNames[r.requesting_ngo_id] || `NGO #${r.requesting_ngo_id}`} {!r.requested_inventory_id && <span className="text-red-500 ml-1">(Old Request)</span>}</p>}
                {r.need_description && <span className="text-xs font-semibold text-indigo-500">for: {r.need_description}</span>}
                <p className="mt-1 text-sm text-slate-500">{r.reason}</p>
              </div>
              <div className="flex items-center gap-2">
                {isAdmin && r.status === 'pending' && (
                  <>
                    <button 
                      onClick={() => handleRequestAction(r.id, 'approve', r.requested_inventory_id, r.quantity_requested)} 
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-600 rounded-lg font-bold text-xs hover:bg-emerald-100 transition-colors ${!r.requested_inventory_id ? 'opacity-50 cursor-not-allowed' : ''}`}
                      title={!r.requested_inventory_id ? "Cannot approve old requests without item link" : ""}
                    >
                      <Check size={14} /> Approve
                    </button>
                    <button onClick={() => handleRequestAction(r.id, 'reject')} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-50 text-red-600 rounded-lg font-bold text-xs hover:bg-red-100 transition-colors">
                      <X size={14} /> Reject
                    </button>
                  </>
                )}
                {!isAdmin && r.quantity_allocated && <span className="text-xs font-bold text-slate-500 bg-slate-100 px-2 py-1 rounded-md">Allocated: {r.quantity_allocated} {r.unit}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Contributions tab ── */}
      {!loading && tab === 'contributions' && (
        <div className="flex flex-col gap-3 animate-fade-in">
          {(isAdmin ? contributions : myContribs).length === 0 && <p className="text-slate-400 text-center py-12 font-medium">{isAdmin ? 'No pending contributions.' : 'No contributions submitted yet.'}</p>}
          {(isAdmin ? contributions : myContribs).map(c => (
            <div key={c.id} className="bg-white border border-slate-100 rounded-xl p-4 flex items-center justify-between flex-wrap gap-4 shadow-sm hover:shadow-md transition-shadow">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <span className="font-bold text-slate-800">{c.name} — {c.quantity} {c.unit}</span>
                  {badge(c.status === 'approved' ? 'emerald' : c.status === 'rejected' ? 'red' : 'amber', c.status)}
                </div>
                {isAdmin && <span className="text-xs font-semibold text-slate-400">from {c.ngo_name}</span>}
                {c.notes && <p className="mt-1 text-sm text-slate-500">{c.notes}</p>}
              </div>
              <div className="flex items-center gap-2">
                {isAdmin && c.status === 'pending' && (
                  <>
                    <button onClick={() => handleContribAction(c.id, 'approve')} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-600 rounded-lg font-bold text-xs hover:bg-emerald-100 transition-colors">
                      <Check size={14} /> Approve
                    </button>
                    <button onClick={() => handleContribAction(c.id, 'reject')} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-50 text-red-600 rounded-lg font-bold text-xs hover:bg-red-100 transition-colors">
                      <X size={14} /> Reject
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Modals ── */}
      {addModal && (
        <div className="fixed inset-0 bg-slate-900/40 z-[300] flex items-center justify-center p-4 backdrop-blur-sm animate-fade-in" onClick={() => setAddModal(false)}>
          <div className="bg-white rounded-3xl p-8 w-full max-w-[440px] shadow-2xl animate-fade-in-up" onClick={e => e.stopPropagation()}>
            <h3 className="font-extrabold text-xl text-slate-900 mb-6 mt-0">Add Inventory Item</h3>
            <form onSubmit={handleAdd} className="flex flex-col gap-4">
              <Fld label="Name" type="text" value={addForm.name} onChange={v => setAddForm({...addForm, name:v})} placeholder="e.g. Rice Bags" required={true} />
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Type</label>
                <select value={addForm.resource_type} onChange={e => setAddForm({...addForm, resource_type:e.target.value})} className="w-full px-4 py-3 bg-slate-50 border-2 border-slate-100 rounded-xl text-sm font-semibold outline-none focus:border-emerald-500 focus:bg-white transition-all cursor-pointer">
                  {Object.keys(RTColors).map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <Fld label="Quantity" type="number" value={addForm.quantity} onChange={v => setAddForm({...addForm, quantity:v})} placeholder="0" required={true} />
              <Fld label="Unit" type="text" value={addForm.unit} onChange={v => setAddForm({...addForm, unit:v})} placeholder="units" required={false} />
              <div className="flex gap-2 justify-end mt-4">
                <button type="button" onClick={()=>setAddModal(false)} className="px-5 py-2.5 bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-xl font-bold text-sm transition-colors">Cancel</button>
                <button type="submit" disabled={saving} className="px-5 py-2.5 bg-emerald-500 text-white hover:bg-emerald-600 rounded-xl font-bold text-sm transition-colors shadow-sm">{saving?'Saving…':'Add Item'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {reqModal && (
        <div className="fixed inset-0 bg-slate-900/40 z-[300] flex items-center justify-center p-4 backdrop-blur-sm animate-fade-in" onClick={() => setReqModal(false)}>
          <div className="bg-white rounded-3xl p-8 w-full max-w-[480px] shadow-2xl animate-fade-in-up" onClick={e => e.stopPropagation()}>
            <h3 className="font-extrabold text-xl text-slate-900 mb-6 mt-0">Request Resource from Admin</h3>
            <form onSubmit={handleRequest} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Select Item from Inventory *</label>
                <select 
                  value={reqForm.resource_inventory_id} 
                  onChange={e => {
                    const item = inventory.find(i => String(i.id) === e.target.value);
                    if (item) setReqForm({ ...reqForm, resource_inventory_id: e.target.value, resource_type: item.resource_type, unit: item.unit });
                  }} 
                  required
                  className="w-full px-4 py-3 bg-slate-50 border-2 border-slate-100 rounded-xl text-sm font-semibold outline-none focus:border-blue-500 focus:bg-white transition-all cursor-pointer"
                >
                  <option value="">— Select an item —</option>
                  {inventory.filter(i => i.quantity > 0).map(i => (
                    <option key={i.id} value={i.id}>{i.name} ({i.quantity} {i.unit} available)</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-4">
                <div className="flex-1 w-full">
                  <Fld label="Quantity *" type="number" value={reqForm.quantity} onChange={v => setReqForm({...reqForm, quantity:v})} placeholder="0" required={true} />
                </div>
                <div className="flex-1">
                  <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Unit</label>
                  <input value={reqForm.unit} disabled className="w-full px-4 py-3 bg-slate-100 border-2 border-slate-100 rounded-xl text-sm font-semibold text-slate-400 outline-none" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Urgency</label>
                <select value={reqForm.urgency} onChange={e => setReqForm({...reqForm, urgency:e.target.value})} className="w-full px-4 py-3 bg-slate-50 border-2 border-slate-100 rounded-xl text-sm font-semibold outline-none focus:border-blue-500 focus:bg-white transition-all cursor-pointer">
                  {['low','medium','high'].map(u=><option key={u} value={u}>{u}</option>)}
                </select>
              </div>
              <Fld label="Reason *" type="text" value={reqForm.reason} onChange={v => setReqForm({...reqForm, reason:v})} placeholder="Why do you need this?" required={true} />
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">For Task (optional)</label>
                <select value={reqForm.need_id} onChange={e => setReqForm({...reqForm, need_id:e.target.value})} className="w-full px-4 py-3 bg-slate-50 border-2 border-slate-100 rounded-xl text-sm font-semibold outline-none focus:border-blue-500 focus:bg-white transition-all cursor-pointer">
                  <option value="">— No specific task —</option>
                  {assignedNeeds.map(n => <option key={n.id} value={n.id}>#{n.id} · {n.category} ({n.location || 'N/A'})</option>)}
                </select>
              </div>
              <div className="flex gap-2 justify-end mt-4">
                <button type="button" onClick={()=>setReqModal(false)} className="px-5 py-2.5 bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-xl font-bold text-sm transition-colors">Cancel</button>
                <button type="submit" disabled={saving} className="px-5 py-2.5 bg-blue-500 text-white hover:bg-blue-600 rounded-xl font-bold text-sm transition-colors shadow-sm">{saving?'Submitting…':'Submit Request'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {ctbModal && (
        <div className="fixed inset-0 bg-slate-900/40 z-[300] flex items-center justify-center p-4 backdrop-blur-sm animate-fade-in" onClick={() => setCtbModal(false)}>
          <div className="bg-white rounded-3xl p-8 w-full max-w-[440px] shadow-2xl animate-fade-in-up" onClick={e => e.stopPropagation()}>
            <h3 className="font-extrabold text-xl text-slate-900 mb-2 mt-0">Contribute to Global Inventory</h3>
            <p className="text-sm text-slate-500 mb-6 font-medium">Suggest items to donate. Admin will review and merge into inventory.</p>
            <form onSubmit={handleContribute} className="flex flex-col gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">Type</label>
                <select value={ctbForm.resource_type} onChange={e => setCtbForm({...ctbForm, resource_type:e.target.value})} className="w-full px-4 py-3 bg-slate-50 border-2 border-slate-100 rounded-xl text-sm font-semibold outline-none focus:border-purple-500 focus:bg-white transition-all cursor-pointer">
                  {Object.keys(RTColors).map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <Fld label="Item Name *" type="text" value={ctbForm.name} onChange={v => setCtbForm({...ctbForm, name:v})} placeholder="Must match existing item name to merge" required={true} />
              <Fld label="Quantity *" type="number" value={ctbForm.quantity} onChange={v => setCtbForm({...ctbForm, quantity:v})} placeholder="0" required={true} />
              <Fld label="Unit" type="text" value={ctbForm.unit} onChange={v => setCtbForm({...ctbForm, unit:v})} placeholder="units" required={false} />
              <Fld label="Notes" type="text" value={ctbForm.notes} onChange={v => setCtbForm({...ctbForm, notes:v})} placeholder="Optional details" required={false} />
              <div className="flex gap-2 justify-end mt-4">
                <button type="button" onClick={()=>setCtbModal(false)} className="px-5 py-2.5 bg-slate-100 text-slate-600 hover:bg-slate-200 rounded-xl font-bold text-sm transition-colors">Cancel</button>
                <button type="submit" disabled={saving} className="px-5 py-2.5 bg-purple-500 text-white hover:bg-purple-600 rounded-xl font-bold text-sm transition-colors shadow-sm">{saving?'Submitting…':'Submit Contribution'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

const Fld = ({ label, type, value, onChange, placeholder, required }) => (
  <div>
    <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">{label}</label>
    <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} required={required} className="w-full px-4 py-3 bg-slate-50 border-2 border-slate-100 rounded-xl text-sm font-semibold outline-none focus:border-indigo-500 focus:bg-white transition-all" />
  </div>
);
