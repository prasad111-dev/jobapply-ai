interface StatsCardProps { title: string; value: string | number; icon: React.ReactNode; color: string; }

export default function StatsCard({ title, value, icon, color }: StatsCardProps) {
  const gradients: Record<string, string> = {
    blue: 'from-sky-500/25 to-indigo-500/25 text-sky-400 shadow-[0_0_24px_-8px_rgba(56,189,248,0.6)]',
    green: 'from-emerald-500/25 to-teal-500/25 text-emerald-400 shadow-[0_0_24px_-8px_rgba(52,211,153,0.6)]',
    yellow: 'from-amber-500/25 to-orange-500/25 text-amber-400 shadow-[0_0_24px_-8px_rgba(251,191,36,0.6)]',
    red: 'from-rose-500/25 to-red-500/25 text-rose-400 shadow-[0_0_24px_-8px_rgba(251,113,133,0.6)]',
    purple: 'from-violet-500/25 to-fuchsia-500/25 text-violet-400 shadow-[0_0_24px_-8px_rgba(167,139,250,0.6)]',
  };
  return (
    <div className="glass-card-hover p-5 flex items-center gap-4">
      <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br flex items-center justify-center text-xl shrink-0 ${gradients[color] || gradients.blue}`}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-slate-400 text-xs font-medium uppercase tracking-wider truncate">{title}</p>
        <p className="text-2xl font-extrabold text-white leading-tight">{value}</p>
      </div>
    </div>
  );
}