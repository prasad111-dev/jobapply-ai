'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { auth } from '@/lib/api';
import toast from 'react-hot-toast';
import { FiUser, FiMail, FiLock, FiType, FiZap, FiArrowRight, FiEye, FiEyeOff } from 'react-icons/fi';

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: '', username: '', password: '', full_name: '' });
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await auth.register(form);
      localStorage.setItem('token', res.data.access_token);
      toast.success('Account created! Now upload your resume.');
      router.push('/profile');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const fields = [
    { name: 'full_name', label: 'Full Name', icon: <FiType />, type: 'text', placeholder: 'John Doe' },
    { name: 'email', label: 'Email', icon: <FiMail />, type: 'email', placeholder: 'john@example.com' },
    { name: 'username', label: 'Username', icon: <FiUser />, type: 'text', placeholder: 'johndoe' },
  ];

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-4xl glass-card overflow-hidden grid md:grid-cols-2">
        <div className="hidden md:flex flex-col justify-between p-10 relative overflow-hidden bg-gradient-to-br from-emerald-600/25 via-teal-600/20 to-sky-600/25">
          <div className="absolute -bottom-20 -right-20 w-64 h-64 rounded-full bg-teal-500/20 blur-[80px]" />
          <div>
            <div className="flex items-center gap-2 mb-8">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-sky-500 flex items-center justify-center shadow-lg">
                <FiZap className="text-white" />
              </div>
              <span className="text-lg font-bold">JobApply<span className="text-gradient">AI</span></span>
            </div>
            <h2 className="text-3xl font-bold mb-4 leading-tight">
              Start applying to<br />100+ jobs today
            </h2>
            <p className="text-slate-300 text-sm leading-relaxed">
              Create your free account and upload your resume. We handle the rest.
            </p>
          </div>
          <div className="space-y-3 text-sm text-slate-300">
            {['Free forever — no credit card', 'AI parses your resume instantly', 'Connect platforms in minutes'].map(t => (
              <div key={t} className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-400" /> {t}
              </div>
            ))}
          </div>
        </div>

        <div className="p-8 md:p-10">
          <h1 className="text-2xl font-bold mb-1">Create Account</h1>
          <p className="text-sm text-slate-400 mb-8">Join and let AI do the applying</p>
          <form onSubmit={handleSubmit} className="space-y-4">
            {fields.map(field => (
              <div key={field.name}>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">{field.label}</label>
                <div className="relative">
                  <span className="absolute left-3.5 top-3.5 text-slate-500">{field.icon}</span>
                  <input type={field.type} className="input-field pl-11" placeholder={field.placeholder}
                    value={(form as any)[field.name]} onChange={e => setForm({...form, [field.name]: e.target.value})} required />
                </div>
              </div>
            ))}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <FiLock className="absolute left-3.5 top-3.5 text-slate-500" />
                <input type={showPw ? 'text' : 'password'} className="input-field pl-11 pr-11" placeholder="Min 8 characters"
                  value={form.password} onChange={e => setForm({...form, password: e.target.value})} required minLength={6} />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-3 text-slate-500 hover:text-slate-300">
                  {showPw ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>
            </div>
            <button type="submit" className="btn-primary w-full py-3" disabled={loading}>
              {loading ? 'Creating account...' : <>Create Account <FiArrowRight /></>}
            </button>
          </form>
          <p className="text-center text-slate-400 mt-6">
            Already have an account?{' '}
            <Link href="/login" className="text-violet-400 font-medium hover:text-violet-300">Login</Link>
          </p>
        </div>
      </div>
    </div>
  );
}