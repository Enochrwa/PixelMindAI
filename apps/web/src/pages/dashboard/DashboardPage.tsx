import { Link } from 'react-router-dom';
import { Zap, ScanText, Image, Sparkles, BarChart3, Sprout, Smile } from 'lucide-react';

const modules = [
  { icon: ScanText, label: 'OCR & Documents', tools: 8, slug: 'receipt-scanner', color: 'indigo' },
  { icon: Image, label: 'Photo Intelligence', tools: 7, slug: 'background-remover', color: 'cyan' },
  { icon: Sparkles, label: 'Creator Studio', tools: 7, slug: 'caption-lens', color: 'violet' },
  { icon: BarChart3, label: 'Business Intel', tools: 8, slug: 'shelf-counter', color: 'amber' },
  { icon: Sprout, label: 'Agriculture AI', tools: 6, slug: 'plant-disease-detector', color: 'green' },
  { icon: Smile, label: 'Entertainment', tools: 7, slug: 'age-predictor', color: 'pink' },
];

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-400">43 AI tools at your fingertips</p>
      </div>

      {/* Credit banner */}
      <div className="card flex items-center justify-between p-5">
        <div className="flex items-center gap-3">
          <Zap className="text-indigo-400" size={20} />
          <div>
            <p className="text-sm font-medium text-white">Credits Remaining</p>
            <p className="text-xs text-gray-400">Resets monthly on paid plans</p>
          </div>
        </div>
        <Link to="/account" className="btn-secondary text-xs">Upgrade</Link>
      </div>

      {/* Module grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {modules.map(({ icon: Icon, label, tools, slug }) => (
          <Link key={slug} to={`/tools/${slug}`}
            className="card group p-6 transition hover:border-indigo-700/60 hover:bg-gray-900">
            <Icon size={24} className="mb-3 text-indigo-400 transition group-hover:scale-110" />
            <h3 className="font-semibold text-white">{label}</h3>
            <p className="mt-1 text-sm text-gray-400">{tools} tools</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
