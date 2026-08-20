export default function Background() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      <div className="absolute inset-0 bg-grid" />
      <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-indigo-600/20 blur-[120px] animate-pulse-glow" />
      <div className="absolute top-1/3 -right-40 w-[500px] h-[500px] rounded-full bg-fuchsia-600/15 blur-[120px] animate-pulse-glow" style={{ animationDelay: '2s' }} />
      <div className="absolute -bottom-40 left-1/3 w-[550px] h-[550px] rounded-full bg-violet-700/20 blur-[130px] animate-pulse-glow" style={{ animationDelay: '1s' }} />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#070b16]" />
    </div>
  );
}