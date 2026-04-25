import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Trophy, Medal, Award, Star } from 'lucide-react';

const API = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
const auth = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
const userRole = () => localStorage.getItem('role');

export default function Leaderboard() {
  const isAdmin = userRole() === 'admin';
  const ngoId   = localStorage.getItem('ngo_id');
  const ngoName = localStorage.getItem('ngo_name');

  const [ngoOptions, setNgoOptions]   = useState([]);
  const [ngoFilter, setNgoFilter]     = useState(ngoId || '');
  const [data, setData]               = useState(null);
  const [loading, setLoading]         = useState(true);

  // Fetch NGO names for admin filter dropdown
  useEffect(() => {
    if (isAdmin) {
      axios.get(`${API}/api/ngo/names`, auth()).then(r => setNgoOptions(r.data)).catch(() => {});
    }
  }, [isAdmin]);

  const fetchLeaderboard = async (id) => {
    setLoading(true);
    try {
      const params = id ? `?ngo_id=${id}` : '';
      const lb = await axios.get(`${API}/api/gamification/leaderboard${params}`, auth());
      setData(lb.data);
    } catch { }
    setLoading(false);
  };

  useEffect(() => { fetchLeaderboard(ngoFilter); }, [ngoFilter]);

  const getTier = (points) => {
    if (points >= 1000) return { name: 'Platinum', color: 'from-slate-300 to-slate-500 text-slate-800' };
    if (points >= 500) return { name: 'Gold', color: 'from-yellow-300 to-yellow-500 text-yellow-900' };
    if (points >= 200) return { name: 'Silver', color: 'from-gray-300 to-gray-400 text-gray-800' };
    return { name: 'Bronze', color: 'from-orange-300 to-orange-500 text-orange-900' };
  };

  const top3 = data?.leaderboard?.slice(0, 3) || [];
  const rest = data?.leaderboard?.slice(3) || [];

  return (
    <div className="font-sans text-slate-900 max-w-6xl mx-auto animate-fade-in-up">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 flex items-center gap-3 tracking-tight">
            <Trophy className="text-yellow-500" size={32} />
            Volunteer Leaderboard
          </h1>
          <p className="text-slate-500 font-medium mt-1">NGO-scoped volunteer rankings by tasks completed and performance.</p>
        </div>

        {/* Admin NGO filter */}
        {isAdmin && (
          <div className="flex items-center gap-3 bg-white p-2 rounded-2xl border border-slate-200 shadow-sm">
            <label className="text-sm font-bold text-slate-500 ml-2">Filter:</label>
            <select
              value={ngoFilter}
              onChange={e => setNgoFilter(e.target.value)}
              className="bg-slate-50 border-none outline-none py-2 px-4 rounded-xl text-sm font-semibold cursor-pointer w-48 text-slate-700 focus:ring-2 focus:ring-indigo-500/30"
            >
              <option value="">🌐 Global (All NGOs)</option>
              {ngoOptions.map(n => (
                <option key={n.id} value={n.id}>{n.name}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* NGO context banner */}
      {(ngoName && !isAdmin) || (isAdmin && ngoFilter) ? (
        <div className="bg-indigo-50 border border-indigo-100 text-indigo-700 px-5 py-3 rounded-xl mb-8 flex items-center gap-3 shadow-sm">
          <span className="text-xl">🏢</span>
          <span className="font-medium text-sm">
            Showing leaderboard for: <strong>
              {isAdmin 
                ? (ngoOptions.find(n => String(n.id) === String(ngoFilter))?.name || `NGO #${ngoFilter}`)
                : ngoName}
            </strong>
          </span>
        </div>
      ) : null}

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-indigo-200 border-t-indigo-600"></div>
        </div>
      ) : (
        <>
          {data?.leaderboard?.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-3xl p-16 text-center shadow-sm">
              <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4">
                <Trophy className="text-slate-300" size={40} />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">No Rankings Yet</h3>
              <p className="text-slate-500">Volunteers need to complete tasks to earn points and appear on the leaderboard.</p>
            </div>
          ) : (
            <div className="space-y-12">
              {/* TOP 3 PODIUM */}
              {top3.length > 0 && (
                <div className="flex flex-col md:flex-row items-end justify-center gap-6 pt-10 px-4">
                  {/* 2nd Place */}
                  {top3[1] && (
                    <div className="flex-1 w-full md:w-auto order-2 md:order-1 flex flex-col items-center animate-fade-in" style={{animationDelay: '0.2s'}}>
                      <div className="bg-white border-2 border-slate-200 rounded-3xl p-6 w-full max-w-[280px] shadow-lg text-center relative z-10 hover:-translate-y-2 transition-transform duration-300">
                        <div className="absolute -top-6 left-1/2 -translate-x-1/2 w-12 h-12 bg-slate-200 rounded-full flex items-center justify-center border-4 border-white shadow-sm">
                          <span className="text-xl">🥈</span>
                        </div>
                        <h3 className="font-extrabold text-slate-900 text-lg mt-4 truncate">{top3[1].name}</h3>
                        <p className="text-sm font-semibold text-slate-500 mb-4">{top3[1].points} pts</p>
                        <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-slate-200 to-slate-300 rounded-full text-xs font-bold text-slate-700 shadow-sm">
                          <Medal size={14} /> Silver Tier
                        </div>
                      </div>
                      <div className="w-[80%] h-16 bg-gradient-to-b from-slate-200 to-slate-100 rounded-t-xl mt-4 border-x border-t border-slate-200/50 hidden md:block"></div>
                    </div>
                  )}

                  {/* 1st Place */}
                  <div className="flex-1 w-full md:w-auto order-1 md:order-2 flex flex-col items-center animate-fade-in">
                    <div className="bg-gradient-to-b from-yellow-50 to-white border-2 border-yellow-300 rounded-3xl p-8 w-full max-w-[320px] shadow-2xl shadow-yellow-500/20 text-center relative z-20 hover:-translate-y-2 transition-transform duration-300 scale-105">
                      <div className="absolute -top-8 left-1/2 -translate-x-1/2 w-16 h-16 bg-gradient-to-br from-yellow-300 to-yellow-500 rounded-full flex items-center justify-center border-4 border-white shadow-lg text-white">
                        <span className="text-3xl drop-shadow-md">🥇</span>
                      </div>
                      <h3 className="font-black text-slate-900 text-xl mt-6 truncate">{top3[0].name}</h3>
                      <p className="text-base font-bold text-yellow-600 mb-4">{top3[0].points} pts</p>
                      <div className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-gradient-to-r from-yellow-400 to-amber-500 rounded-full text-xs font-black text-white shadow-md">
                        <Trophy size={14} /> Gold Tier
                      </div>
                      <div className="mt-4 flex items-center justify-center gap-3 text-xs font-semibold text-slate-600 bg-white/50 py-2 rounded-xl border border-yellow-200/50">
                        <span className="flex items-center gap-1"><CheckCircle2 size={14} className="text-emerald-500"/> {top3[0].tasks_completed} Tasks</span>
                        <span className="flex items-center gap-1"><Star size={14} className="text-yellow-500"/> {top3[0].rating?.toFixed(1) || '—'}</span>
                      </div>
                    </div>
                    <div className="w-[80%] h-24 bg-gradient-to-b from-yellow-200 to-yellow-100 rounded-t-xl mt-4 border-x border-t border-yellow-300/50 hidden md:block"></div>
                  </div>

                  {/* 3rd Place */}
                  {top3[2] && (
                    <div className="flex-1 w-full md:w-auto order-3 flex flex-col items-center animate-fade-in" style={{animationDelay: '0.4s'}}>
                      <div className="bg-white border-2 border-orange-200 rounded-3xl p-6 w-full max-w-[280px] shadow-lg text-center relative z-10 hover:-translate-y-2 transition-transform duration-300">
                        <div className="absolute -top-6 left-1/2 -translate-x-1/2 w-12 h-12 bg-orange-200 rounded-full flex items-center justify-center border-4 border-white shadow-sm">
                          <span className="text-xl">🥉</span>
                        </div>
                        <h3 className="font-extrabold text-slate-900 text-lg mt-4 truncate">{top3[2].name}</h3>
                        <p className="text-sm font-semibold text-orange-600 mb-4">{top3[2].points} pts</p>
                        <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-orange-300 to-orange-400 rounded-full text-xs font-bold text-orange-900 shadow-sm">
                          <Award size={14} /> Bronze Tier
                        </div>
                      </div>
                      <div className="w-[80%] h-10 bg-gradient-to-b from-orange-200 to-orange-100 rounded-t-xl mt-4 border-x border-t border-orange-200/50 hidden md:block"></div>
                    </div>
                  )}
                </div>
              )}

              {/* REST OF THE LIST */}
              {rest.length > 0 && (
                <div className="bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-sm">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                          <th className="py-4 px-6 font-semibold">Rank</th>
                          <th className="py-4 px-6 font-semibold">Volunteer</th>
                          <th className="py-4 px-6 font-semibold">Tier</th>
                          <th className="py-4 px-6 font-semibold text-right">Points</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {rest.map((v, i) => {
                          const rank = i + 4;
                          const tier = getTier(v.points);
                          return (
                            <tr key={v.volunteer_id} className="hover:bg-slate-50 transition-colors group">
                              <td className="py-4 px-6">
                                <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-sm font-bold text-slate-500 group-hover:bg-indigo-100 group-hover:text-indigo-600 transition-colors">
                                  #{rank}
                                </div>
                              </td>
                              <td className="py-4 px-6">
                                <div className="font-bold text-slate-900">{v.name}</div>
                                <div className="text-xs font-medium text-slate-500 flex items-center gap-2 mt-0.5">
                                  <span>{v.tasks_completed} tasks</span> •
                                  <span>⭐ {v.rating?.toFixed(1) || '—'}</span>
                                </div>
                              </td>
                              <td className="py-4 px-6">
                                <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-gradient-to-r ${tier.color} shadow-sm`}>
                                  {tier.name}
                                </span>
                              </td>
                              <td className="py-4 px-6 text-right font-black text-slate-700 text-lg">
                                {v.points}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// Temporary shim for lucide icons missing above
function CheckCircle2(props) {
  return <svg xmlns="http://www.w3.org/2000/svg" width={props.size||24} height={props.size||24} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={props.className}><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg>;
}
