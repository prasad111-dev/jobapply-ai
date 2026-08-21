'use client';
import { useEffect, useState } from 'react';
import { platforms as platformsApi } from '@/lib/api';
import toast from 'react-hot-toast';
import { FiCheck, FiExternalLink, FiShield, FiXCircle, FiLock, FiZap, FiLoader, FiGlobe } from 'react-icons/fi';

export default function PlatformsPage() {
  const [platforms, setPlatforms] = useState<any[]>([]);
  const [connected, setConnected] = useState<any[]>([]);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [verifyMsg, setVerifyMsg] = useState<{ name: string; ok: boolean; msg: string } | null>(null);
  const [showForm, setShowForm] = useState<string | null>(null);
  const [credForm, setCredForm] = useState({ username: '', password: '' });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [p, c] = await Promise.all([platformsApi.list(), platformsApi.connected()]);
      setPlatforms(p.data);
      setConnected(c.data);
    } catch {}
  };

  const isConnected = (name: string) => connected.some(c => c.platform_name === name && c.is_connected);
  const hasCredentials = (name: string) => connected.some(c => c.platform_name === name && c.has_credentials);

  const handleConnect = async (platformName: string) => {
    if (!credForm.username || !credForm.password) { toast.error('Enter your platform username and password.'); return; }
    setConnecting(platformName);
    setVerifyMsg(null);
    try {
      await platformsApi.connect({ platform_name: platformName, username: credForm.username, password: credForm.password });
      setShowForm(null); setCredForm({ username: '', password: '' });
      toast.success(`Connected to ${platformName}!`);
      loadData();
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Connection failed'); }
    setConnecting(null);
  };

  const handleVerifyAndConnect = async (platformName: string) => {
    if (!credForm.username || !credForm.password) { toast.error('Enter your platform username and password first.'); return; }
    setConnecting(platformName);
    setVerifyMsg(null);
    try {
      const test = await platformsApi.testConnection(platformName, credForm.username, credForm.password);
      const v = test.data;
      if (v.verified) {
        setVerifyMsg({ name: platformName, ok: true, msg: v.message || 'Verified & connected!' });
      } else {
        setVerifyMsg({ name: platformName, ok: true, msg: v.message || 'Credentials saved. Verification was skipped.' });
      }
      setShowForm(null); setCredForm({ username: '', password: '' });
      toast.success(`Connected to ${platformName}${v.verified ? ' (verified)' : ' (credentials saved)'}`);
      loadData();
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Connection failed'); }
    setConnecting(null);
  };

  const handleDisconnect = async (name: string) => {
    try {
      await platformsApi.disconnect(name);
      toast.success(`Disconnected from ${name}`);
      loadData();
    } catch { toast.error('Disconnect failed'); }
  };

  const difficultyColor: Record<string, string> = { easy: 'badge-green', medium: 'badge-yellow', hard: 'badge-red' };
  const brandColor: Record<string, string> = {
    indeed: 'from-sky-500/30 to-blue-500/30', linkedin: 'from-blue-500/30 to-sky-500/30',
    naukri: 'from-rose-500/30 to-red-500/30', glassdoor: 'from-emerald-500/30 to-teal-500/30',
    internshala: 'from-orange-500/30 to-amber-500/30', unstop: 'from-violet-500/30 to-purple-500/30',
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-extrabold tracking-tight mb-2">Job Platforms</h1>
      <p className="text-slate-400 mb-8 max-w-2xl">
        Enter your real account credentials once — we verify the login and reuse the session for auto-apply.
      </p>

      {verifyMsg && (
        <div className={`glass-card p-4 mb-6 border ${verifyMsg.ok ? 'border-emerald-500/40 bg-emerald-500/[0.06]' : 'border-rose-500/40 bg-rose-500/[0.06]'}`}>
          <p className={verifyMsg.ok ? 'text-emerald-300' : 'text-rose-300'}>{verifyMsg.msg}</p>
        </div>
      )}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
        {platforms.map(p => {
          const isConn = isConnected(p.name);
          const hasCreds = hasCredentials(p.name);
          const connRecord = connected.find(c => c.platform_name === p.name);
          const gradient = brandColor[p.name] || 'from-indigo-500/30 to-violet-500/30';
          return (
            <div key={p.name} className={`glass-card-hover p-5 ${isConn ? 'border-emerald-500/40' : ''}`}>
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${gradient} flex items-center justify-center text-xl shrink-0`}>
                  <FiGlobe />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-bold text-lg leading-tight">{p.display_name}</h3>
                  <a href={p.url} target="_blank" rel="noopener noreferrer" className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1">
                    {p.url.replace('https://', '')} <FiExternalLink className="text-[10px]" />
                  </a>
                </div>
                <span className={difficultyColor[p.difficulty_level]}>{p.difficulty_level}</span>
              </div>

              {showForm === p.name ? (
                <div className="space-y-3">
                  <input className="input-field text-sm" placeholder="Username / Email" value={credForm.username} onChange={e => setCredForm({...credForm, username: e.target.value})} />
                  <input className="input-field text-sm" type="password" placeholder="Password" value={credForm.password} onChange={e => setCredForm({...credForm, password: e.target.value})} />
                  <p className="text-xs text-slate-500 flex items-center gap-1.5"><FiLock className="text-xs" /> Password is encrypted. We log in once to verify &amp; save the session.</p>
                  <div className="flex flex-wrap gap-2">
                    <button onClick={() => handleVerifyAndConnect(p.name)} disabled={connecting === p.name} className="btn-primary text-sm flex-1">
                      {connecting === p.name ? <><FiLoader className="animate-spin" /> Verifying...</> : <><FiZap /> Verify &amp; Connect</>}
                    </button>
                    <button onClick={() => handleConnect(p.name)} disabled={connecting === p.name} className="btn-secondary text-sm">Save</button>
                    <button onClick={() => setShowForm(null)} className="btn-secondary text-sm">Cancel</button>
                  </div>
                </div>
              ) : isConn ? (
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-emerald-400 text-sm font-medium"><FiCheck /> Connected</span>
                    <button onClick={() => handleDisconnect(p.name)} className="text-rose-400 hover:text-rose-300 text-sm flex items-center gap-1">
                      <FiXCircle /> Disconnect
                    </button>
                  </div>
                  {hasCreds ? (
                    <span className="flex items-center gap-1.5 text-xs text-emerald-300"><FiShield /> Credentials stored — auto-apply enabled</span>
                  ) : (
                    <span className="flex items-center gap-1.5 text-xs text-amber-400">
                      <FiShield /> No credentials —{' '}
                      <button onClick={() => { setShowForm(p.name); setCredForm({...credForm, username: (connRecord || {}).username || ''}); }}
                        className="underline hover:text-amber-300">Add password</button> to enable auto-apply
                    </span>
                  )}
                </div>
              ) : (
                <button onClick={() => setShowForm(p.name)} className="btn-primary text-sm w-full py-2.5">Connect Account</button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}