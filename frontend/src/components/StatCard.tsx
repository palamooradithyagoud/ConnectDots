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
    brand: "bg-brand/15 text-brand border-brand/30",
    success: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    warning: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    error: "bg-rose-500/15 text-rose-400 border-rose-500/30",
  };

  return (
    <div className="glass-panel glass-panel-hover rounded-xs p-6 relative overflow-hidden flex flex-col justify-between">
      {/* Top accent line */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-brand/40 to-transparent" />

      <div>
        <div className="flex items-center justify-between">
          <span className="text-[0.7rem] font-bold tracking-[0.2em] uppercase text-white/50">
            {label}
          </span>
          <div className="flex h-8 w-8 items-center justify-center rounded-xs bg-white/5 border border-white/10 text-brand">
            <Icon className="h-4 w-4" />
          </div>
        </div>

        <div className="mt-4 flex items-baseline gap-2">
          <span className="text-3xl lg:text-4xl font-black tracking-tight text-white font-mono">
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
        <p className="mt-4 text-xs font-medium text-white/40 border-t border-white/5 pt-3">
          {subtitle}
        </p>
      )}
    </div>
  );
}
