'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { auth } from '@/lib/api';
import toast from 'react-hot-toast';
import { FiMail, FiLock, FiZap, FiEye, FiEyeOff, FiArrowRight } from 'react-icons/fi';

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', form.username);
      formData.append('password', form.password);
      const res = await auth.login(formData);
      localStorage.setItem('token', res.data.access_token);
      toast.success('Welcome back!');
      router.push('/dashboard');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-4xl glass-card overflow-hidden grid md:grid-cols-2">
        <div className="hidden md:flex flex-col justify-between p-10 relative overflow-hidden bg-gradient-to-br from-indigo-600/30 via-violet-600/20 to-fuchsia-600/30">
          <div className="absolute -bottom-20 -left-20 w-64 h-64 rounded-full bg-fuchsia-500/20 blur-[80px]" />
          <div>
            <div className="flex items-center gap-2 mb-8">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-fuchsia-500 flex items-center justify-center shadow-lg">
                <FiZap className="text-white" />
              </div>
              <span className="text-lg font-bold">JobApply<span className="text-gradient">AI</span></span>
            </div>
            <h2 className="text-3xl font-bold mb-4 leading-tight">
              Welcome back to<br />smarter job applying
            </h2>
            <p className="text-slate-300 text-sm leading-relaxed">
              Your saved resume, platform sessions and auto-apply engine are waiting for you.
            </p>
          </div>
          <div className="space-y-3 text-sm text-slate-300">
            {['AI auto-fills every application', 'Sessions saved — no re-login', 'Track every application'].map(t => (
              <div key={t} className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-fuchsia-400" /> {t}
              </div>
            ))}
          </div>
        </div>

        <div className="p-8 md:p-10">
          <h1 className="text-2xl font-bold mb-1">Login</h1>
          <p className="text-sm text-slate-400 mb-8">Access your job application hub</p>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Username</label>
              <div className="relative">
                <FiMail className="absolute left-3.5 top-3.5 text-slate-500" />
                <input type="text" className="input-field pl-11" placeholder="your username" value={form.username} onChange={e => setForm({...form, username: e.target.value})} required />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <FiLock className="absolute left-3.5 top-3.5 text-slate-500" />
                <input type={showPw ? 'text' : 'password'} className="input-field pl-11 pr-11" placeholder="••••••••" value={form.password} onChange={e => setForm({...form, password: e.target.value})} required />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-3 text-slate-500 hover:text-slate-300">
                  {showPw ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>
            </div>
            <button type="submit" className="btn-primary w-full py-3" disabled={loading}>
              {loading ? 'Logging in...' : <>Continue <FiArrowRight /></>}
            </button>
          </form>
          <p className="text-center text-slate-400 mt-6">
            Don&apos;t have an account?{' '}
            <Link href="/register" className="text-violet-400 font-medium hover:text-violet-300">Create one</Link>
          </p>
        </div>
      </div>
    </div>
  );
}