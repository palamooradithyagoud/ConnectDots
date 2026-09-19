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
  Check,
} from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const isLandingPage = pathname === "/";
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  useEffect(() => {
    let ticking = false;
    const handleScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const y = window.scrollY;
          setScrolled((prev) => {
            // Hysteresis prevents flickering when hovering around the threshold
            if (!prev && y > 50) return true;
            if (prev && y < 25) return false;
            return prev;
          });
          ticking = false;
        });
        ticking = true;
      }
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
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
      id: "pricing",
      label: "Pricing",
      href: "#pricing",
      items: [
        {
          title: "Free Tier (₹0)",
          desc: "Limited data sources, 10 cases/mo, 30 days history",
          href: "#pricing",
          icon: Zap,
          badge: "Free",
        },
        {
          title: "Monthly Pro (₹499/mo)",
          desc: "Unlimited cases, all data sources, advanced AI & maps",
          href: "#pricing",
          icon: Sparkles,
          badge: "Popular",
        },
        {
          title: "Yearly Pro (₹4,999/yr)",
          desc: "Full suite, 5+ yrs data, 2 months free, priority support",
          href: "#pricing",
          icon: Shield,
          badge: "Save 17%",
        },
      ],
    },
  ];

  // Pricing tiers for navigation dropdown preview (shadcn pricing tiers component)
  const pricingTiers = [
    {
      name: "Free",
      icon: "🆓",
      price: "₹0",
      period: "",
      badge: null,
      description: "Perfect for testing & basic exploration",
      features: [
        "10 cases/month FIR / Case Analysis",
        "Limited Data Sources",
        "Basic Crime Pattern Detection",
        "Basic Hotspot Detection",
        "30 days Historical Data",
        "Community Support",
      ],
      cta: "Get Started Free →",
      href: "/overview",
      highlighted: false,
    },
    {
      name: "Monthly Pro",
      icon: "🚀",
      price: "₹499",
      period: "/ month",
      badge: "Popular",
      description: "For active investigative units & local stations",
      features: [
        "Unlimited FIR / Case Analysis",
        "All Supported Data Sources",
        "Advanced AI Pattern Detection",
        "Hotspot Detection & AI Insights",
        "Interactive Crime Map (Advanced)",
        "Trend Analysis & Report Export",
        "2 years Historical Data",
        "Priority Processing & Support",
      ],
      cta: "Start Monthly Pro →",
      href: "/overview",
      highlighted: true,
    },
    {
      name: "Yearly Pro",
      icon: "👑",
      price: "₹4,999",
      period: "/ year",
      badge: "Best Value",
      description: "Maximum value for law enforcement units",
      features: [
        "Everything in Monthly Pro",
        "5+ years Historical Data",
        "2 Months Free (Save ₹1,000)",
        "Advanced Multi-Modal AI Correlation",
        "Autonomous AI Detective Reasoning",
        "Priority Queue Processing",
        "Dedicated Intelligence Priority Support",
      ],
      cta: "Get Yearly Pro →",
      href: "/overview",
      highlighted: false,
    },
  ];

  // Detailed comparison matrix from user prompt
  const comparisonRows = [
    { feature: "Price", free: "₹0", monthly: "₹499 / month", yearly: "₹4,999 / year" },
    { feature: "Data Sources", free: "Limited", monthly: "All supported sources", yearly: "All supported sources" },
    { feature: "FIR / Case Analysis", free: "10 cases/month", monthly: "Unlimited", yearly: "Unlimited" },
    { feature: "Crime Pattern Detection", free: "Basic", monthly: "Advanced AI", yearly: "Advanced AI" },
    { feature: "Hotspot Detection", free: "Basic", monthly: "✓", yearly: "✓" },
    { feature: "AI Insights", free: "Limited", monthly: "✓", yearly: "✓" },
    { feature: "Interactive Crime Map", free: "Basic", monthly: "✓ Advanced", yearly: "✓ Advanced" },
    { feature: "Trend Analysis", free: "—", monthly: "✓", yearly: "✓" },
    { feature: "Reports & Export", free: "Limited", monthly: "✓", yearly: "✓" },
    { feature: "Historical Data", free: "30 days", monthly: "2 years", yearly: "5+ years" },
    { feature: "Priority Processing", free: "—", monthly: "✓", yearly: "✓" },
    { feature: "Support", free: "Community", monthly: "Priority", yearly: "Priority" },
  ];

  // ==========================================
  // 1. LANDING PAGE NAVBAR (EXACT TECHSNAP REPLICA)
  // ==========================================
  if (isLandingPage) {
    return (
      <nav
        className={`fixed z-[100] left-1/2 -translate-x-1/2 transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] will-change-[top,width,background-color,box-shadow,border-radius] ${
          scrolled
            ? "top-3 sm:top-4 w-[94%] max-w-[1320px] rounded-full border border-purple-500/30 bg-[#080714]/92 backdrop-blur-2xl shadow-[0_16px_45px_rgba(0,0,0,0.85),0_0_30px_rgba(223,0,149,0.18)] px-4 sm:px-6 py-2"
            : "top-0 w-full max-w-[1600px] rounded-none border border-transparent bg-transparent shadow-none px-6 pt-3.5 pb-2"
        }`}
      >
        <div className="relative mx-auto w-full">
          {/* Desktop Navbar Row */}
          <div className="relative hidden lg:flex w-full items-center justify-between">
            {/* Left: Logo */}
            <div className="flex items-center justify-start w-[15%] min-w-[180px] shrink-0">
              <Link href="/" className="flex items-center gap-2.5 group">
                <div className="relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-tr from-[#df0095] via-purple-600 to-violet-600 p-0.5 shadow-md group-hover:scale-105 transition-transform duration-300">
                  <div className={`flex h-full w-full items-center justify-center rounded-[10px] transition-colors duration-500 ${
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
                  <span className={`text-xl font-black tracking-tight font-sans leading-none transition-colors duration-500 ${
                    scrolled ? "text-white" : "text-slate-950"
                  }`}>
                    Connect<span className="text-[#df0095]">Dots</span>
                  </span>
                  <span className={`text-[0.6rem] font-bold tracking-wider uppercase mt-0.5 transition-colors duration-500 ${
                    scrolled ? "text-violet-300/70 font-mono" : "text-slate-500"
                  }`}>
                    Snap the crime
                  </span>
                </div>
              </Link>
            </div>

            {/* Center: Pill Menu */}
            <div className="w-[70%] flex justify-center items-center shrink-0">
              <div className={`w-full max-w-[780px] flex py-1.5 px-3 rounded-full justify-evenly items-center space-x-1.5 transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] ${
                scrolled
                  ? "bg-white/[0.06] border border-white/10"
                  : "bg-white text-slate-900 shadow-[0_4px_20px_rgba(0,0,0,0.12)] border border-slate-200/90"
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
                            : "text-slate-800 hover:bg-slate-100 hover:text-slate-950"
                      }`}
                    >
                      <span>{dropdown.label}</span>
                      <ChevronDown
                        className={`w-3.5 h-3.5 ml-1.5 transition-transform duration-200 ${
                          isOpen ? "rotate-180" : "group-hover/btn:rotate-180 group-hover:rotate-180"
                        }`}
                      />
                    </a>

                    {/* Rich Floating Dropdown Card */}
                    {dropdown.id === "pricing" ? (
                      /* SHADCN NAVIGATION MENU PRICING TIERS PREVIEW DROPDOWN */
                      <div
                        className={`absolute right-[-40px] md:right-[-60px] lg:right-[-90px] top-full pt-2.5 w-[850px] max-w-[92vw] z-50 transition-all duration-200 ${
                          isOpen
                            ? "block opacity-100 visible"
                            : "hidden group-hover:block group-hover:opacity-100 group-hover:visible"
                        }`}
                      >
                        <div className="rounded-3xl border border-slate-200 bg-white p-5 sm:p-6 shadow-[0_25px_70px_rgba(0,0,0,0.5)] text-slate-900 space-y-5 max-h-[82vh] overflow-y-auto text-left">
                          {/* Header */}
                          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                            <div>
                              <h3 className="text-sm sm:text-base font-black text-slate-950 font-mono tracking-tight flex items-center gap-2">
                                <span>ConnectDots Intelligence Plans</span>
                                <span className="text-[0.62rem] font-bold px-2 py-0.5 rounded-full bg-pink-100 text-[#df0095] border border-pink-200 uppercase font-sans">
                                  Public Safety Pricing
                                </span>
                              </h3>
                              <p className="text-xs text-slate-500 font-sans mt-0.5">
                                Transparent pricing from community testing to full intelligence units.
                              </p>
                            </div>
                            <Link
                              href="#pricing"
                              onClick={() => setOpenDropdown(null)}
                              className="text-xs font-bold text-[#df0095] hover:underline flex items-center gap-1 font-mono shrink-0"
                            >
                              <span>Full Page</span>
                              <ArrowRight className="h-3 w-3" />
                            </Link>
                          </div>

                          {/* 3 Tier Cards Grid */}
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
                            {pricingTiers.map((tier, tIdx) => (
                              <div
                                key={tIdx}
                                className={`relative rounded-2xl p-4 flex flex-col justify-between transition-all duration-200 ${
                                  tier.highlighted
                                    ? "border-2 border-[#df0095] bg-gradient-to-b from-pink-50/60 to-white shadow-[0_8px_25px_rgba(223,0,149,0.15)] scale-[1.02]"
                                    : "border border-slate-200 bg-slate-50/70 hover:bg-white hover:border-slate-300"
                                }`}
                              >
                                {tier.badge && (
                                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-2.5 py-0.5 rounded-full bg-gradient-to-r from-[#e002a2] to-[#df0095] text-white text-[0.62rem] font-black uppercase tracking-wider shadow whitespace-nowrap">
                                    {tier.badge}
                                  </div>
                                )}

                                <div>
                                  <div className="flex items-center gap-1.5">
                                    <span className="text-lg">{tier.icon}</span>
                                    <h4 className="font-mono font-black text-sm text-slate-900">{tier.name}</h4>
                                  </div>

                                  <div className="mt-2 flex items-baseline gap-1">
                                    <span className="font-mono font-black text-2xl text-slate-950">{tier.price}</span>
                                    {tier.period && (
                                      <span className="text-xs text-slate-500 font-medium font-sans">{tier.period}</span>
                                    )}
                                  </div>

                                  <p className="text-[0.68rem] text-slate-500 mt-1 leading-snug font-sans">
                                    {tier.description}
                                  </p>

                                  <div className="mt-3.5 pt-3 border-t border-slate-200/70 space-y-1.5 text-left">
                                    {tier.features.map((feat, fIdx) => (
                                      <div key={fIdx} className="flex items-start gap-1.5 text-[0.7rem] text-slate-700 font-sans leading-tight">
                                        <Check className="h-3.5 w-3.5 text-emerald-600 shrink-0 mt-0.5" />
                                        <span>{feat}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>

                                <div className="mt-4 pt-3">
                                  <Link
                                    href={tier.href}
                                    onClick={() => setOpenDropdown(null)}
                                    className={`w-full inline-flex items-center justify-center py-2 px-3 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-200 ${
                                      tier.highlighted
                                        ? "bg-gradient-to-r from-[#e002a2] via-[#df0095] to-[#c20084] text-white shadow hover:brightness-110 active:scale-95"
                                        : "bg-white border border-slate-300 text-slate-800 hover:bg-slate-100 active:scale-95"
                                    }`}
                                  >
                                    {tier.cta}
                                  </Link>
                                </div>
                              </div>
                            ))}
                          </div>

                          {/* Downside: Feature Comparison Table */}
                          <div className="pt-3 border-t border-slate-200">
                            <div className="flex items-center justify-between mb-2 px-1">
                              <h5 className="text-xs font-mono font-black text-slate-900 uppercase tracking-wider">
                                Detailed Comparison Table
                              </h5>
                              <span className="text-[0.65rem] text-slate-500 font-mono">
                                All prices in INR (₹)
                              </span>
                            </div>

                            <div className="rounded-xl border border-slate-200 overflow-hidden text-[0.72rem]">
                              <table className="w-full text-left border-collapse">
                                <thead>
                                  <tr className="bg-slate-100 text-slate-700 font-mono text-[0.7rem] border-b border-slate-200">
                                    <th className="py-2 px-3 font-bold w-[34%]">Feature</th>
                                    <th className="py-2 px-3 font-bold text-center w-[20%]">🆓 Free</th>
                                    <th className="py-2 px-3 font-bold text-center w-[23%] text-[#df0095] bg-pink-50/50">
                                      🚀 Monthly Pro
                                    </th>
                                    <th className="py-2 px-3 font-bold text-center w-[23%] text-purple-700">
                                      👑 Yearly Pro
                                    </th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100 text-slate-700">
                                  {comparisonRows.map((row, rIdx) => (
                                    <tr
                                      key={rIdx}
                                      className={rIdx % 2 === 1 ? "bg-slate-50/60" : "bg-white"}
                                    >
                                      <td className="py-1.5 px-3 font-semibold text-slate-900">
                                        {row.feature}
                                      </td>
                                      <td className="py-1.5 px-3 text-center text-slate-600 font-mono">
                                        {row.free}
                                      </td>
                                      <td className="py-1.5 px-3 text-center font-bold font-mono text-[#df0095] bg-pink-50/30">
                                        {row.monthly}
                                      </td>
                                      <td className="py-1.5 px-3 text-center font-bold font-mono text-purple-900">
                                        {row.yearly}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      /* Standard Dropdown Card */
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
                    )}
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
