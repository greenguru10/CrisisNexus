import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { CheckCircle, Play, CheckCircle2, Star, MessageSquare } from 'lucide-react';

const VolunteerTasks = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [completingTask, setCompletingTask] = useState(null);
  const [processing, setProcessing] = useState(null);
  const [feedback, setFeedback] = useState({ rating: 5, comments: '' });

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const { data } = await api.get('/api/task/my-tasks');
      setTasks(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (id, action) => {
    setProcessing(id);
    try {
      await api.post(`/api/task/${id}/${action}`);
      await fetchTasks();
    } catch (err) {
      alert(err.response?.data?.detail || `Failed to ${action} task`);
    } finally {
      setProcessing(null);
    }
  };

  const handleComplete = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/api/task/${completingTask}/complete`, {
        feedback_rating: parseFloat(feedback.rating),
        feedback_comments: feedback.comments
      });
      setCompletingTask(null);
      fetchTasks();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to complete task');
    }
  };

  if (loading) return <div className="p-8 text-center text-gray-500 blur-sm animate-pulse">Loading Tasks...</div>;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">My Assignments</h1>
        <p className="text-gray-500 text-sm">Manage your active and past crisis tasks here.</p>
      </div>

      {tasks.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p>No tasks assigned yet. You'll be notified when you're needed!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tasks.map(task => (
            <div key={task.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 flex flex-col justify-between hover:shadow-md transition-all">
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
                  <div className="flex flex-col gap-1">
                    <span className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-xs font-bold uppercase tracking-wider w-fit">
                      {task.category}
                    </span>
                    {task.is_global_pool && (
                      <span className="px-3 py-1 bg-amber-50 text-amber-600 border border-amber-200 rounded-full text-[10px] font-extrabold uppercase tracking-widest w-fit">
                        🌍 Globally Assigned by Admin
                      </span>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-1.5">
                    <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wide ${
                      task.status === 'completed' ? 'bg-green-100 text-green-700' :
                      task.status === 'in_progress' ? 'bg-purple-100 text-purple-700 animate-pulse' :
                      task.status === 'accepted' ? 'bg-indigo-100 text-indigo-700' :
                      'bg-amber-100 text-amber-700'
                    }`}>
                      {task.status.replace('_', ' ')}
                    </span>
                    {task.status === 'completed' && (
                      <span className="text-xs font-black text-amber-600 flex items-center gap-0.5" title="Points earned for this task">
                        ⭐ {task.is_global_pool ? '+11' : '+10'} pts
                      </span>
                    )}
                  </div>
                </div>
                
                <h3 className="font-bold text-gray-900 text-lg mb-1">{task.location || 'Unknown Location'}</h3>
                <p className="text-gray-500 text-sm mb-4 line-clamp-3">{task.raw_text}</p>
                
                <div className="flex justify-between text-xs font-semibold text-gray-400 mb-6">
                  <span>Urgency: <span className="text-gray-700 uppercase">{task.urgency}</span></span>
                  <span>People: <span className="text-gray-700">{task.people_affected}</span></span>
                </div>
              </div>

              {/* ACTION BUTTONS */}
              <div className="pt-4 border-t border-gray-100">
                {task.status === 'assigned' || task.status === 'pending' ? (
                  <button disabled={processing === task.id} onClick={() => handleAction(task.id, 'accept')} className="w-full py-2.5 bg-blue-600 text-white rounded-lg font-bold flex justify-center items-center gap-2 hover:bg-blue-700 disabled:opacity-50 transition-all">
                    <CheckCircle size={18} /> {processing === task.id ? 'Processing...' : 'Accept Assignment'}
                  </button>
                ) : task.status === 'accepted' ? (
                  <button disabled={processing === task.id} onClick={() => handleAction(task.id, 'start')} className="w-full py-2.5 bg-indigo-600 text-white rounded-lg font-bold flex justify-center items-center gap-2 hover:bg-indigo-700 disabled:opacity-50 transition-all">
                    <Play size={18} /> {processing === task.id ? 'Processing...' : 'Make In-Progress'}
                  </button>
                ) : (task.status === 'in_progress' || task.status === 'accepted') && task.my_ngo_completed ? (
                  <div className="w-full py-2.5 bg-blue-50 text-blue-500 rounded-lg font-bold flex justify-center items-center gap-2 border border-blue-100">
                    <CheckCircle2 size={18} /> Waiting for other NGOs
                  </div>
                ) : task.status === 'in_progress' ? (
                  <button disabled={processing === task.id} onClick={() => setCompletingTask(task.id)} className="w-full py-2.5 bg-green-600 text-white rounded-lg font-bold flex justify-center items-center gap-2 hover:bg-green-700 disabled:opacity-50 transition-all">
                    <CheckCircle2 size={18} /> Complete Task
                  </button>
                ) : (
                  <div className="w-full py-2.5 bg-gray-50 text-gray-400 rounded-lg font-bold flex justify-center items-center gap-2">
                    <CheckCircle2 size={18} /> Finished
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* COMPLETION MODAL */}
      {completingTask && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl">
            <h3 className="text-xl font-bold text-gray-900 mb-2">Complete Task</h3>
            <p className="text-gray-500 text-sm mb-6">Great job! How did it go?</p>
            
            <form onSubmit={handleComplete} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center gap-1">
                  <Star size={16}/> Rate Experience (1-5)
                </label>
                <input 
                  type="number" min="1" max="5" step="0.5" required
                  value={feedback.rating} 
                  onChange={e => setFeedback({ ...feedback, rating: e.target.value })} 
                  className="w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2 flex items-center gap-1">
                  <MessageSquare size={16}/> Comments
                </label>
                <textarea 
                  value={feedback.comments} 
                  onChange={e => setFeedback({ ...feedback, comments: e.target.value })} 
                  className="w-full px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-green-500 min-h-[100px]"
                  placeholder="Any issues faced?"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button type="button" onClick={() => setCompletingTask(null)} className="flex-1 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-semibold">Cancel</button>
                <button type="submit" className="flex-1 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold shadow-sm">Submit</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default VolunteerTasks;
