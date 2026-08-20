'use client';
import { useEffect, useState } from 'react';
import { applications } from '@/lib/api';
import { FiCheckCircle, FiClock, FiXCircle, FiTarget, FiExternalLink, FiFileText, FiChevronDown, FiLoader } from 'react-icons/fi';

export default function ApplicationsPage() {
  const [apps, setApps] = useState<any[]>([]);
  const [filter, setFilter] = useState('');
  const [expanded, setExpanded] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadApps(); }, [filter]);

  const loadApps = async () => {
    setLoading(true);
    try {
      const res = await applications.list({ status: filter || undefined });
      setApps(res.data);
    } catch {}
    setLoading(false);
  };

  const statusConfig = (s: string) => {
    const map: Record<string, { icon: React.ReactNode; badge: string; label: string; ring: string }> = {
      submitted: { icon: <FiCheckCircle className="text-emerald-400 text-lg" />, badge: 'badge-green', label: 'Applied', ring: 'border-emerald-500/40' },
      pending: { icon: <FiClock className="text-amber-400 text-lg" />, badge: 'badge-yellow', label: 'Needs Manual Submit', ring: 'border-amber-500/40' },
      failed: { icon: <FiXCircle className="text-rose-400 text-lg" />, badge: 'badge-red', label: 'Failed', ring: 'border-rose-500/40' },
      interview: { icon: <FiTarget className="text-violet-400 text-lg" />, badge: 'badge-purple', label: 'Interview', ring: 'border-violet-500/40' },
    };
    return map[s] || { icon: <FiClock className="text-slate-400 text-lg" />, badge: 'badge-blue', label: s, ring: 'border-white/10' };
  };

  const filters = [
    { key: '', label: 'All' },
    { key: 'submitted', label: 'Applied' },
    { key: 'pending', label: 'Manual' },
    { key: 'failed', label: 'Failed' },
    { key: 'interview', label: 'Interview' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-extrabold tracking-tight mb-2">My Applications</h1>
      <p className="text-slate-400 mb-8">Track every application across all platforms</p>

      <div className="flex gap-2 mb-6 flex-wrap">
        {filters.map(f => (
          <button key={f.key} onClick={() => setFilter(f.key)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${filter === f.key
              ? 'bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-[0_0_16px_-4px_rgba(139,92,246,0.6)]'
              : 'bg-white/[0.04] border border-white/10 text-slate-400 hover:text-white hover:border-white/20'}`}>
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="flex items-center gap-3 text-slate-400"><FiLoader className="animate-spin" /> Loading applications...</div></div>
      ) : apps.length === 0 ? (
        <div className="glass-card text-center py-16">
          <p className="text-lg text-slate-300 mb-2">No applications yet</p>
          <p className="text-sm text-slate-500">Go to <span className="text-violet-400">Jobs</span> and apply to your first job.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {apps.map(app => {
            const cfg = statusConfig(app.status);
            return (
              <div key={app.id}>
                <div className={`glass-card p-5 flex items-center gap-4 cursor-pointer hover:border-white/20 transition-colors border ${expanded === app.id ? 'border-violet-400/40' : 'border-white/10'}`}
                  onClick={() => setExpanded(expanded === app.id ? null : app.id)}>
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center bg-white/[0.05] border ${cfg.ring} shrink-0`}>{cfg.icon}</div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold truncate">{app.job_title || `Job #${app.job_id}`}</p>
                    <p className="text-sm text-slate-400 truncate">
                      {app.job_company && <span className="text-slate-300">{app.job_company}</span>}
                      {app.job_company && app.platform_name && <span> · </span>}
                      <span className="capitalize">via {app.platform_name}</span>
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    {app.platform_url && (
                      <a href={app.platform_url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
                        className="text-slate-400 hover:text-white p-2 transition-colors" title="Open job posting">
                        <FiExternalLink />
                      </a>
                    )}
                    <span className={`badge ${cfg.badge}`}>{cfg.label}</span>
                    <span className="text-xs text-slate-500 hidden sm:inline">{new Date(app.created_at).toLocaleDateString()}</span>
                    <FiChevronDown className={`text-slate-500 transition-transform ${expanded === app.id ? 'rotate-180' : ''}`} />
                  </div>
                </div>

                {expanded === app.id && (
                  <div className="glass-card mt-2 border-white/[0.06] text-sm overflow-hidden">
                    {app.form_data?.note && (
                      <div className="p-4 bg-white/[0.03] border-b border-white/[0.06]">
                        <p className="text-slate-300">{app.form_data.note}</p>
                        {app.form_data.platform_url && (
                          <a href={app.form_data.platform_url} target="_blank" rel="noopener noreferrer"
                            className="text-violet-400 hover:underline mt-1.5 inline-flex items-center gap-1">
                            Open Platform <FiExternalLink className="text-xs" />
                          </a>
                        )}
                      </div>
                    )}
                    <div className="p-4 space-y-4">
                      {app.cover_letter && (
                        <div>
                          <p className="text-slate-400 mb-2 flex items-center gap-1.5 font-medium"><FiFileText /> Cover Letter</p>
                          <pre className="text-slate-300 whitespace-pre-wrap text-xs bg-white/[0.03] p-4 rounded-xl leading-relaxed">{app.cover_letter}</pre>
                        </div>
                      )}
                      {app.form_data && Object.keys(app.form_data).filter(k => !['note', 'platform_url', 'error'].includes(k)).length > 0 && (
                        <div>
                          <p className="text-slate-400 mb-2 font-medium">Details</p>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            {Object.entries(app.form_data)
                              .filter(([k]) => !['note', 'platform_url', 'error', 'user_profile', 'auto_answers', 'automation_result'].includes(k))
                              .map(([k, v]) => (
                                <div key={k} className="bg-white/[0.03] border border-white/[0.06] p-2.5 rounded-lg">
                                  <span className="text-slate-500">{k}: </span>
                                  <span className="text-slate-200">{String(v).substring(0, 80)}</span>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}