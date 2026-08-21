'use client';
import { useEffect, useState } from 'react';
import { jobs as jobsApi, applications, platforms as platformsApi, profile as profileApi } from '@/lib/api';
import JobCard from '@/components/JobCard';
import SetupChecklist from '@/components/SetupChecklist';
import toast from 'react-hot-toast';
import { FiSearch, FiCheck, FiDownload, FiLoader, FiZap, FiX, FiShield, FiUser } from 'react-icons/fi';

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [scraping, setScraping] = useState<string | null>(null);
  const [connectedPlatforms, setConnectedPlatforms] = useState<any[]>([]);
  const [scrapePlatform, setScrapePlatform] = useState('all');
  const [scrapeQuery, setScrapeQuery] = useState('python developer');
  const [readiness, setReadiness] = useState<any>(null);
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => { loadJobs(); loadConnectedPlatforms(); loadReadiness(); }, []);

  const loadReadiness = async () => {
    try {
      const r = await profileApi.readiness();
      setReadiness(r.data);
    } catch {}
  };

  const loadConnectedPlatforms = async () => {
    try {
      const res = await platformsApi.connected();
      setConnectedPlatforms(res.data);
      if (res.data.length > 0) setScrapePlatform(res.data[0].platform_name);
    } catch {}
  };

  const loadJobs = async (searchQuery?: string) => {
    setLoading(true);
    try {
      const res = await jobsApi.list({ search: searchQuery || undefined, limit: 50 });
      setJobs(res.data);
    } catch { toast.error('Failed to load jobs'); }
    setLoading(false);
  };

  const scrapeJobs = async () => {
    setScraping(scrapePlatform);
    try {
      const res = await platformsApi.scrape(scrapePlatform, scrapeQuery, 10);
      toast.success(res.data.message);
      loadJobs();
    } catch { toast.error('Scrape failed'); }
    setScraping(null);
  };

  useEffect(() => {
    if (!loading && jobs.length === 0 && connectedPlatforms.length === 0) {
      scrapeJobs();
    }
  }, [loading, connectedPlatforms]);

  const toggleSelect = (id: number) => {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
  };

  const selectAll = () => {
    if (selected.size === jobs.length) setSelected(new Set());
    else setSelected(new Set(jobs.map(j => j.id)));
  };

  const bulkApply = async () => {
    if (selected.size === 0) { toast.error('Select at least one job'); return; }
    setShowConfirm(true);
  };

  const confirmApply = async () => {
    setShowConfirm(false);
    setApplying(true);
    try {
      const res = await applications.apply(Array.from(selected));
      const { successful, pending, failed, applications: apps } = res.data;
      if (successful > 0) toast.success(`Applied to ${successful} jobs!`);
      if (pending > 0) toast(`${pending} jobs need attention. Check Applications tab.`, { icon: '📋' });
      if (failed > 0) toast.error(`${failed} jobs failed`);
      setSelected(new Set());
      loadJobs();
      loadReadiness();
    } catch { toast.error('Bulk apply failed'); }
    setApplying(false);
  };

  const singleApply = async (id: number) => {
    try {
      const res = await applications.apply([id]);
      const app = res.data.applications?.[0];
      if (app?.status === 'submitted') toast.success('Applied successfully!');
      else if (app?.form_data?.platform_url) {
        toast(`Application prepared. Complete it on the platform.`, { icon: '🌐' });
        window.open(app.form_data.platform_url, '_blank');
      } else toast.success('Application data prepared!');
    } catch { toast.error('Apply failed'); }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Jobs</h1>
          <p className="text-slate-400 mt-1">Find, match and apply in one place</p>
        </div>
        {selected.size > 0 && (
          <button onClick={bulkApply} disabled={applying} className="btn-primary flex items-center gap-2 px-6 py-2.5">
            <FiCheck /> {applying ? 'Applying...' : `Apply to ${selected.size} Job${selected.size > 1 ? 's' : ''}`}
          </button>
        )}
      </div>

      <div className="mb-6">
        <SetupChecklist compact />
      </div>

      <div className="glass-card p-6 mb-6 relative overflow-hidden">
        <div className="absolute -top-16 -right-16 w-48 h-48 rounded-full bg-indigo-600/15 blur-[70px]" />
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2.5">
          <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500/25 to-violet-500/25 text-indigo-400 flex items-center justify-center"><FiDownload /></span>
          Scrape New Jobs
        </h2>
        {connectedPlatforms.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {connectedPlatforms.map((p: any) => (
              <span key={p.platform_name} className={`badge ${p.is_connected ? 'badge-green' : 'badge-red'} capitalize`}>
                {p.is_connected ? '✓' : '✗'} {p.platform_name}
              </span>
            ))}
          </div>
        )}
        <div className="grid md:grid-cols-[1fr_1.5fr_auto] gap-3 items-end">
          <div>
            <label className="text-xs text-slate-400 mb-1.5 block font-medium uppercase tracking-wide">Source</label>
            <select className="input-field" value={scrapePlatform} onChange={e => setScrapePlatform(e.target.value)}>
              <option value="all">All sources (RemoteOK + Remotive + Internshala + JSearch)</option>
              <option value="remoteok">RemoteOK (remote jobs)</option>
              <option value="remotive">Remotive (remote jobs)</option>
              <option value="internshala">Internshala (internships)</option>
              <option value="linkedin">LinkedIn (via JSearch)</option>
              <option value="indeed">Indeed (via JSearch)</option>
              <option value="glassdoor">Glassdoor (via JSearch)</option>
              <option value="naukri">Naukri (may need CAPTCHA)</option>
              {connectedPlatforms.length > 0 && connectedPlatforms.map(p => (
                <option key={p.platform_name} value={p.platform_name} className="capitalize">{p.platform_name} (connected)</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1.5 block font-medium uppercase tracking-wide">Search Query</label>
            <input className="input-field" value={scrapeQuery} onChange={e => setScrapeQuery(e.target.value)} placeholder="e.g. python developer" onKeyDown={e => e.key === 'Enter' && scrapeJobs()} />
          </div>
          <button onClick={scrapeJobs} disabled={!!scraping} className="btn-primary h-11 px-6 whitespace-nowrap">
            {scraping ? <><FiLoader className="animate-spin" /> Scraping...</> : <><FiDownload /> Scrape Jobs</>}
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative flex-1 min-w-[220px]">
          <FiSearch className="absolute left-3.5 top-3 text-slate-500" />
          <input className="input-field pl-10" placeholder="Search jobs, companies, skills..." value={search}
            onChange={e => setSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && loadJobs(search)} />
        </div>
        <button onClick={() => loadJobs(search)} className="btn-secondary px-6">Search</button>
        {jobs.length > 0 && (
          <button onClick={selectAll} className="btn-secondary px-6">
            {selected.size === jobs.length ? 'Deselect All' : 'Select All'}
          </button>
        )}
        {selected.size > 0 && (
          <span className="flex items-center gap-2 text-sm text-violet-300">
            <FiZap className="text-amber-400" /> {selected.size} selected
          </span>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="flex items-center gap-3 text-slate-400"><FiLoader className="animate-spin" /> Loading jobs...</div>
        </div>
      ) : jobs.length === 0 ? (
        <div className="glass-card text-center py-16">
          <p className="text-lg mb-3 text-slate-300">No jobs found yet</p>
          <p className="text-sm text-slate-500 mb-4">Click <span className="text-violet-400 font-medium">Scrape Jobs</span> above to pull live listings from RemoteOK, Remotive, and Internshala.</p>
          <p className="text-xs text-slate-600">Tip: Naukri requires CAPTCHA verification — use "All sources" for best results.</p>
        </div>
      ) : (
        <>
          <p className="text-sm text-slate-500 mb-4">{jobs.length} jobs found</p>
          <div className="grid md:grid-cols-2 gap-4">
            {jobs.map(job => (
              <div key={job.id} className={`relative rounded-2xl ${selected.has(job.id) ? 'ring-2 ring-violet-500/60' : ''}`}>
                <input type="checkbox" checked={selected.has(job.id)} onChange={() => toggleSelect(job.id)}
                  className="absolute top-5 right-5 w-5 h-5 accent-violet-500 z-10 cursor-pointer" />
                <JobCard job={job} onApply={singleApply} />
              </div>
            ))}
          </div>
        </>
      )}

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setShowConfirm(false)} />
          <div className="relative glass-card max-w-lg w-full p-6 shadow-2xl">
            <button onClick={() => setShowConfirm(false)} className="absolute top-4 right-4 text-slate-400 hover:text-white">
              <FiX />
            </button>
            <div className="flex items-center gap-3 mb-4">
              <span className="w-11 h-11 rounded-xl bg-gradient-to-br from-violet-500/30 to-fuchsia-500/30 flex items-center justify-center text-violet-300 text-lg"><FiZap /></span>
              <div>
                <h3 className="text-lg font-bold">Confirm Auto-Apply</h3>
                <p className="text-xs text-slate-400">{selected.size} job{selected.size > 1 ? 's' : ''} selected</p>
              </div>
            </div>

            <div className="max-h-44 overflow-y-auto mb-4 space-y-1.5 rounded-xl bg-white/[0.03] border border-white/[0.06] p-3">
              {jobs.filter(j => selected.has(j.id)).map(j => (
                <div key={j.id} className="flex items-center justify-between text-sm">
                  <span className="text-slate-200 truncate">{j.title} <span className="text-slate-500">@ {j.company}</span></span>
                  <span className={`badge capitalize ${j.platform_source === 'naukri' ? 'badge-blue' : j.platform_source === 'internshala' ? 'badge-green' : 'badge-purple'}`}>
                    {j.platform_source}
                  </span>
                </div>
              ))}
            </div>

            {!readiness?.ready ? (
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/[0.06] p-3.5 mb-4">
                <p className="text-sm text-amber-300 font-medium mb-1.5 flex items-center gap-1.5"><FiShield /> Setup not complete</p>
                <p className="text-xs text-slate-300">{readiness?.message}</p>
                <div className="flex gap-2 mt-2">
                  {!readiness?.profile?.complete && (
                    <a href="/profile" className="text-xs text-violet-300 hover:underline flex items-center gap-1"><FiUser /> Complete profile</a>
                  )}
                  {readiness?.connections?.length === 0 && (
                    <a href="/platforms" className="text-xs text-violet-300 hover:underline flex items-center gap-1"><FiShield /> Connect platform</a>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-xs text-emerald-300 mb-4 flex items-center gap-1.5">
                <FiShield /> Profile complete &amp; platforms connected — these will be submitted automatically.
              </p>
            )}

            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowConfirm(false)} className="btn-secondary px-5">Cancel</button>
              <button onClick={confirmApply} disabled={applying || !readiness?.ready} className="btn-primary px-5">
                {applying ? <><FiLoader className="animate-spin" /> Applying...</> : <>Apply Now</>}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}