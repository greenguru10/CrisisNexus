import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Mail, Lock, Phone, MapPin, CheckCircle, AlertTriangle, Save, Eye, EyeOff, Shield, Edit3, Star } from 'lucide-react';

const roleConfig = {
  admin: { label: 'Administrator', color: 'bg-red-100 text-red-700 border-red-200', dot: 'bg-red-500' },
  ngo: { label: 'NGO Partner', color: 'bg-purple-100 text-purple-700 border-purple-200', dot: 'bg-purple-500' },
  volunteer: { label: 'Volunteer', color: 'bg-green-100 text-green-700 border-green-200', dot: 'bg-green-500' },
};

const InputField = ({ icon: Icon, label, type = 'text', value, onChange, placeholder, hint, rightElement }) => (
  <div className="group">
    <label className="block text-sm font-semibold text-gray-600 mb-2">{label}</label>
    <div className="relative">
      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
        <Icon size={17} className="text-gray-400 group-focus-within:text-blue-500 transition-colors" />
      </div>
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="block w-full pl-11 pr-12 py-3.5 bg-gray-50 border border-gray-200 rounded-xl
                   focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:bg-white
                   outline-none transition-all text-gray-800 placeholder-gray-400 text-sm"
      />
      {rightElement && (
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center">{rightElement}</div>
      )}
    </div>
    {hint && <p className="mt-1.5 text-xs text-gray-400">{hint}</p>}
  </div>
);

const Profile = () => {
  const role = localStorage.getItem('role') || 'volunteer';
  const rc = roleConfig[role] || roleConfig.volunteer;

  const [profile, setProfile] = useState({ email: '', mobile_number: '', location: '', skills: '' });
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  // derive initials from email
  const initials = profile.email ? profile.email.slice(0, 2).toUpperCase() : '??';

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const { data } = await api.get('/auth/me');
        setProfile({
          email: data.email || '',
          mobile_number: data.mobile_number || '',
          location: data.location || '',
          skills: data.skills ? data.skills.join(', ') : '',
        });
      } catch (err) {
        console.error('Failed to fetch profile', err);
      } finally {
        setFetching(false);
      }
    };
    fetchProfile();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess(false);
    try {
      const updateData = {
        email: profile.email,
        mobile_number: profile.mobile_number,
        location: profile.location,
      };
      if (role === 'volunteer') {
        updateData.skills = profile.skills.split(',').map(s => s.trim()).filter(Boolean);
      }
      if (password) updateData.password = password;
      await api.put('/auth/me', updateData);
      setSuccess(true);
      setPassword('');
      setTimeout(() => setSuccess(false), 4000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile.');
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return (
      <div className="max-w-2xl mx-auto space-y-4 animate-pulse">
        <div className="h-8 bg-gray-200 rounded-lg w-48"></div>
        <div className="bg-white rounded-2xl border border-gray-100 p-8 space-y-4">
          <div className="flex gap-4 items-center">
            <div className="w-20 h-20 bg-gray-200 rounded-full"></div>
            <div className="space-y-2 flex-1">
              <div className="h-5 bg-gray-200 rounded w-40"></div>
              <div className="h-4 bg-gray-100 rounded w-24"></div>
            </div>
          </div>
          {[1,2,3,4].map(i => <div key={i} className="h-12 bg-gray-100 rounded-xl"></div>)}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Profile Settings</h1>
        <p className="text-gray-500 text-sm mt-1">Manage your personal information and account security</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Avatar + identity card */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center gap-5">
            {/* Avatar */}
            <div className="relative">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
                <span className="text-2xl font-bold text-white">{initials}</span>
              </div>
              <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-white rounded-full border-2 border-white shadow flex items-center justify-center">
                <Edit3 size={11} className="text-blue-500" />
              </div>
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <p className="font-bold text-gray-900 text-lg truncate">{profile.email}</p>
              <div className="flex items-center gap-2 mt-1.5">
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${rc.color}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${rc.dot}`}></span>
                  {rc.label}
                </span>
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-600 border border-gray-200">
                  <Shield size={10} /> Active
                </span>
              </div>
              {profile.location && (
                <p className="text-xs text-gray-400 mt-1.5 flex items-center gap-1">
                  <MapPin size={11} /> {profile.location}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-100 rounded-xl animate-fade-in">
            <AlertTriangle size={18} className="text-red-500 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
        {success && (
          <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-100 rounded-xl animate-fade-in">
            <CheckCircle size={18} className="text-green-500 flex-shrink-0" />
            <p className="text-sm text-green-700 font-medium">Profile updated successfully!</p>
          </div>
        )}

        {/* Fields card */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-5">
          <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider">Account Information</h2>

          <InputField
            icon={Mail}
            label="Email Address"
            type="email"
            value={profile.email}
            onChange={(e) => setProfile(p => ({ ...p, email: e.target.value }))}
            placeholder="you@example.com"
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <InputField
              icon={Phone}
              label="Mobile Number"
              type="tel"
              value={profile.mobile_number}
              onChange={(e) => setProfile(p => ({ ...p, mobile_number: e.target.value }))}
              placeholder="+91 98765 43210"
            />
            <InputField
              icon={MapPin}
              label="Location"
              value={profile.location}
              onChange={(e) => setProfile(p => ({ ...p, location: e.target.value }))}
              placeholder="Mumbai, India"
            />
          </div>

          {role === 'volunteer' && (
            <InputField
              icon={Star}
              label="Skills (comma separated)"
              value={profile.skills}
              onChange={(e) => setProfile(p => ({ ...p, skills: e.target.value }))}
              placeholder="e.g. medical, language translation, logistics"
            />
          )}
        </div>

        {/* Password card */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-5">
          <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider">Change Password</h2>
          <InputField
            icon={Lock}
            label="New Password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Leave blank to keep current"
            hint="Must be at least 6 characters"
            rightElement={
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            }
          />
        </div>

        {/* Submit */}
        <div className="flex justify-end pb-4">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2.5 px-7 py-3.5 bg-blue-600 text-white font-semibold
                       rounded-xl shadow-lg shadow-blue-600/25 hover:bg-blue-700 active:scale-95
                       disabled:opacity-60 disabled:cursor-not-allowed transition-all text-sm"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Saving...
              </>
            ) : (
              <>
                <Save size={16} />
                Save Changes
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default Profile;
