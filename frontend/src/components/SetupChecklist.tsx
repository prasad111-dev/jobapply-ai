'use client';
import { useEffect, useState } from 'react';
import { profile as profileApi } from '@/lib/api';
import Link from 'next/link';
import { FiCheckCircle, FiXCircle, FiArrowRight, FiUser, FiShield, FiFileText, FiZap } from 'react-icons/fi';

export default function SetupChecklist({ compact = false }: { compact?: boolean }) {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    profileApi.readiness().then(r => setData(r.data)).catch(() => {});
  }, []);

  if (!data) return null;

  const { profile, connections, ready } = data;
  const connectedWithCreds = connections.filter((c: any) => c.has_credentials);

  return (
    <div className={`glass-card ${compact ? 'p-4' : 'p-6'} relative overflow-hidden`}>
      <div className="absolute -top-12 -right-12 w-40 h-40 rounded-full bg-violet-600/10 blur-[60px]" />
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h3 className="font-bold flex items-center gap-2">
          <span className={`w-8 h-8 rounded-lg flex items-center justify-center ${ready ? 'bg-emerald-500/20 text-emerald-400' : 'bg-violet-500/20 text-violet-400'}`}>
            <FiZap />
          </span>
          {ready ? 'Ready to Auto-Apply!' : 'Setup for One-Click Apply'}
        </h3>
        <span className={`badge ${ready ? 'badge-green' : 'badge-yellow'}`}>
          {profile.score}% complete
        </span>
      </div>

      <div className={`flex items-center gap-1 mb-5 ${compact ? '' : ''}`}>
        {[1, 2, 3].map(step => {
          const active = step === 1 && profile.complete ? true : step === 2 && connectedWithCreds.length > 0 ? true : step === 3 && ready ? true : false;
          const reached = step === 1 ? profile.complete : step === 2 ? profile.complete && connectedWithCreds.length > 0 : ready;
          return (
            <div key={step} className="flex-1">
              <div className={`h-1.5 rounded-full ${reached ? 'bg-gradient-to-r from-indigo-500 to-violet-500' : 'bg-white/10'}`} />
              <p className={`text-[10px] mt-1.5 font-medium ${reached ? 'text-violet-300' : 'text-slate-500'}`}>
                {step === 1 ? '1. Profile' : step === 2 ? '2. Connect' : '3. Apply'}
              </p>
            </div>
          );
        })}
      </div>

      <div className="grid md:grid-cols-2 gap-3">
        <div className={`rounded-xl border p-3.5 ${profile.complete ? 'border-emerald-500/30 bg-emerald-500/[0.04]' : 'border-white/10 bg-white/[0.03]'}`}>
          <p className="text-sm font-semibold mb-2 flex items-center gap-1.5 text-slate-200">
            <FiUser className={profile.complete ? 'text-emerald-400' : 'text-slate-500'} />
            Profile
          </p>
          {profile.complete ? (
            <p className="text-xs text-emerald-300 flex items-center gap-1.5"><FiCheckCircle /> All done — resume, contact, skills &amp; answers set</p>
          ) : (
            <Link href="/profile" className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1.5">
              {profile.missing?.length || 0} steps remaining <FiArrowRight />
            </Link>
          )}
        </div>

        <div className={`rounded-xl border p-3.5 ${connectedWithCreds.length > 0 ? 'border-emerald-500/30 bg-emerald-500/[0.04]' : 'border-white/10 bg-white/[0.03]'}`}>
          <p className="text-sm font-semibold mb-2 flex items-center gap-1.5 text-slate-200">
            <FiShield className={connectedWithCreds.length > 0 ? 'text-emerald-400' : 'text-slate-500'} />
            Platforms Connected
          </p>
          {connectedWithCreds.length > 0 ? (
            <p className="text-xs text-emerald-300 flex items-center gap-1.5"><FiCheckCircle /> {connectedWithCreds.map((c: any) => c.platform_name).join(', ')}</p>
          ) : (
            <Link href="/platforms" className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1.5">
              Connect Naukri / Internshala <FiArrowRight />
            </Link>
          )}
        </div>
      </div>

      {ready && (
        <p className="mt-4 text-xs text-slate-400 flex items-center gap-1.5">
          <FiFileText className="text-emerald-400" /> Pick multiple jobs on the Jobs page — one click applies to all automatically.
        </p>
      )}
    </div>
  );
}