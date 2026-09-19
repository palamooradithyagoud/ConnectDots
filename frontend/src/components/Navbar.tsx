"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  ChevronDown,
  Brain,
  BarChart3,
  PhoneCall,
  Database,
  Sparkles,
  MapPin,
  UploadCloud,
  Menu,
  X,
  Shield,
  Search,
  Network,
  Radio,
  FileText,
  Activity,
  ArrowRight,
  AlertTriangle,
  Cpu,
  Zap,
  Building2,
  Lock,
  TrendingUp,
  Layers,
} from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const isLandingPage = pathname === "/";
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
    setOpenDropdown(null);
  }, [pathname]);

  interface DropdownSubItem {
    title: string;
    desc: string;
    href: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: string;
  }

  interface DropdownMenu {
    id: string;
    label: string;
    href: string;
    items: DropdownSubItem[];
  }

  // Techsnap-style Executive Landing Navigation configuration
  const navDropdowns: DropdownMenu[] = [
    {
      id: "problem",
      label: "Problem",
      href: "#problem",
      items: [
        {
          title: "Siloed FIR Records",
          desc: "Crime databases fragmented across state & municipal lines",
          href: "#problem",
          icon: AlertTriangle,
          badge: "Crisis",
        },
        {
          title: "Manual CDR Spreadsheet Dumps",
          desc: "Millions of telecom rows searched manually with Ctrl+F",
          href: "#problem",
          icon: PhoneCall,
          badge: "Bottleneck",
        },
        {
          title: "Burner SIM & Hardware Hopping",
          desc: "Prepaid SIMs swapped every 48h to evade lookups",
          href: "#problem",
          icon: Radio,
          badge: "Evasion",
        },
        {
          title: "Critical 72-Hour Evidentiary Lag",
          desc: "Weeks spent preparing dossiers while syndicates disperse",
          href: "#problem",
          icon: FileText,
          badge: "Delay",
        },
      ],
    },
    {
      id: "solution",
      label: "Solution",
      href: "#solution",
      items: [
        {
          title: "Spatial PostGIS Normalization",
          desc: "Universal WGS84 coordinates with 100% audit trail",
          href: "#solution",
          icon: MapPin,
        },
        {
          title: "Semantic Qdrant Vector Search",
          desc: "384-dim Modus Operandi clustering across all FIRs",
          href: "#solution",
          icon: Sparkles,
        },
        {
          title: "Neo4j Multi-Hop Graph Traversal",
          desc: "3-Hop relationship discovery between suspects & SIMs",
          href: "#solution",
          icon: Network,
        },
        {
          title: "Autonomous AI Detective",
          desc: "Llama-3.3 70B cell tower triangulation & dossier creator",
          href: "#solution",
          icon: Brain,
        },
      ],
    },
    {
      id: "architecture",
      label: "Architecture",
      href: "#architecture",
      items: [
        {
          title: "5-Tier Intelligence Pipeline",
          desc: "End-to-end data ingestion, graph & agent reasoning flow",
          href: "#architecture",
          icon: Layers,
        },
        {
          title: "PostGIS Spatial Core",
          desc: "EPSG:4326 geometry indexes and radial ST_DWithin buffers",
          href: "#architecture",
          icon: MapPin,
        },
        {
          title: "Dense Vector Vectorization",
          desc: "spaCy NER + all-MiniLM-L6-v2 semantic MO indexing",
          href: "#architecture",
          icon: Database,
        },
        {
          title: "Agentic Tool-Calling Loops",
          desc: "Autonomous Groq Llama-3.3 recursive forensic reasoning",
          href: "#architecture",
          icon: Cpu,
        },
      ],
    },
    {
      id: "impact",
      label: "Benefits & Impact",
      href: "#impact",
      items: [
        {
          title: "< 50ms MO Search Latency",
          desc: "Sub-second similarity queries across 1M+ FIR records",
          href: "#impact",
          icon: Zap,
        },
        {
          title: "85% Faster Time-to-Charge",
          desc: "Automated court-ready dossiers compiled in 18 minutes",
          href: "#impact",
          icon: TrendingUp,
        },
        {
          title: "100% Forensic Auditability",
          desc: "Non-destructive data lineage with immutable hash tracking",
          href: "#impact",
          icon: Shield,
        },
        {
          title: "Burner Network De-Anonymization",
          desc: "Co-location algorithms identify multi-handset carriers",
          href: "#impact",
          icon: PhoneCall,
        },
      ],
    },
    {
      id: "business-model",
      label: "Business Model",
      href: "#business-model",
      items: [
        {
          title: "District Police Commissionerate",
          desc: "Local jurisdiction spatial & vector search license",
          href: "#business-model",
          icon: Building2,
          badge: "Tier 1",
        },
        {
          title: "State Police CID & Special Cell",
          desc: "Full multi-hop graph, telecom CDR & autonomous agent",
          href: "#business-model",
          icon: Shield,
          badge: "Flagship",
        },
        {
          title: "Sovereign Air-Gapped Gov",
          desc: "100% on-premise defense deployment with offline LLMs",
          href: "#business-model",
          icon: Lock,
          badge: "Defense",
        },
        {
          title: "Pay-Per-Case Forensics",
          desc: "On-demand telecom CDR analysis & crisis escalation",
          href: "#business-model",
          icon: Activity,
          badge: "Add-on",
        },
      ],
    },
  ];

  // ==========================================
  // 1. LANDING PAGE NAVBAR (EXACT TECHSNAP REPLICA)
  // ==========================================
  if (isLandingPage) {
    return (
      <nav
        className={`fixed z-[100] transition-all duration-500 ease-out ${
          scrolled
            ? "top-3 sm:top-4 left-1/2 -translate-x-1/2 w-[94%] max-w-[1320px] rounded-full border border-purple-500/30 bg-[#080714]/92 backdrop-blur-2xl shadow-[0_16px_45px_rgba(0,0,0,0.85),0_0_30px_rgba(223,0,149,0.18)] px-4 sm:px-6 py-2"
            : "top-0 left-0 right-0 w-full bg-transparent pt-3.5 pb-2"
        }`}
      >
        <div className={`relative mx-auto transition-all duration-500 ease-in-out w-full ${
          scrolled ? "max-w-full px-1" : "max-w-[1400px] xl:max-w-[1500px] 2xl:max-w-[1600px] px-6"
        }`}>
          {/* Desktop Navbar Row */}
          <div className="relative hidden lg:flex w-full items-center justify-between">
            {/* Left: Logo */}
            <div className="flex items-center justify-start w-[15%] min-w-[180px] shrink-0">
              <Link href="/" className="flex items-center gap-2.5 group">
                <div className="relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-tr from-[#df0095] via-purple-600 to-violet-600 p-0.5 shadow-md group-hover:scale-105 transition-transform duration-300">
                  <div className={`flex h-full w-full items-center justify-center rounded-[10px] ${
                    scrolled ? "bg-[#0d0d18]" : "bg-white"
                  }`}>
                    <Image
                      src="/logo.png"
                      alt="ConnectDots"
                      width={28}
                      height={28}
                      className="object-contain"
                      priority
                    />
                  </div>
                </div>
                <div className="flex flex-col">
                  <span className={`text-xl font-black tracking-tight font-sans leading-none transition-colors ${
                    scrolled ? "text-white" : "text-slate-950"
                  }`}>
                    Connect<span className="text-[#df0095]">Dots</span>
                  </span>
                  <span className={`text-[0.6rem] font-bold tracking-wider uppercase mt-0.5 transition-colors ${
                    scrolled ? "text-violet-300/70 font-mono" : "text-slate-500"
                  }`}>
                    Snap the crime
                  </span>
                </div>
              </Link>
            </div>

            {/* Center: Pill Menu */}
            <div className="w-[70%] flex justify-center items-center shrink-0">
              <div className={`w-full max-w-[780px] flex py-1.5 px-3 rounded-full justify-evenly items-center space-x-1.5 transition-all duration-300 ${
                scrolled
                  ? "bg-white/[0.06] border border-white/10"
                  : "bg-white text-black shadow-[0_2px_14px_rgba(0,0,0,0.18)] border border-slate-200/80"
              }`}>
              {navDropdowns.map((dropdown) => {
                const isOpen = openDropdown === dropdown.id;
                return (
                  <div
                    key={dropdown.id}
                    className="relative group flex-1 text-center"
                    onMouseEnter={() => setOpenDropdown(dropdown.id)}
                    onMouseLeave={() => setOpenDropdown(null)}
                  >
                    <a
                      href={dropdown.href}
                      onClick={(e) => {
                        const targetId = dropdown.href.replace("#", "");
                        const elem = document.getElementById(targetId);
                        if (elem) {
                          e.preventDefault();
                          elem.scrollIntoView({ behavior: "smooth" });
                        }
                      }}
                      className={`group/btn w-full justify-center flex items-center text-xs px-3 py-2 rounded-full font-semibold transition-all duration-300 whitespace-nowrap cursor-pointer select-none ${
                        isOpen
                          ? "bg-[#df0095] text-white shadow-[0_0_12px_rgba(223,0,149,0.5)]"
                          : scrolled
                            ? "text-white/80 hover:text-white hover:bg-white/10"
                            : "bg-white text-slate-900 group-hover:bg-[#df0095] group-hover:text-white shadow-[0_2px_8px_rgba(0,0,0,0.18)]"
                      }`}
                    >
                      <span>{dropdown.label}</span>
                      <ChevronDown
                        className={`w-3.5 h-3.5 ml-1.5 transition-transform duration-200 ${
                          isOpen ? "rotate-180" : "group-hover/btn:rotate-180 group-hover:rotate-180"
                        }`}
                      />
                    </a>

                    {/* Rich Floating Dropdown Card (Solid White Background with Zero Transparency) */}
                    <div
                      className={`absolute left-1/2 -translate-x-1/2 top-full pt-2.5 w-72 z-50 transition-all duration-200 ${
                        isOpen
                          ? "block opacity-100 visible"
                          : "hidden group-hover:block group-hover:opacity-100 group-hover:visible"
                      }`}
                    >
                      <div className="rounded-2xl border border-slate-200 bg-white p-2.5 shadow-[0_20px_50px_rgba(0,0,0,0.45)] space-y-1">
                          {dropdown.items.map((subItem, idx) => {
                            const SubIcon = subItem.icon;
                            return (
                              <Link
                                key={idx}
                                href={subItem.href}
                                onClick={(e) => {
                                  if (subItem.href.startsWith("#")) {
                                    const targetId = subItem.href.replace("#", "");
                                    const elem = document.getElementById(targetId);
                                    if (elem) {
                                      e.preventDefault();
                                      elem.scrollIntoView({ behavior: "smooth" });
                                      setOpenDropdown(null);
                                    }
                                  }
                                }}
                                className="group/item flex items-start gap-3 rounded-xl p-2.5 hover:bg-slate-50 transition-colors"
                              >
                                <div className="p-2 rounded-lg bg-slate-100 text-slate-700 border border-slate-200 group-hover/item:bg-[#df0095]/10 group-hover/item:text-[#df0095] group-hover/item:border-[#df0095]/30 transition-colors shrink-0 mt-0.5">
                                  <SubIcon className="h-4 w-4" />
                                </div>
                                <div className="flex-1 min-w-0 text-left">
                                  <div className="flex items-center justify-between gap-1">
                                    <span className="text-xs font-bold text-slate-900 group-hover/item:text-[#df0095] transition-colors">
                                      {subItem.title}
                                    </span>
                                    {subItem.badge && (
                                      <span className="text-[0.6rem] font-bold px-1.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-slate-600">
                                        {subItem.badge}
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-[0.68rem] text-slate-500 leading-snug truncate">
                                    {subItem.desc}
                                  </p>
                                </div>
                              </Link>
                            );
                          })}
                        </div>
                      </div>
                  </div>
                );
              })}
              </div>
            </div>

            {/* Right: Demo Action Button */}
            <div className="flex w-[15%] min-w-[180px] justify-center items-center shrink-0">
              <Link
                href="/overview"
                className="inline-flex items-center justify-center px-7 py-2.5 rounded-full bg-gradient-to-r from-[#e002a2] via-[#df0095] to-[#c20084] text-white text-sm font-black tracking-wide uppercase shadow-[0_4px_18px_rgba(223,0,149,0.45)] hover:brightness-110 hover:scale-105 active:scale-95 transition-all duration-200 cursor-pointer"
              >
                Demo
              </Link>
            </div>
          </div>

          {/* Mobile Header Row (lg:hidden) */}
          <div className="relative lg:hidden flex w-full items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-[#df0095] to-violet-600 p-0.5">
                <div className={`flex h-full w-full items-center justify-center rounded-md ${
                  scrolled ? "bg-[#0d0d18]" : "bg-white"
                }`}>
                  <Image src="/logo.png" alt="ConnectDots" width={22} height={22} className="object-contain" />
                </div>
              </div>
              <span className={`text-lg font-black tracking-tight font-sans transition-colors ${
                scrolled ? "text-white" : "text-slate-950"
              }`}>
                Connect<span className="text-[#df0095]">Dots</span>
              </span>
            </Link>

            <div className="flex items-center gap-2">
              <Link
                href="/overview"
                className="px-3.5 py-1.5 bg-gradient-to-r from-[#e002a2] to-[#df0095] text-white rounded-full text-xs font-bold shadow-brand-glow"
              >
                Demo
              </Link>
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className={`p-2 rounded-full border shadow-sm transition-colors ${
                  scrolled
                    ? "bg-[#0d0d18] border-white/10 text-white hover:bg-white/10"
                    : "bg-white border-slate-200 text-slate-800 hover:bg-slate-50"
                }`}
                aria-label="Toggle Menu"
              >
                {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
            </div>
          </div>

          {/* Mobile Drawer Menu (Solid White Background with Zero Transparency) */}
          {mobileMenuOpen && (
            <div className="lg:hidden mt-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-2xl space-y-4 max-h-[80vh] overflow-y-auto text-slate-900">
              <div className="space-y-1 divide-y divide-slate-100">
                {navDropdowns.map((dropdown) => (
                  <div key={dropdown.id} className="pt-2">
                    <span className="text-[0.68rem] font-bold text-slate-400 uppercase tracking-wider px-2 font-mono">
                      {dropdown.label}
                    </span>
                    <div className="mt-1 space-y-1">
                      {dropdown.items.map((item, idx) => (
                        <Link
                          key={idx}
                          href={item.href}
                          onClick={() => setMobileMenuOpen(false)}
                          className="flex items-center justify-between p-2 rounded-lg text-xs font-semibold text-slate-800 hover:bg-slate-50 hover:text-[#df0095] transition-colors"
                        >
                          <span>{item.title}</span>
                          <ArrowRight className="h-3 w-3 text-slate-400" />
                        </Link>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="pt-3 border-t border-slate-100 flex">
                <Link
                  href="/overview"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-3 rounded-full bg-gradient-to-r from-[#e002a2] via-[#df0095] to-[#c20084] text-white text-sm font-black uppercase tracking-wider shadow-md"
                >
                  Launch Demo Dashboard
                </Link>
              </div>
            </div>
          )}
        </div>
      </nav>
    );
  }

  // ==========================================
  // 2. OPERATIONAL WORKSPACE NAVBAR (FOR /investigation, /overview, etc.)
  // ==========================================
  const workspaceLinks = [
    { label: "Demo", href: "/overview", icon: Sparkles },
    { label: "Investigation", href: "/investigation", icon: Brain },
    { label: "Telecom CDR", href: "/telecom", icon: PhoneCall },
    { label: "Analytics", href: "/analytics", icon: Activity },
    { label: "Crime Explorer", href: "/crimes", icon: Database },
    { label: "Semantic Search", href: "/search", icon: Search },
    { label: "Spatial Map", href: "/map", icon: MapPin },
    { label: "Ingestion", href: "/import", icon: UploadCloud },
    { label: "Landing", href: "/", icon: Shield },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-purple-900/20 bg-[#030307]/90 backdrop-blur-2xl py-2.5">
      <div className="mx-auto flex max-w-[1600px] items-center justify-between px-4 sm:px-6 lg:px-8 gap-3 xl:gap-4">
        {/* Brand Logo & Name */}
        <Link href="/" className="flex items-center gap-2.5 group shrink-0">
          <div className="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-xl border border-violet-500/40 bg-charcoal p-1.5 shadow-brand-glow transition-transform duration-300 group-hover:scale-105 group-hover:border-violet-400">
            <Image
              src="/logo.png"
              alt="ConnectDots Logo"
              width={30}
              height={30}
              className="h-full w-full object-contain"
              priority
            />
          </div>
          <div className="flex flex-col">
            <span className="text-base font-black tracking-wider text-white uppercase font-mono leading-none">
              Connect<span className="text-violet-400">Dots</span>
            </span>
            <span className="text-[0.6rem] font-bold tracking-[0.2em] text-violet-300/60 uppercase mt-0.5">
              AI Crime Intelligence Platform
            </span>
          </div>
        </Link>

        {/* Operational Nav Links */}
        <nav className="hidden lg:flex items-center gap-1 rounded-full border border-purple-500/20 bg-[#0c0c16]/90 p-1.5 shadow-2xl backdrop-blur-2xl">
          {workspaceLinks.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`whitespace-nowrap shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-all ${
                  isActive
                    ? "bg-gradient-to-r from-violet-600 via-purple-600 to-fuchsia-600 text-white shadow-brand-glow font-bold"
                    : "text-white/70 hover:text-white hover:bg-white/[0.08]"
                }`}
              >
                <Icon className={`h-3.5 w-3.5 transition-colors ${isActive ? "text-white" : "text-violet-400/70"}`} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5 shrink-0">
          <Link
            href="/investigation"
            className="whitespace-nowrap inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-fuchsia-600 via-purple-600 to-violet-600 px-5 py-2 text-xs font-black uppercase tracking-wider text-white shadow-brand-glow hover:brightness-110 transition-all active:scale-95"
          >
            <Brain className="h-3.5 w-3.5" />
            <span>Command Center</span>
          </Link>

          <Link
            href="/overview"
            className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-white px-4 py-2 text-xs font-black uppercase tracking-wider text-slate-900 shadow-lg hover:bg-slate-100 transition-all active:scale-95"
          >
            <BarChart3 className="h-3.5 w-3.5 text-violet-700" />
            <span>Overview</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
