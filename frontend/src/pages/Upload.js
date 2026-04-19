import React, { useState } from 'react';
import api from '../services/api';
import { Upload as UploadIcon, FileText, CheckCircle, AlertTriangle, File } from 'lucide-react';

const Upload = () => {
  const [mode, setMode] = useState('text'); // 'text' or 'file'
  const [rawText, setRawText] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleTextSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const { data } = await api.post('/api/upload-report', { raw_text: rawText });
      setResult(data);
      setRawText('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process report');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post('/api/upload-file', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(data);
      setFile(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process file');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      <header>
        <h1 className="text-2xl font-bold text-gray-900">Upload Report</h1>
        <p className="text-gray-500">Submit an NGO survey report for NLP processing</p>
      </header>

      {/* Mode Toggle */}
      <div className="flex gap-2 bg-gray-100 p-1 rounded-xl w-fit">
        <button
          onClick={() => setMode('text')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            mode === 'text' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <span className="flex items-center gap-2"><FileText size={16} /> Paste Text</span>
        </button>
        <button
          onClick={() => setMode('file')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            mode === 'file' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <span className="flex items-center gap-2"><File size={16} /> Upload File</span>
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-100 rounded-xl flex items-start gap-3">
          <AlertTriangle className="text-red-500 mt-0.5" size={18} />
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {/* Text Mode */}
      {mode === 'text' && (
        <form onSubmit={handleTextSubmit} className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Survey Report Text</label>
          <textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            rows={8}
            className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none resize-none"
            placeholder="Paste the NGO survey report here...&#10;&#10;Example: Urgent need for medical supplies in Mumbai. 500 families affected by flooding. Clean drinking water shortage."
            required
            minLength={20}
          />
          <p className="text-xs text-gray-400 mt-2">Minimum 20 characters required</p>
          <button
            type="submit"
            disabled={loading || rawText.length < 20}
            className="mt-4 px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-all shadow-sm shadow-blue-600/20"
          >
            {loading ? 'Processing...' : 'Analyze Report'}
          </button>
        </form>
      )}

      {/* File Mode */}
      {mode === 'file' && (
        <form onSubmit={handleFileSubmit} className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">Upload PDF, DOCX, or TXT</label>
          <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center hover:border-blue-400 transition-colors">
            <UploadIcon className="mx-auto text-gray-400 mb-3" size={32} />
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(e) => setFile(e.target.files[0])}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-600 file:font-medium hover:file:bg-blue-100 cursor-pointer"
            />
            {file && (
              <p className="mt-3 text-sm text-green-600 font-medium">
                Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </p>
            )}
          </div>
          <button
            type="submit"
            disabled={loading || !file}
            className="mt-4 px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-all shadow-sm shadow-blue-600/20"
          >
            {loading ? 'Processing...' : 'Upload & Analyze'}
          </button>
        </form>
      )}

      {/* Result */}
      {result && (
        <div className="bg-white rounded-xl border border-green-100 shadow-sm p-6 animate-slide-up">
          <div className="flex items-center gap-3 mb-4">
            <CheckCircle className="text-green-600" size={24} />
            <h3 className="text-lg font-semibold text-gray-900">Report Processed Successfully</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-400 uppercase font-bold">Category</p>
              <p className="text-sm font-semibold text-gray-900 capitalize mt-1">{result.category}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-400 uppercase font-bold">Urgency</p>
              <p className="text-sm font-semibold text-gray-900 capitalize mt-1">{result.urgency}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-400 uppercase font-bold">People Affected</p>
              <p className="text-sm font-semibold text-gray-900 mt-1">{result.people_affected}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-400 uppercase font-bold">Location</p>
              <p className="text-sm font-semibold text-gray-900 mt-1">{result.location || 'N/A'}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-400 uppercase font-bold">Priority Score</p>
              <p className="text-sm font-semibold text-blue-600 mt-1">{result.priority_score?.toFixed(1)}/100</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-400 uppercase font-bold">Status</p>
              <p className="text-sm font-semibold text-amber-600 capitalize mt-1">{result.status}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Upload;
