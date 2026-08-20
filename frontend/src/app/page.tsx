import Link from 'next/link';
import { FiArrowRight, FiZap, FiCheckCircle, FiLayers, FiShield, FiMail, FiTrendingUp, FiStar } from 'react-icons/fi';

const platforms = ['Naukri', 'Indeed', 'LinkedIn', 'Glassdoor', 'Unstop', 'Internshala', 'Foundit', 'Shine'];

const features = [
  { icon: <FiLayers className="text-2xl" />, title: 'Connect Every Platform', desc: 'Naukri, Indeed, LinkedIn, Unstop and 10+ job boards — one account, one dashboard.', grad: 'from-sky-500/20 to-indigo-500/20', iconColor: 'text-sky-400' },
  { icon: <FiZap className="text-2xl" />, title: 'AI Auto-Fill, Zero Typing', desc: 'Upload your resume once. AI extracts your profile and fills every application form for you.', grad: 'from-violet-500/20 to-fuchsia-500/20', iconColor: 'text-violet-400' },
  { icon: <FiTrendingUp className="text-2xl" />, title: 'One-Click Bulk Apply', desc: 'Auto-apply to your best-matching jobs every day. Set it once, apply forever.', grad: 'from-emerald-500/20 to-teal-500/20', iconColor: 'text-emerald-400' },
  { icon: <FiMail className="text-2xl" />, title: 'Daily Job Digest', desc: 'New matching jobs emailed to you automatically. Never miss a role again.', grad: 'from-amber-500/20 to-orange-500/20', iconColor: 'text-amber-400' },
];

const stats = [
  { value: '10+', label: 'Platforms' },
  { value: '1-Click', label: 'Bulk Apply' },
  { value: '100%', label: 'AI Auto-Fill' },
  { value: '24/7', label: 'Auto-Scraping' },
];

export default function Home() {
  return (
    <div className="relative">
      <section className="max-w-7xl mx-auto px-4 pt-20 pb-16 md:pt-28 md:pb-24 text-center relative">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-violet-500/30 bg-violet-500/10 text-violet-300 text-sm font-medium mb-8 animate-pulse-glow">
          <FiZap className="text-xs" /> AI-powered job application engine
        </div>
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.05] mb-6">
          Apply to <span className="text-gradient">100+ Jobs</span><br />with a Single Click
        </h1>
        <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Connect your job accounts once, upload your resume, and let AI apply to
          every matching job for you — automatically, around the clock.
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-4">
          <Link href="/register" className="btn-primary text-lg px-8 py-3.5">
            Get Started Free <FiArrowRight />
          </Link>
          <Link href="/login" className="btn-secondary text-lg px-8 py-3.5">
            Login to Dashboard
          </Link>
        </div>

        <div className="mt-12 flex flex-wrap justify-center gap-2.5">
          {platforms.map(p => (
            <span key={p} className="px-4 py-1.5 rounded-full text-sm text-slate-300 bg-white/[0.05] border border-white/10 hover:border-violet-400/40 transition-colors">
              {p}
            </span>
          ))}
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-4 py-10">
        <div className="glass-card p-8 md:p-10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {stats.map(s => (
              <div key={s.label}>
                <div className="text-3xl md:text-4xl font-extrabold text-gradient">{s.value}</div>
                <div className="text-sm text-slate-400 mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="section-title mb-3">Everything Your Job Search Needs</h2>
          <p className="text-slate-400 max-w-xl mx-auto">One platform to find, match, apply and track — no more juggling tabs and forms.</p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((f, i) => (
            <div key={i} className="glass-card-hover p-6 group">
              <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${f.grad} flex items-center justify-center mb-5 ${f.iconColor} group-hover:scale-110 transition-transform`}>
                {f.icon}
              </div>
              <h3 className="text-lg font-bold mb-2">{f.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-4 py-16">
        <div className="glass-card p-8 md:p-12 relative overflow-hidden">
          <div className="absolute -top-24 -right-24 w-72 h-72 rounded-full bg-violet-600/20 blur-[90px]" />
          <div className="relative flex flex-col md:flex-row items-center gap-8 text-center md:text-left">
            <div>
              <div className="flex items-center justify-center md:justify-start gap-1 mb-4">
                {[...Array(5)].map((_, i) => <FiStar key={i} className="text-amber-400 fill-amber-400" />)}
              </div>
              <h2 className="text-2xl md:text-3xl font-bold mb-3">Apply Smarter, Not Harder</h2>
              <p className="text-slate-400 mb-6 max-w-md">
                Join thousands of job seekers who stopped copy-pasting and started letting AI do the work.
              </p>
              <Link href="/register" className="btn-primary text-lg px-8 py-3.5 inline-flex">
                Start Now — It&apos;s Free <FiArrowRight />
              </Link>
            </div>
            <div className="flex-1 w-full">
              <div className="glass-card p-6 space-y-4">
                {[
                  { icon: <FiShield className="text-emerald-400" />, text: 'Credentials encrypted & sessions saved securely' },
                  { icon: <FiCheckCircle className="text-sky-400" />, text: 'Resume uploaded once — everything auto-filled' },
                  { icon: <FiZap className="text-amber-400" />, text: 'New matching jobs applied for you daily' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3 text-sm text-slate-300">
                    <span className="w-9 h-9 rounded-xl bg-white/[0.06] flex items-center justify-center shrink-0">{item.icon}</span>
                    {item.text}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/10 py-10 mt-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-slate-500">
          <span className="font-semibold text-slate-300">JobApply<span className="text-gradient">AI</span></span> — Apply to multiple job platforms from one place.
        </div>
      </footer>
    </div>
  );
}