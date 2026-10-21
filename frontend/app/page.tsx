import GymRagAdvisor from '@/components/gymrag-advisor';

export default function Home() {
  return (
    <main className="h-app relative flex w-full flex-col overflow-hidden bg-slate-50">
      {/* Ambient backdrop */}
      <div className="bg-grid pointer-events-none absolute inset-0" />
      <div className="pointer-events-none absolute -top-32 left-1/2 h-72 w-[36rem] -translate-x-1/2 rounded-full bg-teal-300/25 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -right-24 h-72 w-72 rounded-full bg-cyan-300/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -left-24 h-72 w-72 rounded-full bg-sky-300/15 blur-3xl" />

      <div className="relative z-10 flex min-h-0 flex-1 flex-col">
        <GymRagAdvisor />
      </div>
    </main>
  );
}
