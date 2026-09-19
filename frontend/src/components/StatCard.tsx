import { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  badgeText?: string;
  badgeType?: "success" | "warning" | "error" | "brand";
}

export default function StatCard({
  label,
  value,
  subtitle,
  icon: Icon,
  badgeText,
  badgeType = "brand",
}: StatCardProps) {
  const badgeColors = {
    brand: "bg-brand/15 text-brand-300 border-brand/30",
    success: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    warning: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    error: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  };

  return (
    <div className="group relative overflow-hidden rounded-xl border border-white/10 bg-midnight-card/80 p-5 backdrop-blur-xl transition-all duration-300 hover:border-brand/40 hover:shadow-xl hover:shadow-brand/5 flex flex-col justify-between">
      {/* Top accent line */}
      <div className="absolute top-0 inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-brand/30 to-transparent group-hover:via-brand/70 transition-all duration-500" />

      <div>
        <div className="flex items-center justify-between gap-2">
          <span className="text-[0.68rem] font-bold tracking-wider uppercase text-white/60 font-mono">
            {label}
          </span>
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/[0.04] text-brand-300 group-hover:border-brand/40 group-hover:bg-brand/10 transition-colors">
            <Icon className="h-4 w-4" />
          </div>
        </div>

        <div className="mt-3 flex items-baseline flex-wrap gap-2">
          <span className="text-2xl sm:text-3xl font-black tracking-tight text-white font-mono">
            {value}
          </span>
          {badgeText && (
            <span className={`text-[0.65rem] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${badgeColors[badgeType]}`}>
              {badgeText}
            </span>
          )}
        </div>
      </div>

      {subtitle && (
        <p className="mt-3 text-xs text-white/45 border-t border-white/[0.06] pt-2.5 font-sans leading-relaxed">
          {subtitle}
        </p>
      )}
    </div>
  );
}
