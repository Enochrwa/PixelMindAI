import { Link } from 'react-router-dom';
import { Zap, Shield, Globe, ArrowRight } from 'lucide-react';

const tools = [
  { icon: '🧾', name: 'Receipt Scanner', desc: 'Extract merchant, items & totals from any receipt photo' },
  { icon: '🪪', name: 'Passport Photo', desc: '30+ country specs applied automatically' },
  { icon: '🎭', name: 'Deepfake Detector', desc: "First free consumer deepfake detection tool" },
  { icon: '✍️', name: 'Handwriting OCR', desc: 'Convert handwritten notes to digital text' },
  { icon: '🌿', name: 'Plant Disease', desc: 'Detect crop diseases from leaf photos' },
  { icon: '📸', name: 'Background Remover', desc: 'AI background removal with U2Net' },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-950">
      {/* Nav */}
      <nav className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
        <span className="text-2xl font-bold text-white">Pixel<span className="text-indigo-400">Mind</span> AI</span>
        <div className="flex gap-3">
          <Link to="/login" className="btn-secondary">Sign in</Link>
          <Link to="/register" className="btn-primary">Get Started Free</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto max-w-4xl px-6 py-24 text-center">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-indigo-700/40 bg-indigo-700/10 px-4 py-1.5 text-sm text-indigo-400">
          <Zap size={14} /> 43 AI Visual Tools · $0 to start
        </div>
        <h1 className="mt-6 text-5xl font-extrabold text-white sm:text-6xl">
          The Unified Visual<br />
          <span className="bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
            Intelligence OS
          </span>
        </h1>
        <p className="mt-6 text-lg text-gray-400">
          OCR, passport photos, deepfake detection, crop disease AI, background removal — 
          43 professional computer vision tools in one platform. Built for Africa, used worldwide.
        </p>
        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <Link to="/register" className="btn-primary px-8 py-3 text-base">
            Start for Free <ArrowRight size={18} />
          </Link>
          <Link to="/pricing" className="btn-secondary px-8 py-3 text-base">View Pricing</Link>
        </div>
      </section>

      {/* Tools Grid */}
      <section className="mx-auto max-w-6xl px-6 pb-24">
        <h2 className="mb-8 text-center text-2xl font-bold text-white">Featured Tools</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {tools.map((tool) => (
            <div key={tool.name} className="card p-6 transition hover:border-indigo-700/50">
              <div className="mb-3 text-3xl">{tool.icon}</div>
              <h3 className="font-semibold text-white">{tool.name}</h3>
              <p className="mt-1 text-sm text-gray-400">{tool.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-gray-800 bg-gray-900/30 py-16">
        <div className="mx-auto max-w-4xl px-6">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
            {[
              { icon: Zap, title: 'Fast & Async', desc: 'All CV jobs processed async via ARQ queue. Never wait at a spinner.' },
              { icon: Shield, title: 'Secure by Design', desc: 'MIME validation, Pillow integrity checks, rate limiting on every endpoint.' },
              { icon: Globe, title: 'Built for Africa', desc: 'MTN MoMo payments coming. Multilingual OCR (EN/FR/Kinyarwanda). Offline-aware.' },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="text-center">
                <Icon size={32} className="mx-auto mb-3 text-indigo-400" />
                <h3 className="font-semibold text-white">{title}</h3>
                <p className="mt-1 text-sm text-gray-400">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
