'use client';
import { useEffect, useState, useMemo } from 'react';
import { jobs as jobsApi, applications, platforms as platformsApi, profile as profileApi } from '@/lib/api';
import JobCard from '@/components/JobCard';
import SetupChecklist from '@/components/SetupChecklist';
import toast from 'react-hot-toast';
import { FiSearch, FiCheck, FiDownload, FiLoader, FiZap, FiX, FiShield, FiUser, FiGlobe } from 'react-icons/fi';

const CATEGORIES = [
  { key: 'all', label: 'All Jobs', icon: '📋' },
  { key: 'software', label: 'Software & IT', icon: '💻', keywords: ['developer', 'engineer', 'software', 'frontend', 'backend', 'fullstack', 'devops', 'cloud', 'data', 'python', 'java', 'react', 'node', 'android', 'ios', 'qa', 'tester', 'admin', 'architect', 'blockchain', 'cyber', 'machine learning', 'ai'] },
  { key: 'design', label: 'Design & Creative', icon: '🎨', keywords: ['designer', 'design', 'ui', 'ux', 'graphic', 'creative', 'animation', 'video', 'photo', 'fashion', 'interior', 'motion'] },
  { key: 'marketing', label: 'Marketing & Sales', icon: '📈', keywords: ['marketing', 'sales', 'seo', 'content', 'social media', 'growth', 'business development', 'account executive', 'advertising', 'brand', 'email'] },
  { key: 'finance', label: 'Finance & Accounting', icon: '💰', keywords: ['accountant', 'finance', 'financial', 'tax', 'audit', 'banking', 'ca ', 'chartered', 'budget', 'investment'] },
  { key: 'hr', label: 'HR & Admin', icon: '👥', keywords: ['human resource', 'hr ', 'recruiter', 'talent', 'admin', 'office', 'payroll'] },
  { key: 'management', label: 'Management', icon: '📊', keywords: ['manager', 'director', 'head', 'lead', 'vp', 'chief', 'operations', 'project manager', 'product manager'] },
  { key: 'education', label: 'Education & Training', icon: '📚', keywords: ['teacher', 'trainer', 'tutor', 'lecturer', 'educational', 'professor', 'instructor'] },
  { key: 'healthcare', label: 'Healthcare', icon: '🏥', keywords: ['nurse', 'doctor', 'medical', 'pharmacist', 'healthcare', 'health', 'clinical'] },
  { key: 'customer', label: 'Customer Support', icon: '🎧', keywords: ['customer', 'support', 'call center', 'helpdesk', 'service'] },
  { key: 'internship', label: 'Internships & Fresher', icon: '🎓', keywords: ['intern', 'internship', 'fresher', 'entry level', 'trainee', 'graduate'] },
  { key: 'remote', label: 'Remote & Freelance', icon: '🌍', keywords: ['remote', 'work from home', 'freelance', 'freelancer', 'wfh', 'anywhere'] },
];

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [scraping, setScraping] = useState<string | null>(null);
  const [scrapingAll, setScrapingAll] = useState(false);
  const [connectedPlatforms, setConnectedPlatforms] = useState<any[]>([]);
  const [scrapePlatform, setScrapePlatform] = useState('all');
  const [scrapeQuery, setScrapeQuery] = useState('');
  const [scrapeLocation, setScrapeLocation] = useState('');
  const [readiness, setReadiness] = useState<any>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [hasAutoScraped, setHasAutoScraped] = useState(false);

  useEffect(() => { loadJobs(); loadConnectedPlatforms(); loadReadiness(); }, []);

  const loadReadiness = async () => {
    try { const r = await profileApi.readiness(); setReadiness(r.data); } catch {}
  };

  const loadConnectedPlatforms = async () => {
    try {
      const res = await platformsApi.connected();
      setConnectedPlatforms(res.data);
    } catch {}
  };

  const loadJobs = async (searchQuery?: string) => {
    setLoading(true);
    try {
      const res = await jobsApi.list({ search: searchQuery || undefined, limit: 500 });
      setJobs(res.data);
      if (!hasAutoScraped && res.data.length < 20) {
        setHasAutoScraped(true);
        scrapeAllCategories();
      }
    } catch { toast.error('Failed to load jobs'); }
    setLoading(false);
  };

  const scrapeJobs = async () => {
    setScraping(scrapePlatform);
    try {
      const res = await platformsApi.scrape(scrapePlatform, scrapeQuery || 'developer', 50, scrapeLocation);
      toast.success(res.data.message);
      loadJobs();
    } catch { toast.error('Scrape failed'); }
    setScraping(null);
  };

  const scrapeAllCategories = async () => {
    setScrapingAll(true);
    toast.loading('Scraping ALL job categories from ALL platforms...', { id: 'scrape-all' });
    try {
      const res = await platformsApi.scrapeAll();
      const data = res.data;
      toast.success(`Done! ${data.message}`, { id: 'scrape-all' });
      loadJobs();
    } catch { toast.error('Full scrape failed', { id: 'scrape-all' }); }
    setScrapingAll(false);
  };

  const toggleSelect = (id: number) => {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
  };

  const selectAll = () => {
    const visible = getFilteredJobs;
    if (selected.size === visible.length) setSelected(new Set());
    else setSelected(new Set(visible.map((j: any) => j.id)));
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
      const { successful, pending, failed } = res.data;
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

  const getFilteredJobs = useMemo(() => {
    let filtered = jobs;
    if (activeCategory !== 'all') {
      const cat = CATEGORIES.find(c => c.key === activeCategory);
      if (cat?.keywords) {
        filtered = jobs.filter(j => {
          const text = ((j.title || '') + ' ' + (j.description || '') + ' ' + (j.company || '')).toLowerCase();
          return cat.keywords.some(kw => text.includes(kw));
        });
      }
    }
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter(j => {
        const text = ((j.title || '') + ' ' + (j.company || '') + ' ' + (j.location || '') + ' ' + (j.description || '')).toLowerCase();
        return text.includes(q);
      });
    }
    return filtered;
  }, [jobs, activeCategory, search]);

  const platformCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    jobs.forEach(j => { const p = j.platform_source || 'other'; counts[p] = (counts[p] || 0) + 1; });
    return counts;
  }, [jobs]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Jobs</h1>
          <p className="text-slate-400 mt-1">{jobs.length} jobs from {Object.keys(platformCounts).length} platforms — search, select, apply</p>
        </div>
        <div className="flex items-center gap-3">
          {selected.size > 0 && (
            <button onClick={bulkApply} disabled={applying} className="btn-primary flex items-center gap-2 px-6 py-2.5">
              <FiCheck /> {applying ? 'Applying...' : `Apply to ${selected.size} Job${selected.size > 1 ? 's' : ''}`}
            </button>
          )}
          <button onClick={scrapeAllCategories} disabled={scrapingAll} className="btn-danger flex items-center gap-2 px-5 py-2.5">
            <FiGlobe /> {scrapingAll ? 'Scraping ALL...' : 'Scrape All Categories'}
          </button>
        </div>
      </div>

      <div className="mb-6"><SetupChecklist compact /></div>

      {/* Category tabs */}
      <div className="flex gap-2 mb-5 overflow-x-auto scrollbar-hide pb-1">
        {CATEGORIES.map(cat => {
          const count = cat.key === 'all' ? jobs.length : jobs.filter(j => {
            const text = ((j.title || '') + ' ' + (j.description || '') + ' ' + (j.company || '')).toLowerCase();
            return cat.keywords?.some(kw => text.includes(kw)) || false;
          }).length;
          return (
            <button key={cat.key} onClick={() => setActiveCategory(cat.key)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                activeCategory === cat.key
                  ? 'bg-gradient-to-r from-indigo-500/90 to-violet-500/90 text-white shadow-lg'
                  : 'bg-white/[0.04] border border-white/10 text-slate-400 hover:text-white hover:bg-white/[0.08]'
              }`}>
              <span>{cat.icon}</span>
              <span>{cat.label}</span>
              <span className="text-xs opacity-60 ml-1">({count})</span>
            </button>
          );
        })}
      </div>

      {/* Platform source badges */}
      <div className="flex flex-wrap gap-2 mb-4">
        {Object.entries(platformCounts).sort((a, b) => b[1] - a[1]).map(([p, c]) => (
          <span key={p} className="badge badge-purple capitalize text-[11px]">{p} ({c})</span>
        ))}
      </div>

      {/* Scrape section */}
      <div className="glass-card p-5 mb-6">
        <h2 className="text-sm font-bold mb-3 flex items-center gap-2 text-slate-300">
          <FiDownload className="text-indigo-400" /> Custom Search Scrape
        </h2>
        <div className="grid md:grid-cols-[1fr_1fr_1.5fr_auto] gap-3 items-end">
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Source</label>
            <select className="input-field text-sm" value={scrapePlatform} onChange={e => setScrapePlatform(e.target.value)}>
              <option value="all">All sources</option>
              <option value="linkedin">LinkedIn (JSearch)</option>
              <option value="indeed">Indeed (JSearch)</option>
              <option value="glassdoor">Glassdoor (JSearch)</option>
              <option value="remoteok">RemoteOK</option>
              <option value="remotive">Remotive</option>
              <option value="internshala">Internshala</option>
              <option value="naukri">Naukri</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Location</label>
            <input className="input-field text-sm" value={scrapeLocation} onChange={e => setScrapeLocation(e.target.value)} placeholder="Mumbai, Delhi, Remote..." onKeyDown={e => e.key === 'Enter' && scrapeJobs()} />
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Search</label>
            <input className="input-field text-sm" value={scrapeQuery} onChange={e => setScrapeQuery(e.target.value)} placeholder="e.g. python developer, marketing manager" onKeyDown={e => e.key === 'Enter' && scrapeJobs()} />
          </div>
          <button onClick={scrapeJobs} disabled={!!scraping} className="btn-primary h-10 px-5 whitespace-nowrap text-sm">
            {scraping ? <><FiLoader className="animate-spin" /> Scraping...</> : <><FiDownload /> Scrape</>}
          </button>
        </div>
      </div>

      {/* Search + Select */}
      <div className="flex flex-wrap gap-3 mb-5">
        <div className="relative flex-1 min-w-[220px]">
          <FiSearch className="absolute left-3.5 top-3 text-slate-500" />
          <input className="input-field pl-10" placeholder={`Search ${getFilteredJobs.length} jobs...`} value={search}
            onChange={e => setSearch(e.target.value)} />
        </div>
        {jobs.length > 0 && (
          <button onClick={selectAll} className="btn-secondary px-5">
            {selected.size === getFilteredJobs.length ? 'Deselect All' : 'Select All'}
          </button>
        )}
        {selected.size > 0 && (
          <span className="flex items-center gap-2 text-sm text-violet-300">
            <FiZap className="text-amber-400" /> {selected.size} selected
          </span>
        )}
      </div>

      {/* Jobs grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="flex items-center gap-3 text-slate-400"><FiLoader className="animate-spin" /> Loading jobs...</div>
        </div>
      ) : getFilteredJobs.length === 0 ? (
        <div className="glass-card text-center py-16">
          <p className="text-lg mb-3 text-slate-300">
            {jobs.length === 0 ? 'No jobs found yet' : 'No jobs match this filter'}
          </p>
          {jobs.length === 0 ? (
            <>
              <p className="text-sm text-slate-500 mb-4">Click <span className="text-red-400 font-medium">Scrape All Categories</span> to pull jobs from ALL platforms and ALL job types.</p>
              <button onClick={scrapeAllCategories} disabled={scrapingAll} className="btn-primary px-6 py-2.5">
                <FiGlobe /> {scrapingAll ? 'Scraping...' : 'Scrape All Categories'}
              </button>
            </>
          ) : (
            <p className="text-sm text-slate-500">Try a different category or clear your search.</p>
          )}
        </div>
      ) : (
        <>
          <div className="grid md:grid-cols-2 gap-4">
            {getFilteredJobs.map(job => (
              <div key={job.id} className={`relative rounded-2xl ${selected.has(job.id) ? 'ring-2 ring-violet-500/60' : ''}`}>
                <input type="checkbox" checked={selected.has(job.id)} onChange={() => toggleSelect(job.id)}
                  className="absolute top-5 right-5 w-5 h-5 accent-violet-500 z-10 cursor-pointer" />
                <JobCard job={job} onApply={singleApply} />
              </div>
            ))}
          </div>
        </>
      )}

      {/* Confirm modal */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setShowConfirm(false)} />
          <div className="relative glass-card max-w-lg w-full p-6 shadow-2xl">
            <button onClick={() => setShowConfirm(false)} className="absolute top-4 right-4 text-slate-400 hover:text-white"><FiX /></button>
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
                  <span className="badge capitalize badge-purple">{j.platform_source}</span>
                </div>
              ))}
            </div>
            {!readiness?.ready ? (
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/[0.06] p-3.5 mb-4">
                <p className="text-sm text-amber-300 font-medium mb-1.5 flex items-center gap-1.5"><FiShield /> Setup not complete</p>
                <p className="text-xs text-slate-300">{readiness?.message}</p>
                <div className="flex gap-2 mt-2">
                  {!readiness?.profile?.complete && <a href="/profile" className="text-xs text-violet-300 hover:underline flex items-center gap-1"><FiUser /> Complete profile</a>}
                  {readiness?.connections?.length === 0 && <a href="/platforms" className="text-xs text-violet-300 hover:underline flex items-center gap-1"><FiShield /> Connect platform</a>}
                </div>
              </div>
            ) : (
              <p className="text-xs text-emerald-300 mb-4 flex items-center gap-1.5">
                <FiShield /> Ready — will auto-apply with your resume & AI cover letter.
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
