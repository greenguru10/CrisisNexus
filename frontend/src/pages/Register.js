import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';
import { UserPlus, CheckCircle } from 'lucide-react';

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

const Register = () => {
  const [email, setEmail]           = useState('');
  const [password, setPassword]     = useState('');
  const [role, setRole]             = useState('volunteer');

  // Volunteer-specific
  const [volunteerName, setVolunteerName] = useState('');
  const [ngoName, setNgoName]             = useState('');
  const [skills, setSkills]               = useState('');
  const [ngoOptions, setNgoOptions]       = useState([]);

  // NGO-specific
  const [ngoOrgName, setNgoOrgName] = useState('');
  const [ngoType, setNgoType]       = useState('');

  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState('');
  const [pendingApproval, setPendingApproval] = useState(false);
  const [pendingType, setPendingType]   = useState('volunteer');
  const navigate = useNavigate();

  // Load approved NGO list when volunteer role is selected
  useEffect(() => {
    if (role === 'volunteer') {
      api.get('/api/ngo/names')
        .then(r => setNgoOptions(r.data))
        .catch(() => setNgoOptions([]));
    }
  }, [role]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (role === 'volunteer') {
        if (!ngoName) { setError('Please select an NGO to join.'); setLoading(false); return; }
        const skillsArray = skills ? skills.split(',').map(s => s.trim()).filter(Boolean) : [];
        await api.post('/auth/register', {
          email, password, role,
          volunteer_name: volunteerName,
          ngo_name: ngoName,
          skills: skillsArray,
        });
        setPendingType('volunteer');
        setPendingApproval(true);
        return;
      }

      if (role === 'ngo') {
        if (!ngoOrgName) { setError('Please enter your NGO name.'); setLoading(false); return; }
        if (!ngoType) { setError('Please select the NGO type.'); setLoading(false); return; }
        await api.post('/auth/register', {
          email, password, role,
          ngo_name: ngoOrgName,
          ngo_type: ngoType,
        });
        setPendingType('ngo');
        setPendingApproval(true);
        return;
      }

      // Admin (no extra fields)
      await api.post('/auth/register', { email, password, role });
      const { data } = await api.post('/auth/login', { email, password });
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('role', data.role);
      window.location.href = '/dashboard';

    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  // ── Pending approval screen ──────────────────────────────────────────
  if (pendingApproval) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <div className="max-w-md w-full mx-4">
          <div className="bg-white rounded-2xl shadow-xl shadow-blue-500/10 p-8 border border-gray-100 text-center">
            <div className="w-16 h-16 bg-amber-100 text-amber-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <CheckCircle size={28} />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              {pendingType === 'ngo' ? 'NGO Registered!' : 'Account Created!'}
            </h1>
            <p className="text-gray-500 mb-6">
              {pendingType === 'ngo' ? 'Your NGO is awaiting Admin approval.' : 'Your account is under review by the NGO Coordinator.'}
            </p>
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
              <p className="text-amber-800 text-sm font-medium mb-1">⏳ Pending Approval</p>
              <p className="text-amber-700 text-sm">
                {pendingType === 'ngo'
                  ? 'An Admin will review and activate your NGO. Check your email for updates.'
                  : 'An NGO Coordinator will review your request. You\'ll receive an email once approved.'}
              </p>
            </div>
            <Link to="/login" className="inline-block w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl shadow-lg shadow-blue-600/20 transition-all text-center">
              Back to Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // ── Registration form ────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-indigo-50 py-8">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-2xl shadow-xl shadow-blue-500/10 p-8 border border-gray-100">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-green-100 text-green-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <UserPlus size={28} />
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Create Account</h1>
            <p className="text-gray-500 mt-2">Join CommunitySync today</p>
          </div>

          {error && (
            <div className="mb-5 p-3 bg-red-50 border border-red-100 text-red-600 text-sm rounded-lg">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Role selector */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">I am a…</label>
              <select value={role} onChange={e => { setRole(e.target.value); setError(''); }}
                className="block w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none">
                <option value="volunteer">Volunteer</option>
                <option value="ngo">NGO Coordinator</option>
              </select>
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                className="block w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
                placeholder="you@example.com" required />
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                className="block w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
                placeholder="Minimum 6 characters" minLength={6} required />
            </div>

            {/* ── Volunteer fields ── */}
            {role === 'volunteer' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                  <input type="text" value={volunteerName} onChange={e => setVolunteerName(e.target.value)}
                    className="block w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
                    placeholder="Priya Sharma" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">NGO to Join *</label>
                  <select value={ngoName} onChange={e => setNgoName(e.target.value)} required
                    className="block w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none">
                    <option value="">Select an NGO…</option>
                    {ngoOptions.map(n => <option key={n.id} value={n.name}>{n.name}</option>)}
                  </select>
                  {ngoOptions.length === 0 && (
                    <p className="text-xs text-amber-600 mt-1">⚠️ No approved NGOs yet. Contact your admin.</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Skills (comma-separated)</label>
                  <input type="text" value={skills} onChange={e => setSkills(e.target.value)}
                    className="block w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
                    placeholder="e.g. medical, logistics, first_aid" />
                </div>
                <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
                  <p className="text-blue-700 text-sm">ℹ️ Volunteer accounts require NGO Coordinator approval before you can log in.</p>
                </div>
              </>
            )}

            {/* ── NGO Coordinator fields ── */}
            {role === 'ngo' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">NGO / Organisation Name *</label>
                  <input type="text" value={ngoOrgName} onChange={e => setNgoOrgName(e.target.value)}
                    className="block w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
                    placeholder="HelpIndia Foundation" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">NGO Type *</label>
                  <select value={ngoType} onChange={e => setNgoType(e.target.value)} required
                    className="block w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none">
                    <option value="">Select NGO type…</option>
                    {NGO_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>
                <div className="bg-purple-50 border border-purple-100 rounded-lg p-3">
                  <p className="text-purple-700 text-sm">ℹ️ NGO registrations require Admin approval before your account is activated.</p>
                </div>
              </>
            )}

            <button type="submit" disabled={loading}
              className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl shadow-lg shadow-blue-600/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
              {loading ? 'Creating account…' : 'Create Account'}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-blue-600 font-semibold hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
