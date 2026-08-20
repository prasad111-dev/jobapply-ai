'use client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { FiUsers, FiCheckCircle, FiBriefcase, FiLayers, FiShield, FiUser, FiMail, FiPhone, FiMapPin, FiGlobe, FiArrowLeft, FiSearch, FiClock, FiUpload, FiActivity } from 'react-icons/fi';

const api = axios.create({ baseURL: '/api' });

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    if (error.response?.status === 403 && typeof window !== 'undefined') {
      window.location.href = '/dashboard';
    }
    return Promise.reject(error);
  }
);

export default function AdminPage() {
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [notAdmin, setNotAdmin] = useState(false);
  const [query, setQuery] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      window.location.href = '/login';
      return;
    }
    Promise.all([
      api.get('/admin/stats'),
      api.get('/admin/users', { params: { limit: 100 } }),
    ]).then(([s, u]) => {
      setStats(s.data);
      setUsers(u.data);
    }).catch((err) => {
      if (err.response?.status === 403) setNotAdmin(true);
    }).finally(() => setLoading(false));
  }, []);

  const loadUser = async (id: number) => {
    try {
      const r = await api.get(`/admin/users/${id}`);
      setSelected(r.data);
    } catch { toast.error('Failed to load user'); }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-slate-400 flex items-center gap-2"><FiActivity className="animate-pulse" /> Loading admin panel...</div>
      </div>
    );
  }

  if (notAdmin) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-24 text-center">
        <FiShield className="text-5xl text-rose-400 mx-auto mb-4" />
        <h1 className="text-2xl font-bold mb-2">Admin access required</h1>
        <p className="text-slate-400 mb-6">You don't have permission to view this panel.</p>
        <a href="/dashboard" className="btn-primary px-6 py-2.5">Back to Dashboard</a>
      </div>
    );
  }

  const filtered = query
    ? users.filter(u =>
        (u.username || '').toLowerCase().includes(query.toLowerCase()) ||
        (u.email || '').toLowerCase().includes(query.toLowerCase()) ||
        (u.full_name || '').toLowerCase().includes(query.toLowerCase()))
    : users;

  const statCards = [
    { label: 'Total Users', value: stats?.total_users || 0, icon: <FiUsers />, color: 'blue' },
    { label: 'Active Users', value: stats?.active_users || 0, icon: <FiCheckCircle />, color: 'green' },
    { label: 'Applications', value: stats?.total_applications || 0, icon: <FiBriefcase />, color: 'purple' },
    { label: 'Jobs Scraped', value: stats?.total_jobs || 0, icon: <FiLayers />, color: 'yellow' },
    { label: 'Platform Conns', value: stats?.connected_platforms || 0, icon: <FiShield />, color: 'red' },
    { label: 'Users Today', value: stats?.users_today || 0, icon: <FiClock />, color: 'indigo' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="flex items-center gap-2 text-sm text-violet-400 font-medium mb-1">
            <FiShield /> Admin Panel
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">User Management</h1>
          <p className="text-slate-400 mt-1">View all users and their details</p>
        </div>
      </div>

      {selected ? (
        <div className="glass-card p-6 md:p-8 relative overflow-hidden">
          <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full bg-indigo-600/15 blur-[80px]" />
          <button onClick={() => setSelected(null)} className="btn-ghost text-sm mb-6 flex items-center gap-1.5">
            <FiArrowLeft /> Back to all users
          </button>
          <div className="relative">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-fuchsia-500 flex items-center justify-center text-2xl font-bold text-white shadow-xl">
                {(selected.full_name || selected.username || 'U').charAt(0).toUpperCase()}
              </div>
              <div>
                <h2 className="text-2xl font-bold">{selected.full_name || selected.username}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-slate-400">@{selected.username}</span>
                  <span className={`badge ${selected.is_admin ? 'badge-purple' : 'badge-blue'}`}>
                    {selected.is_admin ? 'Admin' : 'User'}
                  </span>
                  <span className={`badge ${selected.is_active ? 'badge-green' : 'badge-red'}`}>
                    {selected.is_active ? 'Active' : 'Inactive'}
                  </span>
                  {selected.has_resume && <span className="badge-green"><FiUpload className="inline" /> Resume</span>}
                </div>
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-4 mb-8">
              <div className="bg-white/[0.04] border border-white/[0.06] rounded-2xl p-4">
                <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Experience</p>
                <p className="text-2xl font-bold">{selected.experience_years || 0} <span className="text-sm text-slate-400 font-normal">years</span></p>
              </div>
              <div className="bg-white/[0.04] border border-white/[0.06] rounded-2xl p-4">
                <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Applications</p>
                <p className="text-2xl font-bold">{selected.applications_count} <span className="text-sm text-slate-400 font-normal">total</span></p>
              </div>
              <div className="bg-white/[0.04] border border-white/[0.06] rounded-2xl p-4">
                <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Platform Connections</p>
                <p className="text-2xl font-bold">{selected.connections_count} <span className="text-sm text-slate-400 font-normal">connected</span></p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-bold mb-3 text-slate-200">Contact Info</h3>
                <div className="space-y-2.5 text-sm">
                  {selected.email && <div className="flex items-center gap-2 text-slate-300"><FiMail className="text-slate-500" /> {selected.email}</div>}
                  {selected.phone && <div className="flex items-center gap-2 text-slate-300"><FiPhone className="text-slate-500" /> {selected.phone}</div>}
                  {selected.location && <div className="flex items-center gap-2 text-slate-300"><FiMapPin className="text-slate-500" /> {selected.location}</div>}
                  {selected.linkedin_url && <div className="flex items-center gap-2 text-slate-300 truncate"><FiGlobe className="text-slate-500" /> {selected.linkedin_url}</div>}
                  {selected.portfolio_url && <div className="flex items-center gap-2 text-slate-300 truncate"><FiUser className="text-slate-500" /> {selected.portfolio_url}</div>}
                  {selected.created_at && (
                    <div className="flex items-center gap-2 text-slate-300">
                      <FiClock className="text-slate-500" /> Joined {new Date(selected.created_at).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>
              <div>
                <h3 className="font-bold mb-3 text-slate-200">Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {selected.skills?.length > 0 ? selected.skills.map((s: string) => <span key={s} className="badge-blue">{s}</span>)
                    : <span className="text-sm text-slate-500">No skills added</span>}
                </div>
                <h3 className="font-bold mt-5 mb-2 text-slate-200">Application Answers</h3>
                <div className="text-sm text-slate-300 space-y-1">
                  <p>Expected: <span className="text-slate-400">{selected.preferences?.expected_salary || '—'}</span></p>
                  <p>Current: <span className="text-slate-400">{selected.preferences?.current_salary || '—'}</span></p>
                  <p>Notice: <span className="text-slate-400">{selected.preferences?.notice_period || '—'}</span></p>
                  <p>Availability: <span className="text-slate-400">{selected.preferences?.availability || '—'}</span></p>
                  <p>Location: <span className="text-slate-400">{selected.preferences?.preferred_location || '—'}</span></p>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            {statCards.map(s => (
              <div key={s.label} className="glass-card p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-lg ${s.color === 'blue' ? 'text-blue-400' : s.color === 'green' ? 'text-emerald-400' : s.color === 'purple' ? 'text-violet-400' : s.color === 'yellow' ? 'text-amber-400' : s.color === 'red' ? 'text-rose-400' : 'text-indigo-400'}`}>{s.icon}</span>
                </div>
                <p className="text-2xl font-extrabold">{s.value}</p>
                <p className="text-xs text-slate-400 mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>

          <div className="glass-card overflow-hidden">
            <div className="flex flex-wrap items-center justify-between gap-3 p-5 border-b border-white/[0.06]">
              <h2 className="font-bold text-lg">All Users ({users.length})</h2>
              <div className="relative">
                <FiSearch className="absolute left-3 top-3 text-slate-500" />
                <input className="input-field pl-10 text-sm" placeholder="Search name, email..." value={query} onChange={e => setQuery(e.target.value)} />
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-500 text-xs uppercase tracking-wide border-b border-white/[0.06]">
                    <th className="px-5 py-3">User</th>
                    <th className="px-5 py-3">Email</th>
                    <th className="px-5 py-3">Experience</th>
                    <th className="px-5 py-3">Applications</th>
                    <th className="px-5 py-3">Platforms</th>
                    <th className="px-5 py-3">Resume</th>
                    <th className="px-5 py-3">Role</th>
                    <th className="px-5 py-3">Joined</th>
                    <th className="px-5 py-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(u => (
                    <tr key={u.id} className="border-b border-white/[0.04] hover:bg-white/[0.03] transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500/30 to-fuchsia-500/30 text-indigo-300 flex items-center justify-center text-sm font-bold shrink-0">
                            {(u.full_name || u.username || 'U').charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-medium text-slate-200">{u.full_name || u.username}</p>
                            <p className="text-xs text-slate-500">@{u.username}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-slate-300">{u.email}</td>
                      <td className="px-5 py-3.5 text-slate-300">{u.experience_years || 0} yrs</td>
                      <td className="px-5 py-3.5 text-slate-300">{u.applications_count}</td>
                      <td className="px-5 py-3.5 text-slate-300">{u.connections_count}</td>
                      <td className="px-5 py-3.5">
                        <span className={`badge ${u.has_resume ? 'badge-green' : 'badge-red'}`}>{u.has_resume ? 'Yes' : 'No'}</span>
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`badge ${u.is_admin ? 'badge-purple' : 'badge-blue'}`}>{u.is_admin ? 'Admin' : 'User'}</span>
                      </td>
                      <td className="px-5 py-3.5 text-slate-400">{u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</td>
                      <td className="px-5 py-3.5">
                        <button onClick={() => loadUser(u.id)} className="btn-secondary text-xs px-3 py-1.5">View</button>
                      </td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr><td colSpan={9} className="px-5 py-10 text-center text-slate-500">No users found</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}