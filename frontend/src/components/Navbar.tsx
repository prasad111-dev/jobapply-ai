'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { auth, platforms as platformsApi } from '@/lib/api';
import { FiGrid, FiSearch, FiFileText, FiLayers, FiUser, FiLogOut, FiMenu, FiX, FiZap, FiShield, FiCheckCircle } from 'react-icons/fi';

export default function Navbar() {
  const pathname = usePathname();
  const [user, setUser] = useState<any>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [connectedPlatforms, setConnectedPlatforms] = useState<any[]>([]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      auth.me().then(res => setUser(res.data)).catch(() => {});
      platformsApi.connected().then(res => setConnectedPlatforms(res.data)).catch(() => {});
    }
  }, []);

  const isAdmin = user?.is_admin;

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setMenuOpen(false);
    window.location.href = '/login';
  };

  const navLinks = [
    { href: '/dashboard', label: 'Dashboard', icon: <FiGrid /> },
    { href: '/jobs', label: 'Jobs', icon: <FiSearch /> },
    { href: '/applications', label: 'Applications', icon: <FiFileText /> },
    { href: '/platforms', label: 'Platforms', icon: <FiLayers /> },
    { href: '/profile', label: 'Profile', icon: <FiUser /> },
  ];

  const adminLinks = [
    { href: '/admin', label: 'Admin', icon: <FiShield /> },
  ];

  const isActive = (href: string) => pathname === href || (href !== '/dashboard' && pathname.startsWith(href));

  return (
    <nav className="sticky top-0 z-50 border-b border-white/10 bg-[#070b16]/70 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-violet-500 to-fuchsia-500 shadow-[0_0_20px_-4px_rgba(139,92,246,0.8)] group-hover:shadow-[0_0_28px_-2px_rgba(139,92,246,1)] transition-shadow">
              <FiZap className="text-white text-lg" />
            </div>
            <span className="text-xl font-bold tracking-tight">
              JobApply<span className="text-gradient">AI</span>
            </span>
          </Link>

          <div className="flex items-center gap-1 bg-white/[0.03] border border-white/10 rounded-2xl p-1 overflow-x-auto max-w-[60vw] scrollbar-hide">
            {user && navLinks.map(link => (
              <Link key={link.href} href={link.href}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-medium whitespace-nowrap transition-all duration-200 ${isActive(link.href) ? 'bg-gradient-to-r from-indigo-500/90 to-violet-500/90 text-white shadow-[0_0_16px_-4px_rgba(139,92,246,0.7)]' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}>
                {link.icon}{link.label}
              </Link>
            ))}
            {user && isAdmin && adminLinks.map(link => (
              <Link key={link.href} href={link.href}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs sm:text-sm font-medium whitespace-nowrap transition-all duration-200 ${isActive(link.href) ? 'bg-gradient-to-r from-rose-500/90 to-fuchsia-500/90 text-white shadow-[0_0_16px_-4px_rgba(244,63,94,0.7)]' : 'text-rose-300 hover:text-white hover:bg-white/5'}`}>
                {link.icon}{link.label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            {user ? (
              <div className="flex items-center gap-2 sm:gap-3">
                {connectedPlatforms.length > 0 && (
                  <div className="hidden sm:flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-3 py-1.5">
                    <FiCheckCircle className="text-sm" />
                    {connectedPlatforms.filter((p: any) => p.is_connected).map((p: any) => (
                      <span key={p.platform_name} className="capitalize">{p.platform_name}</span>
                    )).reduce((prev: any, curr: any) => [prev, ', ', curr], [])}
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-fuchsia-500 flex items-center justify-center text-sm font-bold">
                    {(user.full_name || user.username || 'U').charAt(0).toUpperCase()}
                  </div>
                  <span className="hidden sm:block text-sm text-slate-300 font-medium max-w-[120px] truncate">{user.full_name || user.username}</span>
                </div>
                <button onClick={logout} className="btn-ghost p-2" title="Logout"><FiLogOut /></button>
              </div>
            ) : (
              <div className="flex gap-2">
                <Link href="/login" className="btn-secondary text-sm px-3 sm:px-4 py-2">Login</Link>
                <Link href="/register" className="btn-primary text-sm px-3 sm:px-4 py-2">Get Started</Link>
              </div>
            )}
            <button className="hidden text-slate-300 p-2" onClick={() => setMenuOpen(!menuOpen)}>
              {menuOpen ? <FiX className="text-xl" /> : <FiMenu className="text-xl" />}
            </button>
          </div>
        </div>
      </div>

      {false && menuOpen && (
        <div className="md:hidden border-t border-white/10 bg-[#0a0f1f]/95 backdrop-blur-xl">
          <div className="px-4 py-3 space-y-1">
            {user ? (
              <>
                {navLinks.map(link => (
                  <Link key={link.href} href={link.href} onClick={() => setMenuOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium ${isActive(link.href) ? 'bg-white/10 text-white' : 'text-slate-400'}`}>
                    {link.icon}{link.label}
                  </Link>
                ))}
                {isAdmin && adminLinks.map(link => (
                  <Link key={link.href} href={link.href} onClick={() => setMenuOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium ${isActive(link.href) ? 'bg-white/10 text-rose-300' : 'text-rose-300'}`}>
                    {link.icon}{link.label}
                  </Link>
                ))}
                <button onClick={logout} className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-rose-300">
                  <FiLogOut /> Logout
                </button>
              </>
            ) : (
              <div className="flex gap-2 pt-2">
                <Link href="/login" onClick={() => setMenuOpen(false)} className="btn-secondary flex-1 text-sm">Login</Link>
                <Link href="/register" onClick={() => setMenuOpen(false)} className="btn-primary flex-1 text-sm">Get Started</Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}