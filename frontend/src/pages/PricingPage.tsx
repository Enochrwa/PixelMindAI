import { Link } from 'react-router-dom';
import { Check } from 'lucide-react';

const plans = [
  {
    name: 'Free',
    price: '$0',
    credits: 30,
    features: ['30 credits/month', 'All 43 tools', '24h file retention', '200 req/min'],
    cta: 'Get started',
    highlight: false,
  },
  {
    name: 'Starter',
    price: '$9',
    credits: 300,
    features: [
      '300 credits/month',
      'All 43 tools',
      '7-day file retention',
      'Priority queue',
      'Email support',
    ],
    cta: 'Upgrade',
    highlight: true,
  },
  {
    name: 'Pro',
    price: '$29',
    credits: 1500,
    features: [
      '1,500 credits/month',
      'All 43 tools',
      '30-day retention',
      'API access',
      'Batch processing',
      'Priority support',
    ],
    cta: 'Upgrade',
    highlight: false,
  },
];

export function PricingPage() {
  return (
    <div className="min-h-screen bg-gray-950 px-6 py-24">
      <div className="mx-auto max-w-4xl text-center">
        <h1 className="text-4xl font-bold text-white">Simple, transparent pricing</h1>
        <p className="mt-4 text-gray-400">Start free. Upgrade when you need more.</p>
      </div>
      <div className="mx-auto mt-16 grid max-w-4xl grid-cols-1 gap-6 sm:grid-cols-3">
        {plans.map((plan) => (
          <div
            key={plan.name}
            className={`card p-8 ${plan.highlight ? 'border-indigo-600 ring-1 ring-indigo-600' : ''}`}
          >
            <h3 className="font-semibold text-white">{plan.name}</h3>
            <p className="mt-2 text-4xl font-bold text-white">
              {plan.price}
              <span className="text-base font-normal text-gray-400">/mo</span>
            </p>
            <ul className="mt-6 space-y-3">
              {plan.features.map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm text-gray-300">
                  <Check size={14} className="shrink-0 text-indigo-400" />
                  {f}
                </li>
              ))}
            </ul>
            <Link
              to="/register"
              className={`mt-8 block w-full rounded-xl py-2.5 text-center text-sm font-semibold transition ${
                plan.highlight
                  ? 'bg-indigo-700 text-white hover:bg-indigo-600'
                  : 'border border-gray-700 text-gray-300 hover:border-gray-600'
              }`}
            >
              {plan.cta}
            </Link>
          </div>
        ))}
      </div>
      <p className="mt-8 text-center text-sm text-gray-500">
        <Link to="/" className="text-indigo-400 hover:underline">
          ← Back home
        </Link>
      </p>
    </div>
  );
}
