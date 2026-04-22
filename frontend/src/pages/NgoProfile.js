import React, { useEffect, useState } from 'react';
import api from '../services/api';
import {
  Building2, Mail, Phone, MapPin, FileText, Calendar, CheckCircle,
  Clock, AlertCircle, Edit3, Save, X, Loader
} from 'lucide-react';

const STATUS_COLORS = {
  pending: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700', badge: 'bg-yellow-100 text-yellow-800' },
  approved: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', badge: 'bg-green-100 text-green-800' },
  rejected: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', badge: 'bg-red-100 text-red-800' },
  suspended: { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-700', badge: 'bg-gray-100 text-gray-800' },
};

const NGO_TYPE_LABELS = {
  disaster_relief: 'Disaster Relief',
  medical: 'Medical & Health',
  food_distribution: 'Food Distribution',
  education: 'Education',
  logistics: 'Logistics & Transport',
  shelter: 'Shelter & Housing',
  rehabilitation: 'Rehabilitation',
  water_sanitation: 'Water & Sanitation',
  child_welfare: 'Child Welfare',
  others: 'Others',
};

const NgoProfile = () => {
  const [ngoData, setNgoData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({});
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    fetchNgoProfile();
  }, []);

  const fetchNgoProfile = async () => {
    try {
      setLoading(true);
      setError('');
      const { data } = await api.get('/api/ngo/me/details');
      setNgoData(data);
      setFormData({
        name: data.name,
        ngo_type: data.ngo_type,
        registration_number: data.registration_number || '',
        description: data.description || '',
        location: data.location || '',
        contact_email: data.contact_email || '',
        contact_phone: data.contact_phone || '',
      });
    } catch (err) {
      console.error('Failed to fetch NGO profile:', err);
      setError(err.response?.data?.detail || 'Failed to load NGO profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError('');
      setSuccessMsg('');
      
      // Only send fields that can be updated
      const updatePayload = {
        name: formData.name,
        ngo_type: formData.ngo_type,
        registration_number: formData.registration_number || null,
        description: formData.description || null,
        location: formData.location || null,
        contact_email: formData.contact_email || null,
        contact_phone: formData.contact_phone || null,
      };

      const { data } = await api.put('/api/ngo/me/details', updatePayload);
      setNgoData(data);
      setIsEditing(false);
      setSuccessMsg('NGO profile updated successfully!');
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (err) {
      console.error('Failed to save NGO profile:', err);
      if (err.response?.status === 403) {
        setError('You do not have permission to edit this profile.');
      } else {
        setError(err.response?.data?.detail || 'Failed to save changes. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      name: ngoData.name,
      ngo_type: ngoData.ngo_type,
      registration_number: ngoData.registration_number || '',
      description: ngoData.description || '',
      location: ngoData.location || '',
      contact_email: ngoData.contact_email || '',
      contact_phone: ngoData.contact_phone || '',
    });
    setIsEditing(false);
    setError('');
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-12 bg-gray-200 rounded-lg w-1/3"></div>
          <div className="bg-white rounded-xl border border-gray-100 p-8 space-y-4">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="h-10 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!ngoData) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-xl p-8 text-center">
          <AlertCircle className="mx-auto mb-4 text-red-500" size={32} />
          <h2 className="text-lg font-semibold text-red-700 mb-2">NGO Profile Not Found</h2>
          <p className="text-red-600">
            {error || 'Unable to load your NGO profile. Please contact support if this persists.'}
          </p>
        </div>
      </div>
    );
  }

  const statusConfig = STATUS_COLORS[ngoData.status] || STATUS_COLORS.pending;
  const ngoTypeLabel = NGO_TYPE_LABELS[ngoData.ngo_type] || ngoData.ngo_type;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Building2 size={32} className="text-purple-600" />
            NGO Profile
          </h1>
          <p className="text-gray-500 mt-1">Manage your organization's information</p>
        </div>
        {!isEditing && (
          <button
            onClick={() => setIsEditing(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
          >
            <Edit3 size={18} /> Edit Profile
          </button>
        )}
      </div>

      {/* Status Banner */}
      <div className={`p-4 rounded-xl border ${statusConfig.border} ${statusConfig.bg}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {ngoData.status === 'approved' && <CheckCircle size={20} className="text-green-600" />}
            {ngoData.status === 'pending' && <Clock size={20} className="text-yellow-600" />}
            {ngoData.status === 'rejected' && <AlertCircle size={20} className="text-red-600" />}
            <div>
              <p className="font-semibold text-sm uppercase tracking-wider">Registration Status</p>
              <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold mt-1 ${statusConfig.badge}`}>
                {ngoData.status.charAt(0).toUpperCase() + ngoData.status.slice(1)}
              </span>
            </div>
          </div>
          {ngoData.admin_notes && (
            <div className="text-sm text-gray-600 text-right max-w-xs">
              <p className="font-semibold mb-1">Admin Notes:</p>
              <p className="italic">{ngoData.admin_notes}</p>
            </div>
          )}
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex gap-3">
          <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
          <p className="text-red-700">{error}</p>
        </div>
      )}
      {successMsg && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex gap-3">
          <CheckCircle className="text-green-600 flex-shrink-0" size={20} />
          <p className="text-green-700">{successMsg}</p>
        </div>
      )}

      {/* Main Profile Card */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="p-8 space-y-6">
          {/* Organization Name */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Organization Name</label>
            {isEditing ? (
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="Enter organization name"
              />
            ) : (
              <p className="text-lg font-semibold text-gray-900">{ngoData.name}</p>
            )}
          </div>

          {/* NGO Type */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Organization Type</label>
            {isEditing ? (
              <select
                name="ngo_type"
                value={formData.ngo_type}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              >
                {Object.entries(NGO_TYPE_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            ) : (
              <p className="text-gray-600 bg-purple-50 inline-block px-3 py-1.5 rounded-lg text-sm font-medium">
                {ngoTypeLabel}
              </p>
            )}
          </div>

          {/* Registration Number */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Registration Number</label>
            {isEditing ? (
              <input
                type="text"
                name="registration_number"
                value={formData.registration_number}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="Enter registration number (optional)"
              />
            ) : (
              <p className="text-gray-600">{ngoData.registration_number || '—'}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <FileText size={16} /> Description
            </label>
            {isEditing ? (
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={4}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="Enter organization description (optional)"
              />
            ) : (
              <p className="text-gray-600 whitespace-pre-wrap">
                {ngoData.description || '—'}
              </p>
            )}
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <MapPin size={16} /> Location
            </label>
            {isEditing ? (
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="Enter location (optional)"
              />
            ) : (
              <p className="text-gray-600">{ngoData.location || '—'}</p>
            )}
          </div>

          {/* Contact Email */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <Mail size={16} /> Contact Email
            </label>
            {isEditing ? (
              <input
                type="email"
                name="contact_email"
                value={formData.contact_email}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="Enter contact email (optional)"
              />
            ) : (
              <p className="text-gray-600">{ngoData.contact_email || '—'}</p>
            )}
          </div>

          {/* Contact Phone */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <Phone size={16} /> Contact Phone
            </label>
            {isEditing ? (
              <input
                type="tel"
                name="contact_phone"
                value={formData.contact_phone}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                placeholder="Enter contact phone (optional)"
              />
            ) : (
              <p className="text-gray-600">{ngoData.contact_phone || '—'}</p>
            )}
          </div>

          {/* Timestamps */}
          <div className="grid grid-cols-2 gap-6 pt-4 border-t border-gray-200">
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Created</p>
              <p className="text-sm text-gray-700">
                {new Date(ngoData.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Last Updated</p>
              <p className="text-sm text-gray-700">
                {new Date(ngoData.updated_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        {isEditing && (
          <div className="px-8 py-6 bg-gray-50 border-t border-gray-100 flex gap-3 justify-end">
            <button
              onClick={handleCancel}
              disabled={saving}
              className="px-6 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors font-semibold flex items-center gap-2"
            >
              <X size={18} /> Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? (
                <>
                  <Loader size={18} className="animate-spin" /> Saving...
                </>
              ) : (
                <>
                  <Save size={18} /> Save Changes
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Note */}
      {!isEditing && ngoData.status !== 'approved' && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <p className="text-sm text-blue-700">
            <strong>Note:</strong> Your organization is currently {ngoData.status}. Once approved by an administrator, 
            you'll be able to fully manage your NGO's operations.
          </p>
        </div>
      )}
    </div>
  );
};

export default NgoProfile;
