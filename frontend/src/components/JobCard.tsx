import { FiMapPin, FiDollarSign, FiClock, FiExternalLink, FiZap } from 'react-icons/fi';

interface JobCardProps {
  job: any;
  selected?: boolean;
  onSelect?: (id: number) => void;
  onApply?: (id: number) => void;
}

export default function JobCard({ job, selected, onSelect, onApply }: JobCardProps) {
  const score = job.match_score ?? 0;
  const matchColor = score >= 0.8 ? 'badge-green' : score >= 0.5 ? 'badge-yellow' : 'badge-red';
  const matchRing = score >= 0.8 ? 'from-emerald-400/40 to-teal-400/40' : score >= 0.5 ? 'from-amber-400/40 to-orange-400/40' : 'from-rose-400/40 to-red-400/40';

  return (
    <div className={`glass-card-hover p-5 group ${selected ? 'border-violet-400/50 bg-violet-500/[0.06] shadow-[0_0_30px_-8px_rgba(139,92,246,0.5)]' : ''}`}
      onClick={() => onSelect?.(job.id)}>
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="min-w-0">
          <h3 className="text-lg font-bold text-white truncate group-hover:text-violet-300 transition-colors">{job.title}</h3>
          <p className="text-violet-400 text-sm font-medium truncate">{job.company}</p>
        </div>
        <div className="relative shrink-0">
          <div className={`w-14 h-14 rounded-full bg-gradient-to-br ${matchRing} p-[2px]`}>
            <div className="w-full h-full rounded-full bg-[#0d1326] flex flex-col items-center justify-center">
              <span className="text-sm font-extrabold text-white leading-none">{Math.round(score * 100)}%</span>
              <span className="text-[9px] text-slate-400">match</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-sm text-slate-400 mb-3">
        {job.location && <span className="flex items-center gap-1.5"><FiMapPin className="text-slate-500" />{job.location}</span>}
        {(job.salary_min || job.salary_max) && (
          <span className="flex items-center gap-1.5">
            <FiDollarSign className="text-slate-500" />
            {job.salary_min ? `₹${(job.salary_min/1000).toFixed(0)}k` : ''}
            {job.salary_min && job.salary_max ? ' - ' : ''}
            {job.salary_max ? `₹${(job.salary_max/1000).toFixed(0)}k` : ''}
          </span>
        )}
        <span className="flex items-center gap-1.5 capitalize"><FiClock className="text-slate-500" />{job.job_type}</span>
        {job.remote_option && <span className="badge-green">Remote</span>}
      </div>

      {(job.skills_required || []).length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {(job.skills_required || []).slice(0, 4).map((skill: string) => (
            <span key={skill} className="px-2.5 py-0.5 rounded-full text-xs bg-white/[0.05] border border-white/10 text-slate-300">{skill}</span>
          ))}
          {(job.skills_required || []).length > 4 && (
            <span className="px-2.5 py-0.5 rounded-full text-xs text-slate-500">+{(job.skills_required || []).length - 4} more</span>
          )}
        </div>
      )}

      <div className="flex items-center justify-between pt-3 border-t border-white/[0.06]">
        <span className="text-xs text-slate-500 capitalize flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-violet-400" /> via {job.platform_source}
        </span>
        <div className="flex items-center gap-2">
          {job.platform_url && (
            <a href={job.platform_url} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}
              className="text-slate-400 hover:text-white p-2 transition-colors" title="Open job posting">
              <FiExternalLink />
            </a>
          )}
          {onApply && (
            <button onClick={(e) => { e.stopPropagation(); onApply(job.id); }} className="btn-primary text-sm px-4 py-1.5">
              <FiZap className="text-xs" /> Quick Apply
            </button>
          )}
        </div>
      </div>
    </div>
  );
}