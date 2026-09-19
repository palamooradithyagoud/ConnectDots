"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  FileText,
  Newspaper,
  Share2,
  Users,
  TrendingUp,
  Lightbulb,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  HelpCircle,
} from "lucide-react";

interface Point {
  x: number;
  y: number;
}

interface ThreadPaths {
  inputs: string[];
  outputs: string[];
  svgSize: { width: number; height: number };
}

export default function StructuredPathSolution() {
  const [activeInput, setActiveInput] = useState<number | null>(null);
  const [activeOutput, setActiveOutput] = useState<number | null>(null);
  const [cycleIndex, setCycleIndex] = useState(0);

  // Dynamic DOM refs for absolute sub-pixel alignment
  const containerRef = useRef<HTMLDivElement>(null);
  const inputSocketRefs = useRef<(HTMLDivElement | null)[]>([]);
  const outputSocketRefs = useRef<(HTMLDivElement | null)[]>([]);
  const centerLeftRef = useRef<HTMLDivElement>(null);
  const centerRightRef = useRef<HTMLDivElement>(null);

  const [paths, setPaths] = useState<ThreadPaths | null>(null);

  // Auto-cycle through data sources for a hypnotic, living forensic demonstration
  useEffect(() => {
    const timer = setInterval(() => {
      setCycleIndex((prev) => (prev + 1) % 4);
    }, 2800);
    return () => clearInterval(timer);
  }, []);

  // Compute exact bezier curves between sockets
  const recalculatePaths = useCallback(() => {
    if (!containerRef.current || !centerLeftRef.current || !centerRightRef.current) return;
    const containerRect = containerRef.current.getBoundingClientRect();
    const clRect = centerLeftRef.current.getBoundingClientRect();
    const crRect = centerRightRef.current.getBoundingClientRect();

    if (containerRect.width === 0 || containerRect.height === 0) return;

    // Center Left port exact pixel coordinate
    const centerLeftPoint: Point = {
      x: clRect.left + clRect.width / 2 - containerRect.left,
      y: clRect.top + clRect.height / 2 - containerRect.top,
    };

    // Center Right port exact pixel coordinate
    const centerRightPoint: Point = {
      x: crRect.left + crRect.width / 2 - containerRect.left,
      y: crRect.top + crRect.height / 2 - containerRect.top,
    };

    // Smooth horizontal cubic bezier curve builder
    const makeBezier = (p1: Point, p2: Point) => {
      const dx = Math.abs(p2.x - p1.x) * 0.45;
      return `M ${p1.x},${p1.y} C ${p1.x + dx},${p1.y} ${p2.x - dx},${p2.y} ${p2.x},${p2.y}`;
    };

    const inputPaths: string[] = [];
    inputSocketRefs.current.forEach((el) => {
      if (el) {
        const r = el.getBoundingClientRect();
        const p1: Point = {
          x: r.left + r.width / 2 - containerRect.left,
          y: r.top + r.height / 2 - containerRect.top,
        };
        inputPaths.push(makeBezier(p1, centerLeftPoint));
      }
    });

    const outputPaths: string[] = [];
    outputSocketRefs.current.forEach((el) => {
      if (el) {
        const r = el.getBoundingClientRect();
        const p2: Point = {
          x: r.left + r.width / 2 - containerRect.left,
          y: r.top + r.height / 2 - containerRect.top,
        };
        outputPaths.push(makeBezier(centerRightPoint, p2));
      }
    });

    setPaths({
      inputs: inputPaths,
      outputs: outputPaths,
      svgSize: {
        width: containerRect.width,
        height: containerRect.height,
      },
    });
  }, []);

  // Recalculate on mount, load, resize, and DOM changes
  useEffect(() => {
    recalculatePaths();
    const t1 = setTimeout(recalculatePaths, 150);
    const t2 = setTimeout(recalculatePaths, 600);

    const ro = new ResizeObserver(() => {
      recalculatePaths();
    });
    if (containerRef.current) {
      ro.observe(containerRef.current);
    }
    window.addEventListener("resize", recalculatePaths);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      ro.disconnect();
      window.removeEventListener("resize", recalculatePaths);
    };
  }, [recalculatePaths]);

  const inputSources = [
    {
      id: 0,
      title: "FIRs & Police Records",
      desc: "Police data, charge sheets, case details",
      color: "#38bdf8", // Sky
      glow: "rgba(56, 189, 248, 0.4)",
      icon: FileText,
      tag: "Scattered FIRs",
    },
    {
      id: 1,
      title: "News & Media",
      desc: "News articles, local media reports",
      color: "#a855f7", // Purple
      glow: "rgba(168, 85, 247, 0.4)",
      icon: Newspaper,
      tag: "Media Feeds",
    },
    {
      id: 2,
      title: "Social Media",
      desc: "Public posts, trending discussions",
      color: "#ec4899", // Pink
      glow: "rgba(236, 72, 153, 0.4)",
      icon: Share2,
      tag: "Social OSINT",
    },
    {
      id: 3,
      title: "Citizen Complaints",
      desc: "People reports, grievances, tips",
      color: "#06b6d4", // Cyan
      glow: "rgba(6, 182, 212, 0.4)",
      icon: Users,
      tag: "Field Intel",
    },
  ];

  const outputImpacts = [
    {
      id: 0,
      title: "Data-Driven Insights",
      desc: "Identify patterns and hotspots",
      color: "#a855f7",
      glow: "rgba(168, 85, 247, 0.45)",
      icon: TrendingUp,
    },
    {
      id: 1,
      title: "Better Decision Making",
      desc: "Actionable recommendations",
      color: "#eab308",
      glow: "rgba(234, 179, 8, 0.45)",
      icon: Lightbulb,
    },
    {
      id: 2,
      title: "Safer Communities",
      desc: "Prevent crimes and build trust",
      color: "#10b981",
      glow: "rgba(16, 185, 129, 0.45)",
      icon: ShieldCheck,
    },
  ];

  return (
    <section
      id="solution"
      className="relative w-full max-w-[1440px] mx-auto py-16 sm:py-24 px-4 sm:px-6 lg:px-8 overflow-hidden select-none"
    >
      {/* Background Ambient Glows & Forensic Atmosphere */}
      <div className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[550px] bg-gradient-to-r from-purple-600/15 via-[#df0095]/15 to-cyan-500/10 rounded-full blur-[160px] -z-10" />

      {/* SECTION HEADER */}
      <div className="text-center max-w-4xl mx-auto space-y-4 mb-14 lg:mb-20">
        <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-[#12121c]/90 px-4 py-1.5 text-xs font-mono font-bold tracking-wider text-violet-300 shadow-brand-glow">
          <HelpCircle className="h-3.5 w-3.5 text-[#df0095] animate-pulse" />
          <span className="uppercase">Confused about what to do with complex crime data?</span>
        </div>

        <h2 className="text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white font-sans leading-[1.08]">
          Follow one{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#df0095] via-purple-400 to-cyan-400">
            structured path
          </span>
        </h2>

        <p className="text-sm sm:text-base text-white/70 max-w-2xl mx-auto font-sans leading-relaxed">
          From scattered information to smarter decisions —{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 to-purple-300 font-bold">
            Connect Dots for PS 189
          </span>
        </p>
      </div>

      {/* PIPELINE CONTAINER */}
      <div className="relative">
        {/* Playful Floating Hand-Drawn Style Annotations */}
        <div className="hidden xl:block absolute -top-8 left-6 text-[#df0095] font-mono text-xs font-bold tracking-wider rotate-[-6deg] z-20">
          <span className="bg-[#1a0f24]/80 border border-[#df0095]/30 px-3 py-1 rounded-full backdrop-blur-md shadow-lg">
            Scattered Data ⤹
          </span>
        </div>

        <div className="hidden xl:block absolute -top-10 right-8 text-cyan-300 font-mono text-xs font-bold tracking-wider rotate-[4deg] z-20">
          <span className="bg-[#0b1c24]/80 border border-cyan-400/30 px-3 py-1 rounded-full backdrop-blur-md shadow-lg">
            Different Sources, One Clear Picture ⤷
          </span>
        </div>

        {/* 3-COLUMN DESKTOP GRID / STACK ON MOBILE */}
        <div ref={containerRef} className="relative grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">

          {/* DYNAMIC SVG CONNECTING THREADS ACROSS THE ENTIRE GRID */}
          {paths && (
            <div className="hidden lg:block absolute inset-0 pointer-events-none z-10 overflow-visible">
              <svg
                className="w-full h-full overflow-visible"
                viewBox={`0 0 ${paths.svgSize.width} ${paths.svgSize.height}`}
              >
                <defs>
                  {/* Left Stream Linear Gradients */}
                  <linearGradient id="dynThreadGrad0" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.9" />
                    <stop offset="100%" stopColor="#c084fc" stopOpacity="0.9" />
                  </linearGradient>
                  <linearGradient id="dynThreadGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#a855f7" stopOpacity="0.9" />
                    <stop offset="100%" stopColor="#e879f9" stopOpacity="0.9" />
                  </linearGradient>
                  <linearGradient id="dynThreadGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#ec4899" stopOpacity="0.9" />
                    <stop offset="100%" stopColor="#df0095" stopOpacity="0.9" />
                  </linearGradient>
                  <linearGradient id="dynThreadGrad3" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.9" />
                    <stop offset="100%" stopColor="#818cf8" stopOpacity="0.9" />
                  </linearGradient>

                  {/* Right Stream Linear Gradients */}
                  <linearGradient id="dynOutGrad0" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#df0095" stopOpacity="0.9" />
                    <stop offset="100%" stopColor="#a855f7" stopOpacity="0.9" />
                  </linearGradient>
                  <linearGradient id="dynOutGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#e879f9" stopOpacity="0.9" />
                    <stop offset="100%" stopColor="#eab308" stopOpacity="0.9" />
                  </linearGradient>
                  <linearGradient id="dynOutGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#818cf8" stopOpacity="0.9" />
                    <stop offset="100%" stopColor="#10b981" stopOpacity="0.9" />
                  </linearGradient>

                  {/* Smooth Photon Glow Filter */}
                  <filter id="dynPhotonGlow" x="-100%" y="-100%" width="300%" height="300%">
                    <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="blur" />
                    <feMerge>
                      <feMergeNode in="blur" />
                      <feMergeNode in="SourceGraphic" />
                    </feMerge>
                  </filter>
                </defs>

                {/* Left Converging Threads (From Exact Sockets to Center Left Port) */}
                {paths.inputs.map((d, idx) => {
                  const item = inputSources[idx];
                  const isHighlighted = activeInput === idx || (activeInput === null && cycleIndex === idx);
                  return (
                    <g key={`in-${idx}`}>
                      <path
                        d={d}
                        fill="none"
                        stroke={`url(#dynThreadGrad${idx})`}
                        strokeWidth={isHighlighted ? "3.2" : "2"}
                        strokeOpacity={isHighlighted ? "1" : "0.5"}
                        strokeLinecap="round"
                      />
                      <circle r="4.5" fill={item.color} filter="url(#dynPhotonGlow)">
                        <animateMotion
                          path={d}
                          dur="2.5s"
                          begin={`${idx * 0.65}s`}
                          repeatCount="indefinite"
                        />
                      </circle>
                      <circle r="2" fill="#ffffff">
                        <animateMotion
                          path={d}
                          dur="2.5s"
                          begin={`${idx * 0.65}s`}
                          repeatCount="indefinite"
                        />
                      </circle>
                    </g>
                  );
                })}

                {/* Right Diverging Threads (From Center Right Port to 3 Exact Outcome Sockets) */}
                {paths.outputs.map((d, idx) => {
                  const item = outputImpacts[idx];
                  const isHovered = activeOutput === idx;
                  return (
                    <g key={`out-${idx}`}>
                      <path
                        d={d}
                        fill="none"
                        stroke={`url(#dynOutGrad${idx})`}
                        strokeWidth={isHovered ? "3.2" : "2"}
                        strokeOpacity={isHovered ? "1" : "0.55"}
                        strokeLinecap="round"
                      />
                      <circle r="4.5" fill={item.color} filter="url(#dynPhotonGlow)">
                        <animateMotion
                          path={d}
                          dur="2.5s"
                          begin={`${0.2 + idx * 0.8}s`}
                          repeatCount="indefinite"
                        />
                      </circle>
                      <circle r="2" fill="#ffffff">
                        <animateMotion
                          path={d}
                          dur="2.5s"
                          begin={`${0.2 + idx * 0.8}s`}
                          repeatCount="indefinite"
                        />
                      </circle>
                    </g>
                  );
                })}
              </svg>
            </div>
          )}

          {/* ========================================================================= */}
          {/* LEFT: 4 SCATTERED DATA INPUT CARDS (Columns 1-3) */}
          {/* ========================================================================= */}
          <div className="lg:col-span-3 flex flex-col gap-3.5 z-10">
            {inputSources.map((item, idx) => {
              const Icon = item.icon;
              const isHighlighted = activeInput === idx || (activeInput === null && cycleIndex === idx);

              return (
                <div
                  key={item.id}
                  onMouseEnter={() => setActiveInput(idx)}
                  onMouseLeave={() => setActiveInput(null)}
                  className={`group relative rounded-2xl border transition-all duration-300 p-3.5 cursor-pointer backdrop-blur-xl ${
                    isHighlighted
                      ? "border-white/40 bg-white/[0.08] shadow-[0_10px_30px_-5px_var(--glow)] scale-[1.02] -translate-y-0.5"
                      : "border-white/10 bg-[#090912]/80 hover:border-white/20 hover:bg-white/[0.04]"
                  }`}
                  style={{ "--glow": item.glow } as React.CSSProperties}
                >
                  <div className="flex items-center gap-3">
                    {/* Icon Box */}
                    <div
                      className="p-2.5 rounded-xl border shrink-0 transition-transform duration-300 group-hover:scale-110"
                      style={{
                        backgroundColor: `${item.color}15`,
                        borderColor: `${item.color}40`,
                        color: item.color,
                      }}
                    >
                      <Icon className="h-5 w-5" />
                    </div>

                    {/* Text Details */}
                    <div className="flex-1 min-w-0 text-left">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs sm:text-sm font-bold text-white font-mono truncate">
                          {item.title}
                        </h4>
                        {isHighlighted && (
                          <div
                            className="h-2 w-2 rounded-full animate-ping"
                            style={{ backgroundColor: item.color }}
                          />
                        )}
                      </div>
                      <p className="text-[0.68rem] text-white/60 font-sans leading-snug truncate mt-0.5">
                        {item.desc}
                      </p>
                    </div>
                  </div>

                  {/* Connecting Socket Dot on Right Edge with Ref */}
                  <div
                    ref={(el) => {
                      inputSocketRefs.current[idx] = el;
                    }}
                    className={`hidden lg:block absolute -right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 rounded-full border-2 border-[#090912] transition-all duration-300 shadow-md ${
                      isHighlighted ? "scale-125 ring-2 ring-white/50" : "opacity-60"
                    }`}
                    style={{ backgroundColor: item.color }}
                  />
                </div>
              );
            })}
          </div>

          {/* ========================================================================= */}
          {/* CENTER: THE MASTER DETECTIVE BOARD HUB (Columns 4-8) */}
          {/* ========================================================================= */}
          <div className="lg:col-span-6 relative flex flex-col items-center justify-center z-20">
            {/* THE CENTER PINBOARD CARD */}
            <div className="w-full max-w-[460px] rounded-3xl border-2 border-purple-500/40 bg-gradient-to-b from-[#140f26] via-[#0d0918] to-[#05040a] p-6 sm:p-7 shadow-[0_0_80px_rgba(168,85,247,0.25)] text-center relative overflow-hidden backdrop-blur-2xl">
              {/* Converging port pulse left with Ref */}
              <div
                ref={centerLeftRef}
                className="hidden lg:flex absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 h-6 w-6 items-center justify-center z-30 pointer-events-none"
              >
                <div className="absolute h-full w-full rounded-full bg-[#df0095] animate-ping opacity-70" />
                <div className="h-3.5 w-3.5 rounded-full bg-white shadow-[0_0_12px_#df0095] border-2 border-[#140f26]" />
              </div>

              {/* Diverging port pulse right with Ref */}
              <div
                ref={centerRightRef}
                className="hidden lg:flex absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 h-6 w-6 items-center justify-center z-30 pointer-events-none"
              >
                <div className="absolute h-full w-full rounded-full bg-cyan-400 animate-ping opacity-70" />
                <div className="h-3.5 w-3.5 rounded-full bg-white shadow-[0_0_12px_#06b6d4] border-2 border-[#140f26]" />
              </div>

              {/* DETECTIVE CORKBOARD PINBOARD ART */}
              <div className="relative mx-auto w-full max-w-[380px] h-[205px] rounded-2xl border-2 border-amber-900/40 bg-[#0d0918] shadow-[0_12px_36px_rgba(0,0,0,0.8)] overflow-hidden group">
                <Image
                  src="/detective_pinboard.jpg"
                  alt="ConnectDots Detective Pinboard"
                  fill
                  sizes="(max-width: 768px) 100vw, 400px"
                  className="object-cover object-center group-hover:scale-105 transition-transform duration-700"
                  priority
                />
                {/* Subtle Ambient Vignette & Gradient Overlays */}
                <div className="absolute inset-0 bg-gradient-to-t from-[#0d0918]/85 via-transparent to-black/20 pointer-events-none" />
                <div className="absolute inset-0 ring-1 ring-inset ring-white/15 rounded-2xl pointer-events-none" />

                {/* Live Status Tag */}
                <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/70 backdrop-blur-md border border-red-500/50 text-[0.62rem] font-mono text-red-300 font-bold tracking-wider shadow-lg">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                  <span>CASE #189 · ACTIVE</span>
                </div>

                {/* Mystery Solved Indicator Badge */}
                <div className="absolute top-2.5 right-2.5 flex items-center gap-1 px-2.5 py-1 rounded-full bg-black/70 backdrop-blur-md border border-cyan-500/50 text-[0.62rem] font-mono text-cyan-300 font-bold shadow-lg">
                  <Sparkles className="w-3 h-3 text-cyan-400" />
                  <span>AI MAPPING</span>
                </div>

                {/* Bottom live correlation bar */}
                <div className="absolute bottom-2 inset-x-2.5 flex items-center justify-between text-[0.62rem] font-mono text-white/80 bg-black/65 backdrop-blur-md px-2.5 py-1 rounded-lg border border-white/10 shadow-md">
                  <span className="truncate">Multi-Modal Crime Correlation</span>
                  <span className="text-[#df0095] font-bold shrink-0 ml-2">99.4% MATCH</span>
                </div>
              </div>

              {/* CARD HEADLINE & INFO */}
              <div className="mt-5 space-y-2">
                <h3 className="text-xl sm:text-2xl font-black text-white font-mono tracking-tight">
                  Connect Dots <br />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#df0095] via-purple-300 to-cyan-300">
                    for PS 189
                  </span>
                </h3>

                <p className="text-xs text-white/70 font-sans max-w-xs mx-auto leading-relaxed">
                  Turning scattered data into safer communities.
                </p>
              </div>

              {/* ACTION BUTTON */}
              <div className="mt-5">
                <Link
                  href="/overview"
                  className="inline-flex items-center gap-2 rounded-full bg-white hover:bg-slate-100 text-slate-950 px-6 py-2.5 text-xs font-black uppercase tracking-wider shadow-[0_4px_20px_rgba(255,255,255,0.3)] hover:scale-105 active:scale-95 transition-all duration-200"
                >
                  <span>Explore The Path</span>
                  <ArrowRight className="h-3.5 w-3.5 text-slate-950" />
                </Link>
              </div>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* RIGHT: 3 ACTIONABLE OUTCOMES (Columns 9-12) */}
          {/* ========================================================================= */}
          <div className="lg:col-span-3 flex flex-col gap-3.5 z-10">
            {outputImpacts.map((item, idx) => {
              const Icon = item.icon;
              const isHovered = activeOutput === idx;

              return (
                <div
                  key={item.id}
                  onMouseEnter={() => setActiveOutput(idx)}
                  onMouseLeave={() => setActiveOutput(null)}
                  className={`group relative rounded-2xl border transition-all duration-300 p-4 cursor-pointer backdrop-blur-xl ${
                    isHovered
                      ? "border-white/40 bg-white/[0.08] shadow-[0_10px_30px_-5px_var(--glow)] scale-[1.02] -translate-y-0.5"
                      : "border-white/10 bg-[#090912]/80 hover:border-white/20 hover:bg-white/[0.04]"
                  }`}
                  style={{ "--glow": item.glow } as React.CSSProperties}
                >
                  {/* Connecting Socket Dot on Left Edge with Ref */}
                  <div
                    ref={(el) => {
                      outputSocketRefs.current[idx] = el;
                    }}
                    className={`hidden lg:block absolute -left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 rounded-full border-2 border-[#090912] transition-all duration-300 shadow-md ${
                      isHovered ? "scale-125 ring-2 ring-white/50" : "opacity-60"
                    }`}
                    style={{ backgroundColor: item.color }}
                  />

                  <div className="flex items-center gap-3.5">
                    {/* Icon Box */}
                    <div
                      className="p-3 rounded-xl border shrink-0 transition-transform duration-300 group-hover:scale-110"
                      style={{
                        backgroundColor: `${item.color}15`,
                        borderColor: `${item.color}40`,
                        color: item.color,
                      }}
                    >
                      <Icon className="h-5 w-5" />
                    </div>

                    {/* Text Details */}
                    <div className="flex-1 min-w-0 text-left">
                      <h4 className="text-xs sm:text-sm font-bold text-white font-mono leading-snug">
                        {item.title}
                      </h4>
                      <p className="text-[0.68rem] text-white/60 font-sans leading-snug mt-1">
                        {item.desc}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Data Finds Answers Floating Tag */}
            <div className="mt-2 text-right">
              <span className="inline-block text-[0.68rem] font-mono text-cyan-300/80 bg-cyan-950/40 border border-cyan-500/20 px-3 py-1 rounded-full">
                Data Finds Answers ✨
              </span>
            </div>
          </div>

        </div>
      </div>

      {/* FOOTER STRIP */}
      <div className="mt-14 pt-6 border-t border-white/[0.08] flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-xs text-white/50">
        <span className="tracking-wide">People. Data. Safer Communities.</span>

        <div className="flex flex-col items-center gap-1.5">
          <div className="tracking-[0.25em] uppercase font-bold text-[0.68rem] text-white/70">
            Analyze · Understand · Act · A Safer Tomorrow
          </div>
          <div className="w-48 h-0.5 bg-gradient-to-r from-[#df0095] via-purple-500 to-cyan-400 rounded-full" />
        </div>

        <span className="text-violet-400 font-semibold tracking-wider">
          ConnectDots AI Platform
        </span>
      </div>
    </section>
  );
}
