interface CreditMeterProps {
  credits: number;
  maxCredits: number;
  plan: string;
}

export function CreditMeter({ credits, maxCredits, plan }: CreditMeterProps) {
  const pct = Math.min((credits / maxCredits) * 100, 100);
  const color = pct > 40 ? 'bg-indigo-500' : pct > 20 ? 'bg-amber-500' : 'bg-red-500';

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-gray-400">{credits} credits</span>
        <span className="capitalize text-gray-500">{plan}</span>
      </div>
      <div className="h-1.5 rounded-full bg-gray-800">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
