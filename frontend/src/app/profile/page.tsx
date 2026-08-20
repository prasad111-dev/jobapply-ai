'use client';
import { useEffect, useState, useRef } from 'react';
import { profile } from '@/lib/api';
import toast from 'react-hot-toast';
import { FiUpload, FiUser, FiPhone, FiMapPin, FiLinkedin, FiGlobe, FiSave, FiCheckCircle, FiBriefcase, FiLoader } from 'react-icons/fi';

export default function ProfilePage() {
  const [form, setForm] = useState<any>({});
  const [parsedData, setParsedData] = useState<any>(null);
  const [autoFilled, setAutoFilled] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    profile.get().then(r => {
      const prefs = r.data.preferences || {};
      setForm({ ...r.data, ...prefs, preferences: prefs });
      if (r.data.skills?.length) setParsedData({ skills: r.data.skills, experience_years: r.data.experience_years, education: r.data.education });
    }).catch(() => {});
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const res = await profile.uploadResume(file);
      setParsedData(res.data.parsed_data);
      setAutoFilled(res.data.auto_filled);
      toast.success('Resume uploaded & parsed! Profile auto-filled.');
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Upload failed'); }
    setUploading(false);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const { preferences, ...rest } = form;
      await profile.update({ ...rest, preferences });
      toast.success('Profile updated!');
    } catch { toast.error('Update failed'); }
    setSaving(false);
  };

  const setPref = (key: string, value: any) => {
    setForm({ ...form, preferences: { ...(form.preferences || {}), [key]: value }, [key]: value });
  };

  const isFresher = (Number(form.experience_years) || 0) === 0;
  const setExperienceType = (type: 'fresher' | 'experienced') => {
    setForm({ ...form, experience_years: type === 'fresher' ? 0 : 1 });
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-extrabold tracking-tight mb-2">My Profile</h1>
      <p className="text-slate-400 mb-8">One resume upload fills everything — fill once, applied everywhere.</p>

      <div className="glass-card p-6 mb-6 relative overflow-hidden">
        <div className="absolute -top-16 -right-16 w-48 h-48 rounded-full bg-fuchsia-600/15 blur-[70px]" />
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2.5">
          <span className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500/25 to-violet-500/25 text-indigo-400 flex items-center justify-center"><FiUpload /></span>
          Resume — AI auto-fills everything
        </h2>
        <div className="border-2 border-dashed border-white/15 rounded-2xl p-8 text-center hover:border-violet-400/50 transition-colors cursor-pointer bg-white/[0.02]" onClick={() => fileRef.current?.click()}>
          <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden" onChange={handleUpload} />
          {uploading ? (
            <div className="flex items-center justify-center gap-2 text-slate-300"><FiLoader className="animate-spin" /> Parsing resume with AI...</div>
          ) : parsedData ? (
            <div>
              <p className="text-emerald-400 mb-2 flex items-center justify-center gap-2 font-medium"><FiCheckCircle /> Resume uploaded &amp; parsed!</p>
              <p className="text-sm text-slate-400">Skills found: <span className="text-slate-200 font-medium">{parsedData.skills?.length || 0}</span> · Experience: <span className="text-slate-200 font-medium">{parsedData.experience_years || 0} years</span></p>
            </div>
          ) : (
            <div>
              <FiUpload className="text-3xl text-slate-500 mx-auto mb-3" />
              <p className="text-slate-300 font-medium mb-1">Click to upload resume (PDF or DOCX)</p>
              <p className="text-sm text-slate-500">Name, phone, location, skills &amp; education filled automatically</p>
            </div>
          )}
        </div>

        {autoFilled && (
          <div className="mt-4 bg-emerald-500/[0.08] border border-emerald-500/30 rounded-xl p-4">
            <p className="text-sm text-emerald-300 font-medium mb-2.5 flex items-center gap-1.5"><FiCheckCircle /> AI auto-filled from resume:</p>
            <div className="flex flex-wrap gap-2">
              {autoFilled.full_name && <span className="badge-green">{autoFilled.full_name}</span>}
              {autoFilled.phone && <span className="badge-green">{autoFilled.phone}</span>}
              {autoFilled.location && <span className="badge-green">{autoFilled.location}</span>}
              {autoFilled.linkedin_url && <span className="badge-green">LinkedIn found</span>}
              <span className="badge-green">{autoFilled.skills_count || 0} skills</span>
            </div>
            <p className="text-xs text-slate-500 mt-2">Edit any field below if needed, then save.</p>
          </div>
        )}
        {parsedData?.skills?.length > 0 && (
          <div className="mt-4">
            <p className="text-sm text-slate-400 mb-2">Extracted Skills:</p>
            <div className="flex flex-wrap gap-2">
              {parsedData.skills.map((s: string) => <span key={s} className="badge-blue">{s}</span>)}
            </div>
          </div>
        )}
      </div>

      <div className="glass-card p-6 mb-6">
        <h2 className="text-xl font-bold mb-5 flex items-center gap-2.5">
          <span className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500/25 to-indigo-500/25 text-sky-400 flex items-center justify-center"><FiUser /></span>
          Personal Info
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          {[
            { name: 'full_name', label: 'Full Name', icon: <FiUser /> },
            { name: 'phone', label: 'Phone', icon: <FiPhone /> },
            { name: 'location', label: 'Location', icon: <FiMapPin /> },
            { name: 'linkedin_url', label: 'LinkedIn URL', icon: <FiLinkedin /> },
            { name: 'portfolio_url', label: 'Portfolio URL', icon: <FiGlobe /> },
          ].map(field => (
            <div key={field.name}>
              <label className="block text-sm text-slate-400 mb-1.5">{field.label}</label>
              <div className="relative">
                <span className="absolute left-3.5 top-3 text-slate-500">{field.icon}</span>
                <input className="input-field pl-11" value={form[field.name] || ''} onChange={e => setForm({...form, [field.name]: e.target.value})} />
              </div>
            </div>
          ))}
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Experience Level</label>
            <div className="grid grid-cols-2 gap-2">
              <button type="button" onClick={() => setExperienceType('fresher')}
                className={`px-4 py-2.5 rounded-xl text-sm font-medium border transition-all ${isFresher ? 'bg-gradient-to-r from-indigo-500/90 to-violet-500/90 text-white border-transparent shadow-lg' : 'bg-white/[0.03] text-slate-300 border-white/10 hover:bg-white/5'}`}>
                Fresher / Intern
              </button>
              <button type="button" onClick={() => setExperienceType('experienced')}
                className={`px-4 py-2.5 rounded-xl text-sm font-medium border transition-all ${!isFresher ? 'bg-gradient-to-r from-indigo-500/90 to-violet-500/90 text-white border-transparent shadow-lg' : 'bg-white/[0.03] text-slate-300 border-white/10 hover:bg-white/5'}`}>
                Experienced
              </button>
            </div>
            {!isFresher && (
              <input type="number" min="0" className="input-field mt-2" placeholder="e.g. 3"
                value={form.experience_years || ''} onChange={e => setForm({...form, experience_years: parseInt(e.target.value) || 0})} />
            )}
          </div>
        </div>
        <button onClick={handleSave} disabled={saving} className="btn-primary mt-6 px-6 py-2.5">
          <FiSave /> {saving ? 'Saving...' : 'Save Profile'}
        </button>
      </div>

      <div className="glass-card p-6">
        <h2 className="text-xl font-bold mb-2 flex items-center gap-2.5">
          <span className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500/25 to-orange-500/25 text-amber-400 flex items-center justify-center"><FiBriefcase /></span>
          Application Answers
        </h2>
        <p className="text-sm text-slate-500 mb-5">Used to auto-answer common application questions — fill once, reused everywhere.</p>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Expected Salary (₹)</label>
            <input className="input-field" placeholder="e.g. 1800000" value={form.preferences?.expected_salary || ''} onChange={e => setPref('expected_salary', e.target.value)} />
          </div>
          {!isFresher && (
            <div>
              <label className="block text-sm text-slate-400 mb-1.5">Current Salary (₹)</label>
              <input className="input-field" placeholder="e.g. 1200000" value={form.preferences?.current_salary || ''} onChange={e => setPref('current_salary', e.target.value)} />
            </div>
          )}
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Notice Period</label>
            <select className="input-field" value={form.preferences?.notice_period || ''} onChange={e => setPref('notice_period', e.target.value)}>
              <option value="">Select</option>
              <option value="Immediate">Immediate</option>
              <option value="15 days">15 days</option>
              <option value="30 days">30 days</option>
              <option value="60 days">60 days</option>
              <option value="90 days">90 days</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Availability</label>
            <select className="input-field" value={form.preferences?.availability || ''} onChange={e => setPref('availability', e.target.value)}>
              <option value="">Select</option>
              <option value="Immediate">Immediate</option>
              <option value="2 weeks">2 weeks</option>
              <option value="1 month">1 month</option>
              <option value="After notice period">After notice period</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Work Authorization</label>
            <select className="input-field" value={form.preferences?.work_authorization || ''} onChange={e => setPref('work_authorization', e.target.value)}>
              <option value="">Select</option>
              <option value="Yes, authorized to work">Yes, authorized to work</option>
              <option value="Visa sponsorship needed">Visa sponsorship needed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Preferred Location</label>
            <input className="input-field" placeholder="e.g. Bengaluru" value={form.preferences?.preferred_location || ''} onChange={e => setPref('preferred_location', e.target.value)} />
          </div>
          {isFresher ? (
            <>
              <div>
                <label className="block text-sm text-slate-400 mb-1.5">Internship Company</label>
                <input className="input-field" placeholder="e.g. Infosys" value={form.preferences?.current_company || ''} onChange={e => setPref('current_company', e.target.value)} />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1.5">Internship Role / Title</label>
                <input className="input-field" placeholder="e.g. Software Intern" value={form.preferences?.current_title || ''} onChange={e => setPref('current_title', e.target.value)} />
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block text-sm text-slate-400 mb-1.5">Current Company</label>
                <input className="input-field" value={form.preferences?.current_company || ''} onChange={e => setPref('current_company', e.target.value)} />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1.5">Current Title</label>
                <input className="input-field" value={form.preferences?.current_title || ''} onChange={e => setPref('current_title', e.target.value)} />
              </div>
            </>
          )}
        </div>
        <button onClick={handleSave} disabled={saving} className="btn-primary mt-6 px-6 py-2.5">
          <FiSave /> {saving ? 'Saving...' : 'Save Answers'}
        </button>
      </div>
    </div>
  );
}