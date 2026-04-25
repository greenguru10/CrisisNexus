import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { LogIn, ArrowRight, ShieldCheck, HeartPulse, Building2, CheckCircle2 } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

const NGO_TYPES = [
  { value: 'disaster_relief', label: 'Disaster Relief' },
  { value: 'medical', label: 'Medical & Health' },
  { value: 'food_distribution', label: 'Food Distribution' },
  { value: 'education', label: 'Education' },
  { value: 'logistics', label: 'Logistics & Transport' },
  { value: 'shelter', label: 'Shelter & Housing' },
  { value: 'rehabilitation', label: 'Rehabilitation' },
  { value: 'water_sanitation', label: 'Water & Sanitation' },
  { value: 'child_welfare', label: 'Child Welfare' },
  { value: 'others', label: 'Others' },
];

function Field({ label, name, type = 'text', value, onChange, placeholder, required }) {
  return (
    <div>
      <label className="block text-sm font-semibold text-slate-700 mb-1.5">{label}{required && ' *'}</label>
      <input type={type} name={name} value={value} onChange={onChange}
        placeholder={placeholder} required={required}
        className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 transition-all placeholder:text-slate-400"
      />
    </div>
  );
}

function FieldSelect({ label, name, value, onChange, required, children }) {
  return (
    <div>
      <label className="block text-sm font-semibold text-slate-700 mb-1.5">{label}{required && ' *'}</label>
      <select name={name} value={value} onChange={onChange} required={required}
        className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 transition-all cursor-pointer appearance-none">
        {children}
      </select>
    </div>
  );
}

function ErrBox({ msg }) {
  if (!msg) return null;
  return (
    <div className="px-4 py-3 bg-red-50 border border-red-200 text-red-600 rounded-xl text-sm font-medium animate-fade-in">
      {msg}
    </div>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  const [ngoNames, setNgoNames] = useState([]);
  const [showLoginModal, setShowLoginModal] = useState(false);

  // Login State
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState('');

  // Forms
  const [volRegForm, setVolRegForm] = useState({ name: '', email: '', password: '', ngo_name: '', skills: '' });
  const [ngoRegForm, setNgoRegForm] = useState({ org_name: '', ngo_type: '', email: '', password: '' });
  
  // Status
  const [volStatus, setVolStatus] = useState({ loading: false, error: '', success: false });
  const [ngoStatus, setNgoStatus] = useState({ loading: false, error: '', success: false });

  useEffect(() => {
    if (localStorage.getItem('token')) navigate('/dashboard');
    axios.get(`${API_BASE}/api/ngo/names`).then(r => setNgoNames(r.data)).catch(() => {});
  }, [navigate]);

  const doLogin = async (e) => {
    e.preventDefault(); setLoginLoading(true); setLoginError('');
    try {
      const res = await axios.post(`${API_BASE}/auth/login`, loginForm);
      const { access_token, role, ngo_id, ngo_name } = res.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('role', role);
      if (ngo_id) { localStorage.setItem('ngo_id', ngo_id); localStorage.setItem('ngo_name', ngo_name || ''); }
      window.location.href = '/dashboard';
    } catch (err) {
      setLoginError(err.response?.data?.detail || 'Invalid credentials. Please try again.');
    } finally {
      setLoginLoading(false);
    }
  };

  const onVolRegister = async e => {
    e.preventDefault(); setVolStatus({ loading: true, error: '', success: false });
    try {
      await axios.post(`${API_BASE}/auth/register`, {
        email: volRegForm.email, password: volRegForm.password, role: 'volunteer',
        volunteer_name: volRegForm.name, ngo_name: volRegForm.ngo_name,
        skills: volRegForm.skills ? volRegForm.skills.split(',').map(s => s.trim()).filter(Boolean) : [],
      });
      setVolStatus({ loading: false, error: '', success: true });
    } catch (err) { setVolStatus({ loading: false, error: err.response?.data?.detail || 'Registration failed', success: false }); }
  };

  const onNgoRegister = async e => {
    e.preventDefault(); setNgoStatus({ loading: true, error: '', success: false });
    try {
      await axios.post(`${API_BASE}/auth/register`, {
        email: ngoRegForm.email, password: ngoRegForm.password, role: 'ngo',
        ngo_name: ngoRegForm.org_name, ngo_type: ngoRegForm.ngo_type,
      });
      setNgoStatus({ loading: false, error: '', success: true });
    } catch (err) { setNgoStatus({ loading: false, error: err.response?.data?.detail || 'Registration failed', success: false }); }
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-indigo-200">
      
      {/* ── NAV ── */}
      <nav className="fixed top-0 w-full z-40 bg-white/80 backdrop-blur-md border-b border-slate-200/50 transition-all">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="text-3xl">🌍</span>
            <span className="font-extrabold text-2xl text-indigo-600 tracking-tight">CommunitySync</span>
          </div>
          <div className="flex items-center gap-6">
            <button onClick={() => document.getElementById('volunteer').scrollIntoView({ behavior: 'smooth' })} className="hidden md:block text-sm font-semibold text-slate-600 hover:text-indigo-600 transition-colors">Volunteers</button>
            <button onClick={() => document.getElementById('ngo').scrollIntoView({ behavior: 'smooth' })} className="hidden md:block text-sm font-semibold text-slate-600 hover:text-indigo-600 transition-colors">NGOs</button>
            <button onClick={() => document.getElementById('admin').scrollIntoView({ behavior: 'smooth' })} className="hidden md:block text-sm font-semibold text-slate-600 hover:text-indigo-600 transition-colors">Admins</button>
            <div className="w-px h-6 bg-slate-200 hidden md:block mx-2"></div>
            <button onClick={() => setShowLoginModal(true)} className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-full font-bold text-sm shadow-lg shadow-indigo-600/20 transition-all hover:-translate-y-0.5">
              <LogIn size={18} strokeWidth={2.5} /> Sign In
            </button>
          </div>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section className="relative pt-36 pb-24 lg:pt-48 lg:pb-32 overflow-hidden">
        {/* Animated Background Gradients */}
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-50 via-white to-slate-50"></div>
        <div className="absolute top-0 right-0 -translate-y-12 translate-x-1/3 w-[800px] h-[800px] bg-indigo-100/50 rounded-full blur-3xl opacity-60 pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 translate-y-1/3 -translate-x-1/3 w-[600px] h-[600px] bg-purple-100/50 rounded-full blur-3xl opacity-60 pointer-events-none"></div>

        <div className="max-w-5xl mx-auto px-6 text-center animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-sm font-bold tracking-wide mb-8 shadow-sm">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-indigo-500"></span>
            </span>
            Multi-NGO Crisis Coordination Platform
          </div>
          <h1 className="text-5xl md:text-7xl lg:text-[5rem] font-extrabold text-slate-900 tracking-tight leading-tight mb-8">
            Crisis Response, <br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
              Coordinated.
            </span>
          </h1>
          <p className="text-lg md:text-xl text-slate-500 max-w-2xl mx-auto leading-relaxed mb-12">
            A unified intelligence platform connecting System Admins, NGOs, and field volunteers to orchestrate disaster relief efforts seamlessly.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button onClick={() => document.getElementById('volunteer').scrollIntoView({ behavior: 'smooth' })} className="w-full sm:w-auto px-8 py-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full font-bold shadow-xl shadow-indigo-600/30 transition-all hover:-translate-y-1 flex items-center justify-center gap-2 text-lg">
              Join as Volunteer <ArrowRight size={20} strokeWidth={2.5} />
            </button>
            <button onClick={() => document.getElementById('ngo').scrollIntoView({ behavior: 'smooth' })} className="w-full sm:w-auto px-8 py-4 bg-white hover:bg-slate-50 text-slate-700 border-2 border-slate-200 rounded-full font-bold shadow-sm transition-all flex items-center justify-center gap-2 text-lg">
              Register NGO
            </button>
          </div>
        </div>
      </section>

      {/* ── VOLUNTEER SECTION ── */}
      <section id="volunteer" className="py-24 bg-white border-t border-slate-100 relative">
        <div className="absolute left-0 top-0 w-1/3 h-full bg-gradient-to-r from-emerald-50/50 to-transparent pointer-events-none"></div>
        <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center relative z-10">
          <div>
            <div className="w-14 h-14 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mb-8 shadow-inner">
              <HeartPulse size={28} strokeWidth={2.5} />
            </div>
            <h2 className="text-4xl md:text-5xl font-extrabold text-slate-900 mb-6 leading-tight">
              Join the field.<br/>Make real impact.
            </h2>
            <p className="text-lg text-slate-600 mb-10 leading-relaxed">
              Register as a volunteer to receive task assignments matched to your skills. Earn badges, track your impact, and be part of a coordinated crisis response network.
            </p>
            <ul className="space-y-5">
              {['AI-matched task assignments based on your specific skills.', 'Accept, start, and complete tasks from a mobile-friendly dashboard.', 'Earn milestone badges and climb your NGO leaderboard.', 'Instant Email & WhatsApp notifications for urgent deployments.'].map((item, i) => (
                <li key={i} className="flex items-start gap-4 text-slate-700 font-semibold text-lg">
                  <CheckCircle2 className="text-emerald-500 shrink-0 mt-0.5" size={24} />
                  {item}
                </li>
              ))}
            </ul>
          </div>
          
          <div className="bg-white border border-slate-200 rounded-[2rem] p-8 md:p-10 shadow-2xl shadow-slate-200/50">
            {volStatus.success ? (
              <div className="text-center py-12 animate-fade-in">
                <div className="w-24 h-24 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
                  <CheckCircle2 size={48} strokeWidth={2.5} />
                </div>
                <h3 className="text-3xl font-extrabold text-slate-900 mb-4">Registration Successful!</h3>
                <p className="text-slate-600 mb-10 text-lg">Your NGO Coordinator will review and approve your account. Check your email for updates.</p>
                <button onClick={() => { setVolStatus({ loading:false, error:'', success:false }); setVolRegForm({ name:'', email:'', password:'', ngo_name:'', skills:'' }); }} className="bg-slate-900 text-white px-8 py-3 rounded-xl font-bold hover:bg-slate-800 transition-colors">
                  Register Another
                </button>
              </div>
            ) : (
              <div className="animate-fade-in">
                <h3 className="text-2xl font-extrabold text-slate-900 mb-8 flex items-center gap-3">
                  <span className="bg-emerald-100 text-emerald-600 px-3 py-1.5 rounded-lg text-sm">🤝</span>
                  Register as a Volunteer
                </h3>
                <form onSubmit={onVolRegister} className="space-y-5">
                  <Field label="Full Name" name="name" value={volRegForm.name} onChange={e=>setVolRegForm({...volRegForm, name: e.target.value})} placeholder="Jane Doe" required />
                  <Field label="Email Address" name="email" type="email" value={volRegForm.email} onChange={e=>setVolRegForm({...volRegForm, email: e.target.value})} placeholder="jane@example.com" required />
                  <Field label="Password" name="password" type="password" value={volRegForm.password} onChange={e=>setVolRegForm({...volRegForm, password: e.target.value})} placeholder="Min 6 characters" required />
                  <div>
                    <FieldSelect label="NGO to Join" name="ngo_name" value={volRegForm.ngo_name} onChange={e=>setVolRegForm({...volRegForm, ngo_name: e.target.value})} required>
                      <option value="">Select an NGO…</option>
                      {ngoNames.map(n => <option key={n.id} value={n.name}>{n.name}</option>)}
                    </FieldSelect>
                    {ngoNames.length === 0 && <p className="text-xs text-amber-600 font-bold mt-2">⚠️ No approved NGOs found. Contact admin.</p>}
                  </div>
                  <Field label="Skills (comma-separated)" name="skills" value={volRegForm.skills} onChange={e=>setVolRegForm({...volRegForm, skills: e.target.value})} placeholder="medical, logistics, first aid" />
                  
                  <ErrBox msg={volStatus.error} />
                  
                  <button type="submit" disabled={volStatus.loading} className="w-full py-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-lg shadow-emerald-600/20 transition-all mt-6 disabled:opacity-70 text-lg">
                    {volStatus.loading ? 'Registering...' : 'Create Volunteer Account'}
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ── NGO SECTION ── */}
      <section id="ngo" className="py-24 bg-slate-50 border-t border-slate-200 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-1/3 h-full bg-gradient-to-l from-purple-50/80 to-transparent pointer-events-none"></div>
        <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center relative z-10">
          <div className="order-2 lg:order-1 bg-white border border-slate-200 rounded-[2rem] p-8 md:p-10 shadow-2xl shadow-slate-200/50">
            {ngoStatus.success ? (
              <div className="text-center py-12 animate-fade-in">
                <div className="w-24 h-24 bg-purple-100 text-purple-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
                  <CheckCircle2 size={48} strokeWidth={2.5} />
                </div>
                <h3 className="text-3xl font-extrabold text-slate-900 mb-4">Registration Submitted!</h3>
                <p className="text-slate-600 mb-10 text-lg">Your NGO is pending Admin approval. You'll receive an email once your organization is activated.</p>
                <button onClick={() => { setNgoStatus({ loading:false, error:'', success:false }); setNgoRegForm({ org_name:'', ngo_type:'', email:'', password:'' }); }} className="bg-slate-900 text-white px-8 py-3 rounded-xl font-bold hover:bg-slate-800 transition-colors">
                  Register Another
                </button>
              </div>
            ) : (
              <div className="animate-fade-in">
                <h3 className="text-2xl font-extrabold text-slate-900 mb-8 flex items-center gap-3">
                  <span className="bg-purple-100 text-purple-600 px-3 py-1.5 rounded-lg text-sm">🏢</span>
                  Register Your NGO
                </h3>
                <form onSubmit={onNgoRegister} className="space-y-5">
                  <Field label="NGO / Organization Name" name="org_name" value={ngoRegForm.org_name} onChange={e=>setNgoRegForm({...ngoRegForm, org_name: e.target.value})} placeholder="Global Relief Foundation" required />
                  <FieldSelect label="Primary Focus Area" name="ngo_type" value={ngoRegForm.ngo_type} onChange={e=>setNgoRegForm({...ngoRegForm, ngo_type: e.target.value})} required>
                    <option value="">Select NGO type…</option>
                    {NGO_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </FieldSelect>
                  <Field label="Coordinator Email" name="email" type="email" value={ngoRegForm.email} onChange={e=>setNgoRegForm({...ngoRegForm, email: e.target.value})} placeholder="coordinator@ngo.org" required />
                  <Field label="Password" name="password" type="password" value={ngoRegForm.password} onChange={e=>setNgoRegForm({...ngoRegForm, password: e.target.value})} placeholder="Min 6 characters" required />
                  
                  <ErrBox msg={ngoStatus.error} />
                  
                  <button type="submit" disabled={ngoStatus.loading} className="w-full py-4 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-bold shadow-lg shadow-purple-600/20 transition-all mt-6 disabled:opacity-70 text-lg">
                    {ngoStatus.loading ? 'Submitting...' : 'Register Organization'}
                  </button>
                </form>
              </div>
            )}
          </div>

          <div className="order-1 lg:order-2 pl-0 lg:pl-10">
            <div className="w-14 h-14 bg-purple-100 text-purple-600 rounded-2xl flex items-center justify-center mb-8 shadow-inner">
              <Building2 size={28} strokeWidth={2.5} />
            </div>
            <h2 className="text-4xl md:text-5xl font-extrabold text-slate-900 mb-6 leading-tight">
              Coordinate your NGO.<br/>Amplify your reach.
            </h2>
            <p className="text-lg text-slate-600 mb-10 leading-relaxed">
              Register your NGO to gain access to volunteer management, AI-powered task assignment, shared resource pools, and cross-NGO coordination with the Admin.
            </p>
            <ul className="space-y-5">
              {['Manage volunteers — approve, reject, and track performance.', 'Receive tasks pushed by Admin, accept or reject them.', 'Request resources & borrow volunteers from the global pool.', 'View NGO-scoped analytics, leaderboard & full task trails.'].map((item, i) => (
                <li key={i} className="flex items-start gap-4 text-slate-700 font-semibold text-lg">
                  <CheckCircle2 className="text-purple-500 shrink-0 mt-0.5" size={24} />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ── ADMIN SECTION ── */}
      <section id="admin" className="py-24 bg-slate-900 text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20 pointer-events-none"></div>
        <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
          <div className="w-16 h-16 bg-blue-500/20 text-blue-400 rounded-2xl flex items-center justify-center mx-auto mb-8 shadow-inner ring-1 ring-blue-500/30">
            <ShieldCheck size={32} strokeWidth={2.5} />
          </div>
          <h2 className="text-4xl md:text-5xl font-extrabold mb-6 leading-tight text-white">
            Govern the platform.<br/>Full system control.
          </h2>
          <p className="text-lg text-slate-400 mb-10 leading-relaxed max-w-2xl mx-auto">
            Admin accounts are pre-provisioned by the system. Login to access the global management dashboard — approve NGOs, assign tasks, manage inventory, and oversee the entire network.
          </p>
          <button onClick={() => setShowLoginModal(true)} className="px-10 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-full font-bold shadow-lg shadow-blue-600/20 transition-all hover:-translate-y-1 text-lg">
            Admin Sign In
          </button>
          <p className="mt-6 text-sm text-slate-500 font-medium flex items-center justify-center gap-2">
            🔒 No self-registration available for Admins.
          </p>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="bg-black py-16 text-center text-slate-400 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-6 flex flex-col items-center">
          <div className="flex items-center gap-3 mb-6 opacity-50 hover:opacity-100 transition-opacity cursor-pointer">
            <span className="text-2xl grayscale">🌍</span>
            <span className="font-extrabold text-xl tracking-tight text-white">CommunitySync</span>
          </div>
          <p className="text-sm font-medium mb-4 max-w-sm">Built with precision for communities that need it most. Ensuring every resource and volunteer is perfectly orchestrated.</p>
          <p className="text-xs opacity-40 font-semibold tracking-wider uppercase">© 2026 CommunitySync. All rights reserved.</p>
        </div>
      </footer>

      {/* ── UNIFIED LOGIN MODAL ── */}
      {showLoginModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-md animate-fade-in">
          <div className="absolute inset-0" onClick={() => setShowLoginModal(false)}></div>
          <div className="relative bg-white w-full max-w-[420px] rounded-[2rem] shadow-2xl p-8 md:p-10 border border-slate-100 animate-fade-in-up">
            <div className="absolute -top-12 left-1/2 -translate-x-1/2 w-24 h-24 bg-indigo-50 rounded-full border-8 border-white flex items-center justify-center text-indigo-600 shadow-sm">
              <ShieldCheck size={36} strokeWidth={2.5} />
            </div>
            
            <div className="text-center mt-10 mb-8">
              <h3 className="text-3xl font-extrabold text-slate-900 tracking-tight">Welcome Back</h3>
              <p className="text-slate-500 font-semibold mt-2">Sign in to your dashboard</p>
            </div>

            <form onSubmit={doLogin} className="space-y-5">
              <Field label="Email Address" name="email" type="email" value={loginForm.email} onChange={e=>setLoginForm({...loginForm, email:e.target.value})} placeholder="you@example.com" required />
              <Field label="Password" name="password" type="password" value={loginForm.password} onChange={e=>setLoginForm({...loginForm, password:e.target.value})} placeholder="••••••••" required />
              
              <ErrBox msg={loginError} />
              
              <button type="submit" disabled={loginLoading} className="w-full py-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-extrabold shadow-lg shadow-indigo-600/30 transition-all mt-4 disabled:opacity-70 text-lg">
                {loginLoading ? 'Authenticating...' : 'Sign In'}
              </button>
            </form>
            
            <button onClick={() => setShowLoginModal(false)} className="w-full mt-4 py-3 text-slate-500 font-bold hover:bg-slate-50 hover:text-slate-700 rounded-xl transition-colors">
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
