import React from "react";
import { cn } from "@/lib/utils";

interface BrandLogoTextProps {
  className?: string;
  showSubtitle?: boolean;
}

export default function BrandLogoText({
  className,
  showSubtitle = true,
}: BrandLogoTextProps) {
  return (
    <div className={cn("flex flex-col select-none", className)}>
      <div className="uiverse-brand-btn" aria-label="CONNECTDOTS" title="ConnectDots AI Intelligence">
        <span className="uiverse-brand-box">C</span>
        <span className="uiverse-brand-box">O</span>
        <span className="uiverse-brand-box">N</span>
        <span className="uiverse-brand-box">N</span>
        <span className="uiverse-brand-box">E</span>
        <span className="uiverse-brand-box">C</span>
        <span className="uiverse-brand-box">T</span>
        <span className="uiverse-brand-box box-accent">D</span>
        <span className="uiverse-brand-box box-accent">O</span>
        <span className="uiverse-brand-box box-accent">T</span>
        <span className="uiverse-brand-box box-accent">S</span>
      </div>
      {showSubtitle && (
        <span className="text-[0.52rem] sm:text-[0.58rem] font-bold tracking-[0.18em] text-violet-300/60 uppercase mt-0.5 whitespace-nowrap">
          AI Crime Intelligence Platform
        </span>
      )}
    </div>
  );
}
