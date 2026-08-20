'use client';
import { useEffect, useState } from 'react';
import { applications, platforms as platformsApi, jobs as jobsApi } from '@/lib/api';
import StatsCard from '@/components/StatsCard';
import JobCard from '@/components/JobCard';
import SetupChecklist from '@/components/SetupChecklist';
import toast from 'react-hot-toast';
import { FiBriefcase, FiCheckCircle, FiClock, FiXCircle, FiTarget, FiZap, FiMail, FiRefreshCw, FiLoader } from 'react-icons/fi';

export default function DashboardPage() {
  const [stats, setStats] = useState<any>({});
  const [recentJobs, setRecentJobs] = useState<any[]>([]);
  const [connectedPlatforms, setConnectedPlatforms] = useState<any[]>([]);
  const [matching, setMatching] = useState<any>({ jobs: [], total_matching: 0 });
  const [applying, setApplying] = useState(false);
  const [digest, setDigest] = useState<any>({ digest_enabled: false, search_queries: [], email_configured: false });
  const [digestQuery, setDigestQuery] = useState('');

  useEffect(() => {
    applications.stats().then(r => setStats(r.data)).catch(() => {});
    jobsApi.list({ limit: 4 }).then(r => setRecentJobs(r.data)).catch(() => {});
    platformsApi.connected().then(r => setConnectedPlatforms(r.data)).catch(() => {});
    applications.matchingPreview({ min_match_score: 0.5, limit: 5 }).then(r => setMatching(r.data)).catch(() => {});
    platformsApi.digestPrefs().then(r => setDigest(r.data)).catch(() => {});
  }, []);

  const handleAutoApply = async () => {
    setApplying(true);
    try {
      const res = await applications.applyMatching({ min_match_score: 0.5, max_jobs: 10 });
      toast.success(`Auto-apply started for ${res.data.applications.length} matching jobs!`);
      applications.stats().then(r => setStats(r.data)).catch(() => {});
    } catch { toast.error('Auto-apply failed'); }
    setApplying(false);
  };

  const toggleDigest = async () => {
    try {
      const res = await platformsApi.setDigestPrefs({ digest_enabled: !digest.digest_enabled, search_queries: digest.search_queries });
      setDigest(res.data);
      toast.success(res.data.digest_enabled ? 'Daily digest enabled!' : 'Digest disabled');
    } catch { toast.error('Failed to update digest'); }
  };

  const addDigestQuery = async () => {
    if (!digestQuery.trim()) return;
    try {
      const qs = [...(digest.search_queries || [])];
      if (!qs.includes(digestQuery.trim())) qs.push(digestQuery.trim());
      const res = await platformsApi.setDigestPrefs({ digest_enabled: true, search_queries: qs });
      setDigest(res.data);
      setDigestQuery('');
      toast.success('Search saved — will be scraped daily');
    } catch { toast.error('Failed to save search'); }
  };

  const runDigestNow = async () => {
    try {
      const res = await platformsApi.runDigest();
      toast.success(res.data.message || 'Digest run complete');
    } catch { toast.error('Digest run failed'); }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Dashboard</h1>
          <p className="text-slate-400 mt-1">Your automated job application hub</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <StatsCard title="Total Applied" value={stats.total_applications || 0} icon={<FiBriefcase />} color="blue" />
        <StatsCard title="Submitted" value={stats.submitted || 0} icon={<FiCheckCircle />} color="green" />
        <StatsCard title="Pending" value={stats.pending || 0} icon={<FiClock />} color="yellow" />
        <StatsCard title="Failed" value={stats.failed || 0} icon={<FiXCircle />} color="red" />
        <StatsCard title="Interviews" value={stats.interview || 0} icon={<FiTarget />} color="purple" />
      </div>

      <div className="mb-6">
        <SetupChecklist />
      </div>

      <div className="grid md:grid-cols-3 gap-6 mb-6">
        <div className="md:col-span-2 space-y-6">
          <div className="glass-card p-6 md:p-8 relative overflow-hidden">
            <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full bg-violet-600/20 blur-[80px]" />
            <div className="relative">
              <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
                <h2 className="text-xl font-bold flex items-center gap-2.5">
                  <span className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500/30 to-orange-500/30 flex items-center justify-center text-amber-400">
                    <FiZap />
                  </span>
                  One-Click Auto-Apply
                </h2>
                <span className="text-sm font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 rounded-full px-4 py-1.5">
                  {matching.total_matching} matching jobs ready
                </span>
              </div>
              <p className="text-sm text-slate-400 mb-5 max-w-xl">
                Automatically applies to your best-matching saved jobs with your resume, AI cover letter and answers — zero typing.
              </p>
              {matching.jobs?.length > 0 && (
                <div className="mb-5 space-y-1.5">
                  {matching.jobs.map((j: any) => (
                    <div key={j.id} className="flex items-center justify-between text-sm bg-white/[0.04] border border-white/[0.06] rounded-xl px-4 py-2.5">
                      <span className="text-slate-200 truncate">
                        {j.title} <span className="text-slate-500">@ {j.company}</span>
                      </span>
                      <span className={`badge ${j.match_score >= 0.8 ? 'badge-green' : 'badge-yellow'}`}>{Math.round(j.match_score * 100)}%</span>
                    </div>
                  ))}
                </div>
              )}
              <button onClick={handleAutoApply} disabled={applying} className="btn-primary px-6 py-3">
                {applying ? <><FiLoader className="animate-spin" /> Applying...</> : <><FiZap /> Auto-Apply to Top {Math.min(matching.total_matching || 0, 10)} Jobs</>}
              </button>
            </div>
          </div>

          <div>
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500/25 to-indigo-500/25 text-sky-400 flex items-center justify-center"><FiBriefcase /></span>
              Top Matching Jobs
            </h2>
            <div className="space-y-4">
              {recentJobs.length > 0 ? recentJobs.map(job => (
                <JobCard key={job.id} job={job} />
              )) : (
                <div className="glass-card text-center text-slate-400 py-12">
                  No jobs found yet. Upload your resume and connect platforms to get started.
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-card p-6">
            <h2 className="text-lg font-bold flex items-center gap-2.5 mb-3">
              <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500/25 to-fuchsia-500/25 text-violet-400 flex items-center justify-center"><FiMail /></span>
              Daily Job Digest
            </h2>
            <p className="text-sm text-slate-400 mb-4">We scrape job sites daily and email new matching jobs — no need to open the app.</p>
            <div className="flex gap-2 mb-3">
              <input className="input-field text-sm flex-1" placeholder="e.g. python developer" value={digestQuery} onChange={e => setDigestQuery(e.target.value)} />
              <button onClick={addDigestQuery} className="btn-secondary text-sm px-4">Add</button>
            </div>
            {digest.search_queries?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-4">
                {digest.search_queries.map((q: string) => <span key={q} className="badge-blue">{q}</span>)}
              </div>
            )}
            <div className="space-y-2">
              <button onClick={toggleDigest} className={`btn w-full ${digest.digest_enabled ? 'btn-danger' : 'btn-primary'}`}>
                {digest.digest_enabled ? 'Disable Digest' : 'Enable Daily Digest'}
              </button>
              <button onClick={runDigestNow} className="btn-secondary w-full">
                <FiRefreshCw /> Run Digest Now
              </button>
            </div>
            {!digest.email_configured && (
              <p className="text-xs text-amber-400/80 mt-3">Email sending not configured — add SMTP settings in backend/.env to receive digests.</p>
            )}
          </div>

          <div className="glass-card p-6">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500/25 to-teal-500/25 text-emerald-400 flex items-center justify-center"><FiCheckCircle /></span>
              Connected Platforms
            </h2>
            <div className="space-y-2.5">
              {connectedPlatforms.length > 0 ? connectedPlatforms.map(p => (
                <div key={p.id} className="flex items-center justify-between bg-white/[0.04] border border-white/[0.06] rounded-xl px-4 py-2.5">
                  <span className="font-medium capitalize">{p.platform_name}</span>
                  <span className={`badge ${p.is_connected ? 'badge-green' : 'badge-red'}`}>{p.is_connected ? 'Connected' : 'Offline'}</span>
                </div>
              )) : (
                <div className="text-center text-slate-400 py-6 text-sm">
                  No platforms connected yet.
                  <br />
                  <span className="text-violet-400">Go to Platforms to connect.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}