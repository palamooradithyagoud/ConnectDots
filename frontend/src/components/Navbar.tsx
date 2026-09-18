"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { Shield, UploadCloud, Database, MapPin, BarChart3, Activity, Sparkles, TrendingUp } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { label: "Overview", href: "/", icon: BarChart3 },
    { label: "Crime Explorer", href: "/crimes", icon: Database },
    { label: "Analytics", href: "/analytics", icon: TrendingUp },
    { label: "Semantic Search", href: "/search", icon: Sparkles },
    { label: "Ingestion Pipeline", href: "/import", icon: UploadCloud },
    { label: "Spatial Map", href: "/map", icon: MapPin },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-midnight/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-12">
        {/* Brand Logo & Name */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-lg border border-brand/40 bg-midnight/90 shadow-brand-glow transition-transform duration-300 group-hover:scale-105 group-hover:border-brand">
            <Image
              src="/logo.png"
              alt="ConnectDots Logo"
              width={40}
              height={40}
              className="h-full w-full object-cover"
              priority
            />
          </div>
          <div className="flex flex-col">
            <span className="text-base font-black tracking-wider text-white uppercase font-mono">
              Connect<span className="text-brand">Dots</span>
            </span>
            <span className="text-[0.62rem] font-bold tracking-[0.2em] text-white/50 uppercase">
              AI Crime Intelligence · Phase 3
            </span>
          </div>
        </Link>

        {/* Navigation Links with animated brand underlines */}
        <nav className="hidden md:flex items-center gap-8">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`group relative flex items-center gap-2 text-[0.78rem] font-bold uppercase tracking-[0.12em] transition-colors duration-200 ${
                  isActive ? "text-white" : "text-white/50 hover:text-white"
                }`}
              >
                <Icon className={`h-4 w-4 transition-colors ${isActive ? "text-brand" : "text-white/40 group-hover:text-white"}`} />
                {item.label}
                <span
                  className={`absolute -bottom-2 left-0 h-[2px] bg-brand transition-all duration-300 ease-out ${
                    isActive ? "w-full" : "w-0 group-hover:w-full"
                  }`}
                />
              </Link>
            );
          })}
        </nav>

        {/* Action Controls & Health */}
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[0.7rem] font-medium text-emerald-400">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
            </span>
            PostGIS Active
          </div>

          <Link
            href="/import"
            className="btn-metallic inline-flex items-center gap-1.5 rounded-xs px-4 py-2 text-[0.75rem] font-black uppercase tracking-wider shadow-sm"
          >
            <UploadCloud className="h-4 w-4" />
            Import Data
          </Link>
        </div>
      </div>
    </header>
  );
}
