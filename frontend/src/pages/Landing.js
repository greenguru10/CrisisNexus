import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

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

// ─── Shared helpers ──────────────────────────────────────────────────────────
const inputCls = (accent = '#6366f1') => ({
  width: '100%', padding: '0.7rem 0.875rem', borderRadius: '8px',
  border: '1.5px solid #e2e8f0', background: '#fff', color: '#1e293b',
  fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box',
  transition: 'border-color 0.2s', fontFamily: 'inherit',
});

function Field({ label, name, type = 'text', value, onChange, placeholder, required, accent = '#6366f1' }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#475569', marginBottom: '0.35rem' }}>
        {label}{required && ' *'}
      </label>
      <input type={type} name={name} value={value} onChange={onChange}
        placeholder={placeholder} required={required}
        style={inputCls(accent)}
        onFocus={e => e.target.style.borderColor = accent}
        onBlur={e => e.target.style.borderColor = '#e2e8f0'}
      />
    </div>
  );
}

function FieldSelect({ label, name, value, onChange, required, children, accent = '#6366f1' }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#475569', marginBottom: '0.35rem' }}>
        {label}{required && ' *'}
      </label>
      <select name={name} value={value} onChange={onChange} required={required}
        style={{ ...inputCls(accent), cursor: 'pointer' }}
        onFocus={e => e.target.style.borderColor = accent}
        onBlur={e => e.target.style.borderColor = '#e2e8f0'}>
        {children}
      </select>
    </div>
  );
}

function ErrBox({ msg }) {
  if (!msg) return null;
  return (
    <div style={{ padding: '0.6rem 0.875rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#dc2626', fontSize: '0.82rem' }}>
      {msg}
    </div>
  );
}

// ─── Shared login helper ─────────────────────────────────────────────────────
async function doLogin(email, password) {
  const res = await axios.post(`${API_BASE}/auth/login`, { email, password });
  const { access_token, role, ngo_id, ngo_name } = res.data;
  localStorage.setItem('token', access_token);
  localStorage.setItem('role', role);
  if (ngo_id) { localStorage.setItem('ngo_id', ngo_id); localStorage.setItem('ngo_name', ngo_name || ''); }
  window.location.href = '/dashboard';
}

// ─── Capability list ─────────────────────────────────────────────────────────
function CapList({ items, accent }) {
  return (
    <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
      {items.map(item => (
        <li key={item} style={{ display: 'flex', gap: '0.6rem', fontSize: '0.9rem', color: '#475569', alignItems: 'flex-start' }}>
          <span style={{ color: accent, fontWeight: 700, marginTop: '1px', flexShrink: 0 }}>✓</span>
          {item}
        </li>
      ))}
    </ul>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════
export default function Landing() {
  const navigate = useNavigate();
  const [ngoNames, setNgoNames] = useState([]);

  useEffect(() => {
    if (localStorage.getItem('token')) navigate('/dashboard');
    // Fetch NGO names for volunteer registration
    axios.get(`${API_BASE}/api/ngo/names`).then(r => setNgoNames(r.data)).catch(() => {});
  }, [navigate]);

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc', fontFamily: "'Inter', sans-serif", color: '#1e293b' }}>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet" />

      {/* ── NAV ── */}
      <nav style={{ position: 'sticky', top: 0, zIndex: 100, background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(12px)', borderBottom: '1px solid #e2e8f0', padding: '0.875rem 2.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <span style={{ fontSize: '1.5rem' }}>🌍</span>
          <span style={{ fontWeight: 800, fontSize: '1.2rem', color: '#4f46e5' }}>CommunitySync</span>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {[['#volunteer', '🤝 Volunteer', '#15803d'], ['#ngo', '🏢 NGO', '#7c3aed'], ['#admin', '🛡️ Admin', '#1e40af']].map(([href, label, color]) => (
            <a key={href} href={href}
              style={{ padding: '0.4rem 1rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 600, color, background: color + '12', textDecoration: 'none', border: `1px solid ${color}30`, transition: 'all 0.2s' }}
              onMouseOver={e => { e.currentTarget.style.background = color + '20'; }}
              onMouseOut={e => { e.currentTarget.style.background = color + '12'; }}>
              {label}
            </a>
          ))}
        </div>
      </nav>

      {/* ── HERO STRIP ── */}
      <div style={{ textAlign: 'center', padding: '4rem 2rem 3rem', background: 'linear-gradient(180deg, #fff 0%, #f1f5f9 100%)' }}>
        <div style={{ display: 'inline-block', padding: '0.35rem 1.1rem', borderRadius: '999px', background: '#ede9fe', fontSize: '0.8rem', color: '#6d28d9', fontWeight: 600, marginBottom: '1.5rem' }}>
          🚀 Multi-NGO Crisis Coordination Platform
        </div>
        <h1 style={{ fontSize: 'clamp(2rem, 5vw, 3.75rem)', fontWeight: 900, lineHeight: 1.15, color: '#0f172a', margin: '0 auto 1rem', maxWidth: '700px' }}>
          Crisis Response,{' '}
          <span style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Coordinated.
          </span>
        </h1>
        <p style={{ color: '#64748b', fontSize: '1.05rem', maxWidth: '560px', margin: '0 auto 2.5rem', lineHeight: 1.7 }}>
          Select your role below to get started. Each section is tailored to your access level.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', flexWrap: 'wrap' }}>
          {[['#volunteer', '🤝', 'Volunteer'], ['#ngo', '🏢', 'NGO Coordinator'], ['#admin', '🛡️', 'System Admin']].map(([href, icon, label]) => (
            <a key={href} href={href} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.4rem', textDecoration: 'none', color: '#6366f1', fontWeight: 600, fontSize: '0.9rem' }}>
              <div style={{ width: '52px', height: '52px', borderRadius: '14px', background: '#ede9fe', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem' }}>{icon}</div>
              {label}
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>↓ scroll</span>
            </a>
          ))}
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════
          SECTION 1 — VOLUNTEER
      ══════════════════════════════════════════════════════════ */}
      <VolunteerSection ngoNames={ngoNames} />

      {/* ══════════════════════════════════════════════════════════
          SECTION 2 — NGO COORDINATOR
      ══════════════════════════════════════════════════════════ */}
      <NgoSection />

      {/* ══════════════════════════════════════════════════════════
          SECTION 3 — ADMIN
      ══════════════════════════════════════════════════════════ */}
      <AdminSection />

      {/* ── FOOTER ── */}
      <footer style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8', fontSize: '0.85rem', borderTop: '1px solid #e2e8f0', background: '#fff' }}>
        Built with ❤️ for communities that need it most · CommunitySync © 2026
      </footer>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION 1 — VOLUNTEER
// ═══════════════════════════════════════════════════════════════════════════════
function VolunteerSection({ ngoNames }) {
  const ACCENT = '#15803d';
  const [showReg, setShowReg] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [regForm, setRegForm] = useState({ name: '', email: '', password: '', ngo_name: '', skills: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleLoginChange = e => setLoginForm({ ...loginForm, [e.target.name]: e.target.value });
  const handleRegChange = e => setRegForm({ ...regForm, [e.target.name]: e.target.value });

  const onLogin = async e => {
    e.preventDefault(); setLoading(true); setError('');
    try { await doLogin(loginForm.email, loginForm.password); }
    catch (err) { setError(err.response?.data?.detail || 'Login failed'); }
    finally { setLoading(false); }
  };

  const onRegister = async e => {
    e.preventDefault(); setLoading(true); setError('');
    try {
      await axios.post(`${API_BASE}/auth/register`, {
        email: regForm.email, password: regForm.password, role: 'volunteer',
        volunteer_name: regForm.name, ngo_name: regForm.ngo_name,
        skills: regForm.skills ? regForm.skills.split(',').map(s => s.trim()).filter(Boolean) : [],
      });
      setSuccess(true);
    } catch (err) { setError(err.response?.data?.detail || 'Registration failed'); }
    finally { setLoading(false); }
  };

  return (
    <section id="volunteer" style={{ padding: '5rem 2rem', background: 'linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%)', borderTop: '4px solid #bbf7d0' }}>
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '3rem', alignItems: 'start' }}>

        {/* Left: Info */}
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.35rem 0.875rem', borderRadius: '999px', background: '#dcfce7', color: ACCENT, fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.06em', marginBottom: '1.25rem' }}>
            🤝 FOR VOLUNTEERS
          </div>
          <h2 style={{ fontSize: '2rem', fontWeight: 800, color: '#052e16', marginBottom: '1rem', lineHeight: 1.2 }}>
            Join the field.<br />Make real impact.
          </h2>
          <p style={{ color: '#166534', lineHeight: 1.7, marginBottom: '1.75rem', fontSize: '0.95rem' }}>
            Register as a volunteer to receive task assignments matched to your skills. Earn badges, track your impact, and be part of a coordinated crisis response network.
          </p>
          <CapList accent={ACCENT} items={[
            'Get matched to tasks by AI based on your skills & location',
            'Accept, start, and complete tasks from your dashboard',
            'Earn milestone badges and climb your NGO leaderboard',
            'Receive Email & WhatsApp notifications instantly',
            'Track your streak, rating, and impact over time',
          ]} />
          <div style={{ marginTop: '2rem', padding: '1rem', borderRadius: '12px', background: '#dcfce7', border: '1px solid #bbf7d0' }}>
            <p style={{ fontSize: '0.82rem', color: '#166534', margin: 0 }}>
              ⏳ <strong>Approval required:</strong> After registration, your NGO Coordinator will review and approve your account before you can log in.
            </p>
          </div>
        </div>

        {/* Right: Form */}
        <div style={{ background: '#fff', borderRadius: '20px', border: '1.5px solid #bbf7d0', padding: '2rem', boxShadow: '0 8px 32px rgba(21,128,61,0.08)' }}>
          {success ? (
            <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✅</div>
              <h3 style={{ fontWeight: 800, color: '#0f172a', marginBottom: '0.5rem' }}>Registration Submitted!</h3>
              <p style={{ color: '#64748b', lineHeight: 1.6, fontSize: '0.9rem' }}>Your NGO Coordinator will review and approve your account. Check your email for updates.</p>
              <button onClick={() => { setSuccess(false); setShowReg(false); setRegForm({ name: '', email: '', password: '', ngo_name: '', skills: '' }); }}
                style={{ marginTop: '1.25rem', padding: '0.6rem 1.5rem', borderRadius: '8px', border: 'none', background: ACCENT, color: '#fff', cursor: 'pointer', fontWeight: 600, fontFamily: 'inherit' }}>
                Back to Login
              </button>
            </div>
          ) : !showReg ? (
            <>
              <h3 style={{ fontWeight: 800, fontSize: '1.2rem', color: '#052e16', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ background: '#dcfce7', borderRadius: '8px', padding: '4px 8px', fontSize: '1.1rem' }}>🤝</span>
                Volunteer Login
              </h3>
              <form onSubmit={onLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <Field label="Email Address" name="email" type="email" value={loginForm.email} onChange={handleLoginChange} placeholder="priya@example.com" required accent={ACCENT} />
                <Field label="Password" name="password" type="password" value={loginForm.password} onChange={handleLoginChange} placeholder="••••••••" required accent={ACCENT} />
                <ErrBox msg={error} />
                <button type="submit" disabled={loading}
                  style={{ padding: '0.875rem', borderRadius: '10px', border: 'none', background: ACCENT, color: '#fff', fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer', opacity: loading ? 0.7 : 1, fontFamily: 'inherit' }}>
                  {loading ? 'Signing in...' : 'Sign In as Volunteer →'}
                </button>
              </form>
              <div style={{ marginTop: '1.25rem', textAlign: 'center', paddingTop: '1.25rem', borderTop: '1px solid #f0fdf4' }}>
                <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
                  New volunteer?{' '}
                  <button onClick={() => { setShowReg(true); setError(''); }}
                    style={{ border: 'none', background: 'none', color: ACCENT, fontWeight: 700, cursor: 'pointer', fontSize: '0.85rem', fontFamily: 'inherit', textDecoration: 'underline' }}>
                    Register here
                  </button>
                </p>
              </div>
            </>
          ) : (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h3 style={{ fontWeight: 800, fontSize: '1.2rem', color: '#052e16', margin: 0 }}>Register as Volunteer</h3>
                <button onClick={() => { setShowReg(false); setError(''); }}
                  style={{ border: 'none', background: '#f1f5f9', color: '#64748b', cursor: 'pointer', fontSize: '0.85rem', padding: '0.3rem 0.7rem', borderRadius: '6px', fontFamily: 'inherit' }}>
                  ← Login
                </button>
              </div>
              <form onSubmit={onRegister} style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                <Field label="Full Name" name="name" value={regForm.name} onChange={handleRegChange} placeholder="Priya Sharma" required accent={ACCENT} />
                <Field label="Email" name="email" type="email" value={regForm.email} onChange={handleRegChange} placeholder="priya@example.com" required accent={ACCENT} />
                <Field label="Password" name="password" type="password" value={regForm.password} onChange={handleRegChange} placeholder="Min 6 characters" required accent={ACCENT} />
                <FieldSelect label="NGO to Join" name="ngo_name" value={regForm.ngo_name} onChange={handleRegChange} required accent={ACCENT}>
                  <option value="">Select an NGO…</option>
                  {ngoNames.map(n => <option key={n.id} value={n.name}>{n.name}</option>)}
                </FieldSelect>
                {ngoNames.length === 0 && <p style={{ fontSize: '0.75rem', color: '#d97706', margin: '-0.4rem 0 0' }}>⚠️ No approved NGOs found. Contact your admin.</p>}
                <Field label="Skills (comma-separated)" name="skills" value={regForm.skills} onChange={handleRegChange} placeholder="medical, logistics, first_aid" accent={ACCENT} />
                <ErrBox msg={error} />
                <button type="submit" disabled={loading}
                  style={{ padding: '0.875rem', borderRadius: '10px', border: 'none', background: ACCENT, color: '#fff', fontWeight: 700, cursor: 'pointer', opacity: loading ? 0.7 : 1, fontFamily: 'inherit' }}>
                  {loading ? 'Registering...' : 'Create Volunteer Account →'}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION 2 — NGO COORDINATOR
// ═══════════════════════════════════════════════════════════════════════════════
function NgoSection() {
  const ACCENT = '#7c3aed';
  const [showReg, setShowReg] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [regForm, setRegForm] = useState({ org_name: '', ngo_type: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleLoginChange = e => setLoginForm({ ...loginForm, [e.target.name]: e.target.value });
  const handleRegChange = e => setRegForm({ ...regForm, [e.target.name]: e.target.value });

  const onLogin = async e => {
    e.preventDefault(); setLoading(true); setError('');
    try { await doLogin(loginForm.email, loginForm.password); }
    catch (err) { setError(err.response?.data?.detail || 'Login failed'); }
    finally { setLoading(false); }
  };

  const onRegister = async e => {
    e.preventDefault(); setLoading(true); setError('');
    try {
      await axios.post(`${API_BASE}/auth/register`, {
        email: regForm.email, password: regForm.password, role: 'ngo',
        ngo_name: regForm.org_name, ngo_type: regForm.ngo_type,
      });
      setSuccess(true);
    } catch (err) { setError(err.response?.data?.detail || 'Registration failed'); }
    finally { setLoading(false); }
  };

  return (
    <section id="ngo" style={{ padding: '5rem 2rem', background: 'linear-gradient(135deg, #faf5ff 0%, #f5f3ff 100%)', borderTop: '4px solid #e9d5ff' }}>
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '3rem', alignItems: 'start' }}>

        {/* Left */}
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.35rem 0.875rem', borderRadius: '999px', background: '#ede9fe', color: ACCENT, fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.06em', marginBottom: '1.25rem' }}>
            🏢 FOR NGO COORDINATORS
          </div>
          <h2 style={{ fontSize: '2rem', fontWeight: 800, color: '#2e1065', marginBottom: '1rem', lineHeight: 1.2 }}>
            Coordinate your NGO.<br />Amplify your reach.
          </h2>
          <p style={{ color: '#6d28d9', lineHeight: 1.7, marginBottom: '1.75rem', fontSize: '0.95rem' }}>
            Register your NGO to gain access to volunteer management, AI-powered task assignment, shared resource pools, and cross-NGO coordination with the Admin.
          </p>
          <CapList accent={ACCENT} items={[
            'Manage volunteers — approve, reject, and track performance',
            'Receive tasks pushed by Admin, accept or reject them',
            'Auto-assign or manually assign volunteers to needs',
            'Request resources & borrow volunteers from the global pool',
            'View NGO-scoped analytics, leaderboard & task trails',
          ]} />
          <div style={{ marginTop: '2rem', padding: '1rem', borderRadius: '12px', background: '#ede9fe', border: '1px solid #e9d5ff' }}>
            <p style={{ fontSize: '0.82rem', color: '#6d28d9', margin: 0 }}>
              ⏳ <strong>Admin approval required:</strong> Your NGO registration will be reviewed by the system Admin before your account is activated.
            </p>
          </div>
        </div>

        {/* Right */}
        <div style={{ background: '#fff', borderRadius: '20px', border: '1.5px solid #e9d5ff', padding: '2rem', boxShadow: '0 8px 32px rgba(124,58,237,0.08)' }}>
          {success ? (
            <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏢</div>
              <h3 style={{ fontWeight: 800, color: '#0f172a', marginBottom: '0.5rem' }}>NGO Registration Submitted!</h3>
              <p style={{ color: '#64748b', lineHeight: 1.6, fontSize: '0.9rem' }}>Your NGO is pending Admin approval. You'll receive an email once your NGO is activated.</p>
              <button onClick={() => { setSuccess(false); setShowReg(false); setRegForm({ org_name: '', ngo_type: '', email: '', password: '' }); }}
                style={{ marginTop: '1.25rem', padding: '0.6rem 1.5rem', borderRadius: '8px', border: 'none', background: ACCENT, color: '#fff', cursor: 'pointer', fontWeight: 600, fontFamily: 'inherit' }}>
                Back to Login
              </button>
            </div>
          ) : !showReg ? (
            <>
              <h3 style={{ fontWeight: 800, fontSize: '1.2rem', color: '#2e1065', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ background: '#ede9fe', borderRadius: '8px', padding: '4px 8px', fontSize: '1.1rem' }}>🏢</span>
                NGO Coordinator Login
              </h3>
              <form onSubmit={onLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <Field label="Email Address" name="email" type="email" value={loginForm.email} onChange={handleLoginChange} placeholder="coordinator@ngo.org" required accent={ACCENT} />
                <Field label="Password" name="password" type="password" value={loginForm.password} onChange={handleLoginChange} placeholder="••••••••" required accent={ACCENT} />
                <ErrBox msg={error} />
                <button type="submit" disabled={loading}
                  style={{ padding: '0.875rem', borderRadius: '10px', border: 'none', background: ACCENT, color: '#fff', fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer', opacity: loading ? 0.7 : 1, fontFamily: 'inherit' }}>
                  {loading ? 'Signing in...' : 'Sign In as NGO Coordinator →'}
                </button>
              </form>
              <div style={{ marginTop: '1.25rem', textAlign: 'center', paddingTop: '1.25rem', borderTop: '1px solid #faf5ff' }}>
                <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
                  New NGO?{' '}
                  <button onClick={() => { setShowReg(true); setError(''); }}
                    style={{ border: 'none', background: 'none', color: ACCENT, fontWeight: 700, cursor: 'pointer', fontSize: '0.85rem', fontFamily: 'inherit', textDecoration: 'underline' }}>
                    Register your NGO
                  </button>
                </p>
              </div>
            </>
          ) : (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h3 style={{ fontWeight: 800, fontSize: '1.2rem', color: '#2e1065', margin: 0 }}>Register Your NGO</h3>
                <button onClick={() => { setShowReg(false); setError(''); }}
                  style={{ border: 'none', background: '#f1f5f9', color: '#64748b', cursor: 'pointer', fontSize: '0.85rem', padding: '0.3rem 0.7rem', borderRadius: '6px', fontFamily: 'inherit' }}>
                  ← Login
                </button>
              </div>
              <form onSubmit={onRegister} style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                <Field label="NGO / Organisation Name" name="org_name" value={regForm.org_name} onChange={handleRegChange} placeholder="HelpIndia Foundation" required accent={ACCENT} />
                <FieldSelect label="NGO Type" name="ngo_type" value={regForm.ngo_type} onChange={handleRegChange} required accent={ACCENT}>
                  <option value="">Select NGO type…</option>
                  {NGO_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </FieldSelect>
                <Field label="Coordinator Email" name="email" type="email" value={regForm.email} onChange={handleRegChange} placeholder="coordinator@ngo.org" required accent={ACCENT} />
                <Field label="Password" name="password" type="password" value={regForm.password} onChange={handleRegChange} placeholder="Min 6 characters" required accent={ACCENT} />
                <ErrBox msg={error} />
                <button type="submit" disabled={loading}
                  style={{ padding: '0.875rem', borderRadius: '10px', border: 'none', background: ACCENT, color: '#fff', fontWeight: 700, cursor: 'pointer', opacity: loading ? 0.7 : 1, fontFamily: 'inherit' }}>
                  {loading ? 'Submitting...' : 'Register NGO →'}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SECTION 3 — ADMIN
// ═══════════════════════════════════════════════════════════════════════════════
function AdminSection() {
  const ACCENT = '#1e40af';
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = e => setLoginForm({ ...loginForm, [e.target.name]: e.target.value });

  const onLogin = async e => {
    e.preventDefault(); setLoading(true); setError('');
    try { await doLogin(loginForm.email, loginForm.password); }
    catch (err) { setError(err.response?.data?.detail || 'Login failed. Contact your system administrator.'); }
    finally { setLoading(false); }
  };

  return (
    <section id="admin" style={{ padding: '5rem 2rem', background: 'linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%)', borderTop: '4px solid #bfdbfe' }}>
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '3rem', alignItems: 'start' }}>

        {/* Left */}
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.35rem 0.875rem', borderRadius: '999px', background: '#dbeafe', color: ACCENT, fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.06em', marginBottom: '1.25rem' }}>
            🛡️ FOR SYSTEM ADMINS
          </div>
          <h2 style={{ fontSize: '2rem', fontWeight: 800, color: '#0c1a4e', marginBottom: '1rem', lineHeight: 1.2 }}>
            Govern the platform.<br />Full system control.
          </h2>
          <p style={{ color: '#1e40af', lineHeight: 1.7, marginBottom: '1.75rem', fontSize: '0.95rem' }}>
            Admin accounts are pre-provisioned by the system. Login to access the global management dashboard — approve NGOs, assign tasks, manage inventory, and oversee the entire network.
          </p>
          <CapList accent={ACCENT} items={[
            'Approve or reject NGO registrations and profiles',
            'Assign crisis needs to one or multiple NGOs',
            'Manage global resource inventory and allocate to NGOs',
            'Approve volunteer pool requests across NGOs',
            'View system-wide analytics and BI dashboards',
          ]} />
          <div style={{ marginTop: '2rem', padding: '1rem', borderRadius: '12px', background: '#dbeafe', border: '1px solid #bfdbfe' }}>
            <p style={{ fontSize: '0.82rem', color: '#1e40af', margin: 0 }}>
              🔒 <strong>No self-registration:</strong> Admin accounts are created directly in the system. Contact your platform administrator if you need access.
            </p>
          </div>
        </div>

        {/* Right */}
        <div style={{ background: '#fff', borderRadius: '20px', border: '1.5px solid #bfdbfe', padding: '2rem', boxShadow: '0 8px 32px rgba(30,64,175,0.08)' }}>
          <h3 style={{ fontWeight: 800, fontSize: '1.2rem', color: '#0c1a4e', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ background: '#dbeafe', borderRadius: '8px', padding: '4px 8px', fontSize: '1.1rem' }}>🛡️</span>
            Admin Dashboard Login
          </h3>
          <form onSubmit={onLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <Field label="Admin Email" name="email" type="email" value={loginForm.email} onChange={handleChange} placeholder="admin@communitysync.org" required accent={ACCENT} />
            <Field label="Password" name="password" type="password" value={loginForm.password} onChange={handleChange} placeholder="••••••••" required accent={ACCENT} />
            <ErrBox msg={error} />
            <button type="submit" disabled={loading}
              style={{ padding: '0.875rem', borderRadius: '10px', border: 'none', background: `linear-gradient(135deg, ${ACCENT}, #1d4ed8)`, color: '#fff', fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer', opacity: loading ? 0.7 : 1, fontFamily: 'inherit', boxShadow: '0 4px 14px rgba(30,64,175,0.3)' }}>
              {loading ? 'Signing in...' : 'Access Admin Dashboard →'}
            </button>
          </form>
          <p style={{ marginTop: '1.25rem', fontSize: '0.8rem', color: '#94a3b8', textAlign: 'center' }}>
            Protected access · No self-registration available
          </p>
        </div>
      </div>
    </section>
  );
}
