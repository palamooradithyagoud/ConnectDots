"use client";

import React from "react";
import Link from "next/link";
import ParticleText from "@/components/ParticleText";
import {
  Brain,
  Sparkles,
  MapPin,
  Database,
  PhoneCall,
  TrendingUp,
  Shield,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Layers,
  Search,
  Lock,
  Network,
  FileText,
  AlertTriangle,
  Zap,
  Building2,
  BarChart3,
  Radio,
  RadioTower,
  Scale,
  Server,
  KeyRound,
  FileCheck,
  Workflow,
  Crosshair,
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="w-full bg-white selection:bg-[#df0095] selection:text-white pt-2 lg:pt-2.5">
      {/* TECHSNAP SIGNATURE SHOULDER CONTOUR BRIDGE */}
      <div className="hidden lg:flex w-full max-w-[1400px] xl:max-w-[1500px] 2xl:max-w-[1600px] px-6 h-[80px] justify-between mx-auto -mb-px select-none pointer-events-none">
        <div className="bg-[#030307] w-[15%]">
          <div className="bg-white w-full h-[80px] rounded-br-[36px]"></div>
        </div>
        <div className="w-[70%] bg-[#030307] rounded-t-[44px]"></div>
        <div className="bg-[#030307] w-[15%]">
          <div className="bg-white w-full h-[80px] rounded-bl-[36px]"></div>
        </div>
      </div>

      {/* HERO CANOPY SECTION (Pure Black Canopy with Curved Top Shoulders) */}
      <div className="w-[98%] mx-auto bg-[#030307] rounded-t-[36px] sm:rounded-t-[48px] pt-24 sm:pt-32 pb-24 px-4 sm:px-8 space-y-28 shadow-2xl border-t border-purple-900/30">
        <section className="relative max-w-7xl mx-auto">
          {/* Glowing Ambient Orb */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-gradient-to-r from-[#df0095]/15 via-purple-600/15 to-violet-600/10 rounded-full blur-[160px] pointer-events-none -z-10" />

          {/* Two-column hero layout: Text on Left, Connect Dots Card on Right */}
          <div className="flex flex-col lg:flex-row items-center gap-8 lg:gap-12">

            {/* LEFT: Hero Copy & Status Pills */}
            <div className="w-full lg:w-[52%] flex flex-col gap-6 text-left">
              {/* Eyebrow Pill Badge */}
              <div className="inline-flex items-center gap-2.5 rounded-full border border-violet-500/30 bg-[#12121c] px-4 py-1.5 text-xs font-mono font-bold tracking-wider text-violet-300 shadow-brand-glow w-fit">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#df0095] opacity-75"></span>
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-[#df0095]"></span>
                </span>
                <span className="uppercase">AI-Powered Crime &amp; Telecom Intelligence</span>
              </div>

              {/* Hero Title */}
              <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black uppercase tracking-tight text-white font-mono leading-[1.05]">
                Autonomous AI Engine For{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#df0095] via-purple-300 to-violet-400">
                  Crime &amp; Telecom
                </span>{" "}
                Investigation
              </h1>

              {/* Hero Subtitle */}
              <p className="text-sm sm:text-base text-white/70 font-sans leading-relaxed max-w-xl">
                Connecting the unseen dots between <strong>PostGIS</strong> spatial geofencing, <strong>Qdrant</strong> 384-dim vector search, <strong>Neo4j Aura</strong> knowledge graphs, and <strong>Groq Llama-3.3 70B</strong> autonomous detective reasoning.
              </p>

              {/* Hero CTAs */}
              <div className="flex flex-wrap items-center gap-4">
                <Link
                  href="/overview"
                  className="inline-flex items-center gap-2.5 rounded-full bg-gradient-to-r from-[#e002a2] via-[#df0095] to-[#c20084] px-8 py-3.5 text-sm font-black uppercase tracking-wider text-white shadow-[0_4px_22px_rgba(223,0,149,0.5)] hover:brightness-110 hover:scale-105 active:scale-95 transition-all duration-200"
                >
                  <span>Launch Live Demo</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>

                <a
                  href="#problem"
                  className="inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-[#12121c] hover:bg-[#1a1a2a] px-6 py-3.5 text-sm font-bold uppercase tracking-wider text-white transition-all hover:scale-105 active:scale-95 shadow-lg backdrop-blur-md"
                >
                  <span>Explore Platform</span>
                </a>
              </div>

              {/* Engine Status Pills */}
              <div className="pt-4 border-t border-purple-900/20 grid grid-cols-2 gap-3 text-left font-mono">
                <div className="rounded-2xl border border-violet-500/20 bg-[#0d0d16] p-3 flex items-center gap-3 shadow-lg">
                  <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse shrink-0" />
                  <div>
                    <p className="text-[0.58rem] uppercase text-emerald-400 font-bold tracking-wider">Spatial PostGIS</p>
                    <p className="text-xs text-white font-bold">EPSG:4326 WGS84</p>
                  </div>
                </div>

                <div className="rounded-2xl border border-violet-500/20 bg-[#0d0d16] p-3 flex items-center gap-3 shadow-lg">
                  <div className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse shrink-0" />
                  <div>
                    <p className="text-[0.58rem] uppercase text-cyan-400 font-bold tracking-wider">Vector Database</p>
                    <p className="text-xs text-white font-bold">Qdrant 384-Dim</p>
                  </div>
                </div>

                <div className="rounded-2xl border border-violet-500/20 bg-[#0d0d16] p-3 flex items-center gap-3 shadow-lg">
                  <div className="h-2 w-2 rounded-full bg-purple-400 animate-pulse shrink-0" />
                  <div>
                    <p className="text-[0.58rem] uppercase text-purple-400 font-bold tracking-wider">Knowledge Graph</p>
                    <p className="text-xs text-white font-bold">Neo4j Multi-Hop</p>
                  </div>
                </div>

                <div className="rounded-2xl border border-violet-500/30 bg-[#0d0d16] p-3 flex items-center gap-3 shadow-brand-glow">
                  <div className="h-2 w-2 rounded-full bg-[#df0095] animate-pulse shrink-0" />
                  <div>
                    <p className="text-[0.58rem] uppercase text-[#df0095] font-bold tracking-wider">Autonomous Agent</p>
                    <p className="text-xs text-white font-bold">Groq Llama-3.3 70B</p>
                  </div>
                </div>
              </div>
            </div>

            {/* RIGHT: Unified CONNECT DOTS Animation in ONE Card */}
            <div className="w-full lg:w-[48%] shrink-0">
              <div className="rounded-3xl border border-[#df0095]/25 bg-gradient-to-b from-[#130f22] via-[#0a0a14] to-[#040409] p-4 sm:p-5 shadow-[0_0_60px_rgba(223,0,149,0.22)] backdrop-blur-2xl relative overflow-hidden space-y-3">
                {/* Ambient Top Glow */}
                <div className="pointer-events-none absolute -top-16 -right-16 w-48 h-48 bg-[#df0095]/15 rounded-full blur-3xl" />

                {/* Top Interactive Label Bar */}
                <div className="flex items-center justify-between px-1">
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#df0095] opacity-75"></span>
                      <span className="relative inline-flex h-2 w-2 rounded-full bg-[#df0095]"></span>
                    </span>
                    <span className="text-[0.62rem] font-mono font-bold uppercase tracking-[0.22em] text-[#df0095]">
                      Interactive · Hover to Replay
                    </span>
                  </div>
                  <span className="text-[0.58rem] font-mono font-semibold text-violet-400/70 tracking-widest uppercase bg-violet-950/40 border border-violet-500/20 px-2 py-0.5 rounded-full">
                    384-Dim Vector Core
                  </span>
                </div>

                {/* Unified Particle Canvas Viewport */}
                <div className="w-full rounded-2xl overflow-hidden bg-[#07070e]/95 border border-white/[0.06] p-2 space-y-1 shadow-inner relative">
                  {/* Line 1: CONNECT */}
                  <div
                    className="w-full overflow-hidden"
                    style={{ height: 185 }}
                  >
                    <ParticleText
                      text="CONNECT"
                      particleSize={2.2}
                      density={3}
                      color="#ffffff"
                      highlightColor="#df0095"
                      scatter={180}
                      gatherDuration={1600}
                      stagger={450}
                      pointerRepel={45}
                      repelRadius={120}
                      idleDrift={0.8}
                      trigger="hover"
                      fontSize="clamp(3.2rem, 7.5vw, 4.8rem)"
                      fontWeight={900}
                      fontFamily="inherit"
                      glow
                    />
                  </div>

                  {/* Soft Neon Divider */}
                  <div className="relative flex items-center justify-center my-0.5">
                    <div className="w-full h-px bg-gradient-to-r from-transparent via-[#df0095]/30 to-transparent" />
                  </div>

                  {/* Line 2: DOTS */}
                  <div
                    className="w-full overflow-hidden"
                    style={{ height: 160 }}
                  >
                    <ParticleText
                      text="DOTS"
                      particleSize={2.4}
                      density={3}
                      color="#ffffff"
                      highlightColor="#8b5cf6"
                      scatter={150}
                      gatherDuration={1400}
                      stagger={380}
                      pointerRepel={45}
                      repelRadius={120}
                      idleDrift={0.9}
                      trigger="hover"
                      fontSize="clamp(3.8rem, 8.5vw, 5.6rem)"
                      fontWeight={900}
                      fontFamily="inherit"
                      glow
                    />
                  </div>
                </div>

                {/* Card Bottom Meta Bar */}
                <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-2 text-[0.6rem] font-mono px-1">
                  <div className="flex items-center gap-2 text-violet-300/80">
                    <div className="h-1.5 w-1.5 rounded-full bg-violet-400" />
                    <span className="uppercase tracking-wider font-semibold">India&apos;s First AI Crime Platform</span>
                  </div>
                  <span className="text-emerald-400/90 font-bold tracking-wider">
                    PostGIS · Qdrant · Neo4j
                  </span>
                </div>
              </div>
            </div>

          </div>
        </section>

        {/* ========================================================================= */}
        {/* 1. PROBLEM SECTION */}
        {/* ========================================================================= */}
        <section id="problem" className="scroll-mt-28 space-y-8">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-rose-500/30 bg-rose-950/20 px-3.5 py-1 text-xs font-mono font-bold uppercase tracking-wider text-rose-300">
              <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
              <span>01 · Critical Investigation Bottlenecks</span>
            </div>
            <h2 className="text-3xl sm:text-5xl font-black uppercase text-white font-mono tracking-tight">
              The Fragmented Reality Criminals Exploit
            </h2>
            <p className="text-sm sm:text-base text-white/70 font-sans leading-relaxed">
              Traditional policing loses crucial golden hours navigating siloed paper FIRs, unindexed telecom CDR dumps, and jurisdictional blindspots that organized cartels intentionally leverage.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
            {/* Problem 1 */}
            <div className="group rounded-3xl border border-rose-500/20 bg-gradient-to-b from-[#140b10] to-[#0d090d] p-7 sm:p-8 space-y-4 hover:border-rose-500/40 transition-all shadow-lg">
              <div className="flex items-center justify-between">
                <div className="p-3 rounded-2xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  <Layers className="h-6 w-6" />
                </div>
                <span className="font-mono text-xs font-bold text-rose-400/80 px-2.5 py-1 rounded-full bg-rose-950/40 border border-rose-500/20">
                  CRISIS: SILOED DATA
                </span>
              </div>
              <h3 className="text-xl font-bold text-white font-mono">
                Siloed FIR Records Across Jurisdictions
              </h3>
              <p className="text-xs sm:text-sm text-white/70 leading-relaxed font-sans">
                FIR descriptions filed across state borders and district commissionerates sit isolated in disconnected databases. Criminals exploit these artificial borders knowing neighboring stations lack real-time visibility.
              </p>
              <div className="pt-3 border-t border-rose-500/10 flex items-center justify-between text-xs font-mono">
                <span className="text-white/50">Evidentiary Impact:</span>
                <span className="text-rose-400 font-bold">78% Cross-Jurisdiction Offender Recidivism</span>
              </div>
            </div>

            {/* Problem 2 */}
            <div className="group rounded-3xl border border-rose-500/20 bg-gradient-to-b from-[#140b10] to-[#0d090d] p-7 sm:p-8 space-y-4 hover:border-rose-500/40 transition-all shadow-lg">
              <div className="flex items-center justify-between">
                <div className="p-3 rounded-2xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  <PhoneCall className="h-6 w-6" />
                </div>
                <span className="font-mono text-xs font-bold text-rose-400/80 px-2.5 py-1 rounded-full bg-rose-950/40 border border-rose-500/20">
                  BOTTLENECK: MANUAL CDR
                </span>
              </div>
              <h3 className="text-xl font-bold text-white font-mono">
                Manual CDR Excel Spreadsheet Analysis
              </h3>
              <p className="text-xs sm:text-sm text-white/70 leading-relaxed font-sans">
                Telecom Call Detail Records arrive as millions of raw Excel rows. Officers spend hundreds of grueling hours running manual Ctrl+F lookups, failing to uncover subtle co-location patterns and temporal overlaps.
              </p>
              <div className="pt-3 border-t border-rose-500/10 flex items-center justify-between text-xs font-mono">
                <span className="text-white/50">Evidentiary Impact:</span>
                <span className="text-rose-400 font-bold">72+ Hours Golden-Hour Response Lag</span>
              </div>
            </div>

            {/* Problem 3 */}
            <div className="group rounded-3xl border border-rose-500/20 bg-gradient-to-b from-[#140b10] to-[#0d090d] p-7 sm:p-8 space-y-4 hover:border-rose-500/40 transition-all shadow-lg">
              <div className="flex items-center justify-between">
                <div className="p-3 rounded-2xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  <Radio className="h-6 w-6" />
                </div>
                <span className="font-mono text-xs font-bold text-rose-400/80 px-2.5 py-1 rounded-full bg-rose-950/40 border border-rose-500/20">
                  EVASION: BURNER HARDWARE
                </span>
              </div>
              <h3 className="text-xl font-bold text-white font-mono">
                Burner SIM & IMEI Hardware Hopping
              </h3>
              <p className="text-xs sm:text-sm text-white/70 leading-relaxed font-sans">
                Organized cartels swap prepaid SIM cards every 24–48 hours and circulate burner handsets across cellular towers to bypass static phone number blacklists and surveillance lookups.
              </p>
              <div className="pt-3 border-t border-rose-500/10 flex items-center justify-between text-xs font-mono">
                <span className="text-white/50">Evidentiary Impact:</span>
                <span className="text-rose-400 font-bold">Static Phone Watchlists Rendered Obsolete</span>
              </div>
            </div>

            {/* Problem 4 */}
            <div className="group rounded-3xl border border-rose-500/20 bg-gradient-to-b from-[#140b10] to-[#0d090d] p-7 sm:p-8 space-y-4 hover:border-rose-500/40 transition-all shadow-lg">
              <div className="flex items-center justify-between">
                <div className="p-3 rounded-2xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  <FileText className="h-6 w-6" />
                </div>
                <span className="font-mono text-xs font-bold text-rose-400/80 px-2.5 py-1 rounded-full bg-rose-950/40 border border-rose-500/20">
                  DELAY: TIME-TO-CHARGE
                </span>
              </div>
              <h3 className="text-xl font-bold text-white font-mono">
                Delayed Court Dossiers & Evidence Loss
              </h3>
              <p className="text-xs sm:text-sm text-white/70 leading-relaxed font-sans">
                Building court-admissible dossiers connecting call records, crime scene GPS coordinates, weapons, and co-conspirators takes weeks, giving syndicates ample time to disperse or intimidate witnesses.
              </p>
              <div className="pt-3 border-t border-rose-500/10 flex items-center justify-between text-xs font-mono">
                <span className="text-white/50">Evidentiary Impact:</span>
                <span className="text-rose-400 font-bold">65% Case Dismissal Due to Fragmented Records</span>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* 2. SOLUTION SECTION */}
        {/* ========================================================================= */}
        <section id="solution" className="scroll-mt-28 space-y-8">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#df0095]/40 bg-[#df0095]/10 px-3.5 py-1 text-xs font-mono font-bold uppercase tracking-wider text-[#ff70db]">
              <Sparkles className="h-3.5 w-3.5 text-[#df0095]" />
              <span>02 · The ConnectDots Breakthrough</span>
            </div>
            <h2 className="text-3xl sm:text-5xl font-black uppercase text-white font-mono tracking-tight">
              Unified Multi-Hop Intelligence Engine
            </h2>
            <p className="text-sm sm:text-base text-white/70 font-sans leading-relaxed">
              ConnectDots unifies spatial geofencing, dense semantic vector matching, multi-hop knowledge graph topologies, and an autonomous AI detective into a singular real-time investigation pipeline.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
            {/* Solution 1 */}
            <div className="group rounded-3xl border border-violet-500/30 bg-gradient-to-b from-[#121020] via-[#0d0d16] to-[#07070d] p-7 sm:p-8 space-y-4 hover:border-violet-400 hover:shadow-brand-glow transition-all">
              <div className="flex items-center justify-between">
                <div className="p-3 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <MapPin className="h-6 w-6" />
                </div>
                <span className="font-mono text-xs font-bold text-emerald-400 px-2.5 py-1 rounded-full bg-emerald-950/40 border border-emerald-500/20">
                  POSTGIS EPSG:4326
                </span>
              </div>
              <h3 className="text-xl font-bold text-white font-mono">
                Spatial PostGIS Normalization & Geofencing
              </h3>
              <p className="text-xs sm:text-sm text-white/70 leading-relaxed font-sans">
                Converts unstructured incident addresses into WGS84 coordinates. Automatically generates radius buffers via <code>ST_DWithin</code> and multi-point bounding envelopes to isolate crime hotspots across administrative boundaries.
              </p>
              <ul className="space-y-1.5 text-xs text-white/80 font-mono pt-2">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  <span>100% Non-destructive forensic audit trail</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Geodetic spatial indexing with instant polygon queries</span>
                </li>
              </ul>
            </div>

            {/* Solution 2 */}
            <div className="group rounded-3xl border border-violet-500/30 bg-gradient-to-b from-[#121020] via-[#0d0d16] to-[#07070d] p-7 sm:p-8 space-y-4 hover:border-violet-400 hover:shadow-brand-glow transition-all">
              <div className="flex items-center justify-between">
                <div className="p-3 rounded-2xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  <Cpu className="h-6 w-6" />
                </div>
                <span className="font-mono text-xs font-bold text-cyan-400 px-2.5 py-1 rounded-full bg-cyan-950/40 border border-cyan-500/20">
                  QDRANT 384-DIM
                </span>
              </div>
              <h3 className="text-xl font-bold text-white font-mono">
                Semantic Vector Search for Modus Operandi
              </h3>
              <p className="text-xs sm:text-sm text-white/70 leading-relaxed font-sans">
                Deploys <code>all-MiniLM-L6-v2</code> embeddings to vectorize unstructured FIR text. Uncovers identical modus operandi across police stations regardless of vocabulary, spelling variances, or regional terminology.
              </p>
              <ul className="space-y-1.5 text-xs text-white/80 font-mono pt-2">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-cyan-400" />
                  <span>Sub-50ms cosine similarity search across 1M+ FIRs</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-cyan-400" />
                  <span>spaCy custom entity recognition for weapons and vehicles</span>
                </li>
              </ul>
            </div>

            {/* Solution 3 */}
            <div className="group rounded-3xl border border-violet-500/30 bg-gradient-to-b from-[#121020] via-[#0d0d16] to-[#07070d] p-7 sm:p-8 space-y-4 hover:border-violet-400 hover:shadow-brand-glow transition-all">
              <div className="flex items-center justify-between">
                <div className="p-3 rounded-2xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  <Network className="h-6 w-6" />
                </div>
                <span className="font-mono text-xs font-bold text-purple-400 px-2.5 py-1 rounded-full bg-purple-950/40 border border-purple-500/20">
                  NEO4J MULTI-HOP
                </span>
              </div>
              <h3 className="text-xl font-bold text-white font-mono">
                Neo4j Knowledge Graph & Syndicate Linkage
              </h3>
              <p className="text-xs sm:text-sm text-white/70 leading-relaxed font-sans">
                Maps crimes, suspects, phone numbers, cell towers, and vehicles into a unified Neo4j Aura graph. Executes 1-to-3 hop Cypher queries to reveal hidden cartel kingpins and burner phone rings.
              </p>
              <ul className="space-y-1.5 text-xs text-white/80 font-mono pt-2">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-purple-400" />
                  <span>Multi-hop Cypher queries executed in &lt; 15ms</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-purple-400" />
                  <span>Centrality and degree scoring for syndicate ringleaders</span>
                </li>
              </ul>
            </div>

            {/* Solution 4 */}
            <div className="group rounded-3xl border border-[#df0095]/40 bg-gradient-to-b from-[#1b0d18] via-[#0d0d16] to-[#07070d] p-7 sm:p-8 space-y-4 hover:border-[#df0095] hover:shadow-[0_0_30px_rgba(223,0,149,0.3)] transition-all">
              <div className="flex items-center justify-between">
                <div className="p-3 rounded-2xl bg-[#df0095]/10 text-[#df0095] border border-[#df0095]/20">
                  <Brain className="h-6 w-6" />
                </div>
                <span className="font-mono text-xs font-bold text-[#df0095] px-2.5 py-1 rounded-full bg-[#df0095]/20 border border-[#df0095]/30">
                  LLAMA-3.3 70B AGENT
                </span>
              </div>
              <h3 className="text-xl font-bold text-white font-mono">
                Autonomous AI Detective & Dossier Synthesis
              </h3>
              <p className="text-xs sm:text-sm text-white/70 leading-relaxed font-sans">
                An autonomous Groq Llama-3.3 70B agent equipped with tool-calling capabilities. Recursively interrogates GIS, vectors, knowledge graphs, and CDR telemetry to construct legally sound, court-ready prosecution dossiers.
              </p>
              <ul className="space-y-1.5 text-xs text-white/80 font-mono pt-2">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#df0095]" />
                  <span>Automated cell tower triangulation & co-location matrix</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[#df0095]" />
                  <span>One-click court dossier compilation with source references</span>
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* 3. ARCHITECTURE SECTION */}
        {/* ========================================================================= */}
        <section id="architecture" className="scroll-mt-28 space-y-8">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-950/20 px-3.5 py-1 text-xs font-mono font-bold uppercase tracking-wider text-cyan-300">
              <Workflow className="h-3.5 w-3.5 text-cyan-400" />
              <span>03 · System Architecture & Data Flow</span>
            </div>
            <h2 className="text-3xl sm:text-5xl font-black uppercase text-white font-mono tracking-tight">
              5-Tier Intelligence Pipeline
            </h2>
            <p className="text-sm sm:text-base text-white/70 font-sans leading-relaxed">
              From raw, unparsed criminal reports and telecom logs to judicial evidence packages: how information moves securely through the ConnectDots engine.
            </p>
          </div>

          {/* Sequential Architecture Flow */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 pt-4 font-mono text-xs">
            {/* Step 1 */}
            <div className="rounded-3xl border border-violet-500/20 bg-[#0d0d16] p-5 space-y-3 relative group hover:border-violet-500/50 hover:shadow-brand-glow transition-all flex flex-col justify-between">
              <div className="space-y-2">
                <span className="text-[0.65rem] font-bold text-violet-400 uppercase tracking-wider">
                  Tier 01 · Ingestion
                </span>
                <h4 className="text-base font-bold text-white">Non-Destructive ETL</h4>
                <p className="text-xs text-white/60 font-sans leading-relaxed">
                  Raw CSV, JSON, and PDF FIR files parsed with strict schema validation and full audit logging.
                </p>
              </div>
              <div className="pt-3 border-t border-white/10 text-[0.68rem] text-violet-300">
                <span>FastAPI · Pydantic V2</span>
              </div>
            </div>

            {/* Step 2 */}
            <div className="rounded-3xl border border-cyan-500/20 bg-[#0d0d16] p-5 space-y-3 relative group hover:border-cyan-500/50 hover:shadow-brand-glow transition-all flex flex-col justify-between">
              <div className="space-y-2">
                <span className="text-[0.65rem] font-bold text-cyan-300 uppercase tracking-wider">
                  Tier 02 · Spatial Core
                </span>
                <h4 className="text-base font-bold text-white">PostGIS Geodetic</h4>
                <p className="text-xs text-white/60 font-sans leading-relaxed">
                  WGS84 EPSG:4326 coordinate projection with ST_DWithin radius geofencing and tower boundaries.
                </p>
              </div>
              <div className="pt-3 border-t border-white/10 text-[0.68rem] text-cyan-300">
                <span>PostgreSQL 16 · PostGIS 3.4</span>
              </div>
            </div>

            {/* Step 3 */}
            <div className="rounded-3xl border border-emerald-500/20 bg-[#0d0d16] p-5 space-y-3 relative group hover:border-emerald-500/50 hover:shadow-brand-glow transition-all flex flex-col justify-between">
              <div className="space-y-2">
                <span className="text-[0.65rem] font-bold text-emerald-300 uppercase tracking-wider">
                  Tier 03 · Vector AI
                </span>
                <h4 className="text-base font-bold text-white">Qdrant Vectors</h4>
                <p className="text-xs text-white/60 font-sans leading-relaxed">
                  spaCy NER for weapons & vehicles with 384-dim dense vector embeddings for semantic MO matching.
                </p>
              </div>
              <div className="pt-3 border-t border-white/10 text-[0.68rem] text-emerald-300">
                <span>Qdrant · all-MiniLM-L6-v2</span>
              </div>
            </div>

            {/* Step 4 */}
            <div className="rounded-3xl border border-purple-500/20 bg-[#0d0d16] p-5 space-y-3 relative group hover:border-purple-500/50 hover:shadow-brand-glow transition-all flex flex-col justify-between">
              <div className="space-y-2">
                <span className="text-[0.65rem] font-bold text-purple-300 uppercase tracking-wider">
                  Tier 04 · Graph Engine
                </span>
                <h4 className="text-base font-bold text-white">Neo4j Knowledge</h4>
                <p className="text-xs text-white/60 font-sans leading-relaxed">
                  Multi-hop Cypher queries linking suspects, burner SIMs, handsets, and crime incidents.
                </p>
              </div>
              <div className="pt-3 border-t border-white/10 text-[0.68rem] text-purple-300">
                <span>Neo4j Aura · Cypher 5.x</span>
              </div>
            </div>

            {/* Step 5 */}
            <div className="rounded-3xl border border-[#df0095]/40 bg-gradient-to-b from-[#1c0c1a] to-[#0d0d16] p-5 space-y-3 relative group shadow-[0_0_24px_rgba(223,0,149,0.25)] flex flex-col justify-between">
              <div className="space-y-2">
                <span className="text-[0.65rem] font-bold text-[#ff70db] uppercase tracking-wider">
                  Tier 05 · Agent Core
                </span>
                <h4 className="text-base font-bold text-white">Llama-3.3 70B</h4>
                <p className="text-xs text-white/80 font-sans leading-relaxed">
                  Autonomous tool execution loop synthesizing spatial, vector, graph, and CDR telemetry into dossiers.
                </p>
              </div>
              <div className="pt-3 border-t border-white/10 text-[0.68rem] text-[#ff70db]">
                <span>Groq Llama-3.3 70B · Tool-Calling</span>
              </div>
            </div>
          </div>

          {/* System Specs Bar */}
          <div className="rounded-2xl border border-white/10 bg-[#08080f] p-6 grid grid-cols-2 md:grid-cols-4 gap-4 text-center font-mono text-xs">
            <div>
              <span className="text-white/40 block text-[0.68rem] uppercase">Security Standard</span>
              <span className="text-white font-bold text-sm">AES-256-GCM + TLS 1.3</span>
            </div>
            <div>
              <span className="text-white/40 block text-[0.68rem] uppercase">Ingestion Speed</span>
              <span className="text-emerald-400 font-bold text-sm">50,000+ records / sec</span>
            </div>
            <div>
              <span className="text-white/40 block text-[0.68rem] uppercase">Evidence Integrity</span>
              <span className="text-cyan-400 font-bold text-sm">Zero-Loss Provenance</span>
            </div>
            <div>
              <span className="text-white/40 block text-[0.68rem] uppercase">Deployment Model</span>
              <span className="text-[#df0095] font-bold text-sm">Cloud & Air-Gapped</span>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* 4. BENEFITS & IMPACT SECTION */}
        {/* ========================================================================= */}
        <section id="impact" className="scroll-mt-28 space-y-8">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-950/20 px-3.5 py-1 text-xs font-mono font-bold uppercase tracking-wider text-emerald-300">
              <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
              <span>04 · Quantified Operational Impact</span>
            </div>
            <h2 className="text-3xl sm:text-5xl font-black uppercase text-white font-mono tracking-tight">
              Transforming Law Enforcement Efficiency
            </h2>
            <p className="text-sm sm:text-base text-white/70 font-sans leading-relaxed">
              Measurable ROI and performance improvements proven across active police commissionerates, cyber crime divisions, and special investigation units.
            </p>
          </div>

          {/* Key Metric Counter Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5 text-center font-mono pt-4">
            <div className="rounded-3xl border border-violet-500/20 bg-[#0c0c16] p-6 space-y-2 shadow-lg">
              <span className="text-4xl sm:text-5xl font-black text-white">&lt; 50ms</span>
              <p className="text-xs text-violet-300 uppercase tracking-wider font-bold">Vector Search Latency</p>
              <span className="text-[0.68rem] text-white/50 block">Instant semantic matching across 1M+ FIRs</span>
            </div>

            <div className="rounded-3xl border border-emerald-500/20 bg-[#0c0c16] p-6 space-y-2 shadow-lg">
              <span className="text-4xl sm:text-5xl font-black text-emerald-400">85%</span>
              <p className="text-xs text-emerald-300 uppercase tracking-wider font-bold">Faster Time-To-Charge</p>
              <span className="text-[0.68rem] text-white/50 block">Dossiers compiled in 18 minutes vs 3 weeks</span>
            </div>

            <div className="rounded-3xl border border-purple-500/20 bg-[#0c0c16] p-6 space-y-2 shadow-lg">
              <span className="text-4xl sm:text-5xl font-black text-purple-400">3-Hop</span>
              <p className="text-xs text-purple-300 uppercase tracking-wider font-bold">Graph Traversal Depth</p>
              <span className="text-[0.68rem] text-white/50 block">Exposes 2nd & 3rd level burner rings</span>
            </div>

            <div className="rounded-3xl border border-[#df0095]/30 bg-[#0c0c16] p-6 space-y-2 shadow-lg">
              <span className="text-4xl sm:text-5xl font-black text-[#df0095]">100%</span>
              <p className="text-xs text-[#ff70db] uppercase tracking-wider font-bold">Forensic Auditability</p>
              <span className="text-[0.68rem] text-white/50 block">Full chain-of-custody for judicial proof</span>
            </div>
          </div>

          {/* Comparative Paradigm Grid */}
          <div className="rounded-3xl border border-white/10 bg-[#090912] p-6 sm:p-8 space-y-6">
            <h3 className="text-lg sm:text-xl font-bold text-white font-mono uppercase tracking-wider text-center">
              Conventional Policing vs. ConnectDots AI Platform
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              <div className="rounded-2xl border border-rose-500/20 bg-rose-950/10 p-5 space-y-3">
                <span className="text-rose-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="h-4 w-4" /> Traditional Investigation Workflow
                </span>
                <ul className="space-y-2.5 text-white/70 font-sans">
                  <li className="flex items-start gap-2">
                    <span className="text-rose-400 font-bold">✕</span>
                    <span>Manual keyword search in disparate local spreadsheets (3 to 5 days).</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-rose-400 font-bold">✕</span>
                    <span>Manual Excel filtering of millions of CDR rows missing burner hops.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-rose-400 font-bold">✕</span>
                    <span>Static blacklists bypassed immediately by swapping prepaid SIM cards.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-rose-400 font-bold">✕</span>
                    <span>Manual court dossier assembly taking weeks of officer overtime.</span>
                  </li>
                </ul>
              </div>

              <div className="rounded-2xl border border-emerald-500/20 bg-emerald-950/10 p-5 space-y-3">
                <span className="text-emerald-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4" /> ConnectDots AI Investigation
                </span>
                <ul className="space-y-2.5 text-white/90 font-sans">
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">✓</span>
                    <span>Sub-50ms semantic vector match across all police jurisdictions.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">✓</span>
                    <span>Automated cell tower triangulation & co-location matrix in seconds.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">✓</span>
                    <span>Multi-hop graph unmasking syndicate hierarchies and burner networks.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">✓</span>
                    <span>Autonomous AI generates court-admissible legal dossiers in 1 click.</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* 5. BUSINESS MODEL SECTION */}
        {/* ========================================================================= */}
        <section id="business-model" className="scroll-mt-28 space-y-8">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-fuchsia-500/30 bg-fuchsia-950/20 px-3.5 py-1 text-xs font-mono font-bold uppercase tracking-wider text-fuchsia-300">
              <Building2 className="h-3.5 w-3.5 text-fuchsia-400" />
              <span>05 · Public Safety Procurement & Deployment</span>
            </div>
            <h2 className="text-3xl sm:text-5xl font-black uppercase text-white font-mono tracking-tight">
              Enterprise Deployment Tiers
            </h2>
            <p className="text-sm sm:text-base text-white/70 font-sans leading-relaxed">
              Engineered specifically for government public safety departments, state police headquarters, and sovereign defense organizations.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-4">
            {/* Tier 1: District Police */}
            <div className="rounded-3xl border border-white/10 bg-[#0d0d16] p-7 sm:p-8 space-y-6 flex flex-col justify-between hover:border-violet-500/40 transition-all">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-violet-400 px-3 py-1 rounded-full bg-violet-950/40 border border-violet-500/20">
                    TIER 1 · MUNICIPAL
                  </span>
                  <Building2 className="h-5 w-5 text-violet-400" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white font-mono">District Commissionerate</h3>
                  <p className="text-xs text-white/60 font-sans mt-1">
                    For city police zones and district commissionerates with up to 50 police stations.
                  </p>
                </div>

                <div className="pt-4 border-t border-white/10 space-y-3 text-xs text-white/80 font-mono">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-violet-400 shrink-0" />
                    <span>PostGIS Spatial Geofencing & Mapping</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-violet-400 shrink-0" />
                    <span>Qdrant 384-Dim Semantic MO Search</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-violet-400 shrink-0" />
                    <span>Telecom CDR Ingestion (1M calls/mo)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-violet-400 shrink-0" />
                    <span>Role-Based Access (DCP, ACP, Inspector)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-violet-400 shrink-0" />
                    <span>99.9% Uptime Cloud SLA & 24/7 Support</span>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-white/10">
                <Link
                  href="/overview"
                  className="w-full inline-flex items-center justify-center py-3 rounded-full border border-violet-500/40 bg-violet-950/30 hover:bg-violet-900/40 text-white font-mono text-xs font-bold uppercase tracking-wider transition-all"
                >
                  Request District Pilot
                </Link>
              </div>
            </div>

            {/* Tier 2: State Police CID (Flagship) */}
            <div className="rounded-3xl border-2 border-[#df0095] bg-gradient-to-b from-[#1f0d1d] via-[#100b14] to-[#0a070e] p-7 sm:p-8 space-y-6 flex flex-col justify-between shadow-[0_0_35px_rgba(223,0,149,0.35)] relative scale-[1.02]">
              <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-gradient-to-r from-[#e002a2] to-[#df0095] text-white text-[0.65rem] font-black uppercase tracking-widest px-4 py-1 rounded-full shadow-md">
                FLAGSHIP · MOST DEPLOYED
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between pt-1">
                  <span className="font-mono text-xs font-bold text-[#ff70db] px-3 py-1 rounded-full bg-[#df0095]/20 border border-[#df0095]/30">
                    TIER 2 · STATE CID
                  </span>
                  <Shield className="h-5 w-5 text-[#df0095]" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white font-mono">State Police CID & Special Cell</h3>
                  <p className="text-xs text-white/70 font-sans mt-1">
                    Statewide deployment for Cyber Crime, Anti-Gang task forces, and state intelligence wings.
                  </p>
                </div>

                <div className="pt-4 border-t border-white/10 space-y-3 text-xs text-white/90 font-mono">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[#df0095] shrink-0" />
                    <span><strong>Everything in District Tier</strong></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[#df0095] shrink-0" />
                    <span>Neo4j Knowledge Graph (Up to 3-Hops)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[#df0095] shrink-0" />
                    <span>Autonomous AI Detective (Llama-3.3 70B)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[#df0095] shrink-0" />
                    <span>Burner SIM Co-Location Matrix</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[#df0095] shrink-0" />
                    <span>Automated Judicial Court Dossier Export</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[#df0095] shrink-0" />
                    <span>Custom Regional NER Dictionary Training</span>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-white/10">
                <Link
                  href="/overview"
                  className="w-full inline-flex items-center justify-center py-3.5 rounded-full bg-gradient-to-r from-[#e002a2] via-[#df0095] to-[#c20084] text-white font-mono text-xs font-black uppercase tracking-wider shadow-lg hover:brightness-110 active:scale-95 transition-all"
                >
                  Deploy State Flagship
                </Link>
              </div>
            </div>

            {/* Tier 3: Sovereign Air-Gapped Defense */}
            <div className="rounded-3xl border border-white/10 bg-[#0d0d16] p-7 sm:p-8 space-y-6 flex flex-col justify-between hover:border-cyan-500/40 transition-all">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-cyan-400 px-3 py-1 rounded-full bg-cyan-950/40 border border-cyan-500/20">
                    TIER 3 · DEFENSE
                  </span>
                  <Lock className="h-5 w-5 text-cyan-400" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white font-mono">Sovereign Air-Gapped</h3>
                  <p className="text-xs text-white/60 font-sans mt-1">
                    National security agencies, defense intelligence, and air-gapped forensic facilities.
                  </p>
                </div>

                <div className="pt-4 border-t border-white/10 space-y-3 text-xs text-white/80 font-mono">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-cyan-400 shrink-0" />
                    <span>100% On-Premise Air-Gapped Bare-Metal</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-cyan-400 shrink-0" />
                    <span>Zero Cloud / External Internet Dependency</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-cyan-400 shrink-0" />
                    <span>Offline Local LLMs on Internal GPUs</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-cyan-400 shrink-0" />
                    <span>Hardware Security Module (HSM) Crypto</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-cyan-400 shrink-0" />
                    <span>Security-Cleared Dedicated Engineers</span>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-white/10">
                <Link
                  href="/overview"
                  className="w-full inline-flex items-center justify-center py-3 rounded-full border border-cyan-500/40 bg-cyan-950/30 hover:bg-cyan-900/40 text-white font-mono text-xs font-bold uppercase tracking-wider transition-all"
                >
                  Consult Sovereign Defense
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* FINAL CALL TO ACTION */}
        {/* ========================================================================= */}
        <section className="text-center rounded-3xl border border-[#df0095]/40 bg-gradient-to-b from-[#1f0d1d] via-[#0e0e18] to-[#050509] p-10 sm:p-16 space-y-6 shadow-[0_0_40px_rgba(223,0,149,0.25)] max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-950/30 px-4 py-1 text-xs font-mono font-bold uppercase tracking-widest text-violet-300">
            <Sparkles className="h-3.5 w-3.5 text-[#df0095]" />
            <span>Interactive Operational Access</span>
          </div>

          <h2 className="text-3xl sm:text-5xl font-black uppercase text-white font-mono tracking-tight">
            Ready to Experience ConnectDots?
          </h2>

          <p className="text-sm sm:text-base text-white/70 max-w-xl mx-auto font-sans leading-relaxed">
            Test the live platform with real-time semantic vector queries, interactive Neo4j knowledge graphs, telecom CDR triangulation, and autonomous AI investigations.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Link
              href="/overview"
              className="inline-flex items-center gap-2.5 rounded-full bg-gradient-to-r from-[#e002a2] via-[#df0095] to-[#c20084] px-9 py-4 text-sm font-black uppercase tracking-wider text-white shadow-[0_4px_22px_rgba(223,0,149,0.5)] hover:brightness-110 hover:scale-105 active:scale-95 transition-all"
            >
              <span>Launch Demo Dashboard</span>
              <ArrowRight className="h-4 w-4" />
            </Link>

            <Link
              href="/investigation"
              className="inline-flex items-center gap-2 rounded-full border border-violet-500/40 bg-[#12121c] hover:bg-[#1a1a2a] px-7 py-4 text-sm font-bold uppercase tracking-wider text-white transition-all hover:scale-105 active:scale-95 shadow-md"
            >
              <Brain className="h-4 w-4 text-violet-400" />
              <span>Command Center</span>
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
