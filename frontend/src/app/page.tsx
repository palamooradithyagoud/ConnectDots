"use client";

import React from "react";
import Link from "next/link";
import ParticleText from "@/components/ParticleText";
import StructuredPathSolution from "@/components/StructuredPathSolution";
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
  Check,
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

          {/* Compact 4-Column Problem Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
            {/* Problem 1 */}
            <div className="group rounded-2xl border border-rose-500/20 bg-gradient-to-b from-[#140b10] to-[#0d090d] p-4 sm:p-5 space-y-3 hover:border-rose-500/40 hover:-translate-y-1 transition-all duration-300 shadow-md flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    <Layers className="h-4 w-4" />
                  </div>
                  <span className="font-mono text-[0.58rem] font-bold text-rose-400/90 px-2 py-0.5 rounded-full bg-rose-950/40 border border-rose-500/20 uppercase">
                    Siloed Data
                  </span>
                </div>
                <h3 className="text-sm sm:text-base font-bold text-white font-mono leading-snug">
                  Siloed FIR Records Across Jurisdictions
                </h3>
                <p className="text-xs text-white/70 leading-relaxed font-sans">
                  FIR descriptions filed across state and district borders sit in isolated databases, creating cross-station blindspots.
                </p>
              </div>
              <div className="pt-2.5 border-t border-rose-500/10 text-[0.65rem] font-mono space-y-0.5">
                <span className="text-white/40 block">Evidentiary Impact:</span>
                <span className="text-rose-400 font-bold block">78% Recidivism Gap</span>
              </div>
            </div>

            {/* Problem 2 */}
            <div className="group rounded-2xl border border-rose-500/20 bg-gradient-to-b from-[#140b10] to-[#0d090d] p-4 sm:p-5 space-y-3 hover:border-rose-500/40 hover:-translate-y-1 transition-all duration-300 shadow-md flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    <PhoneCall className="h-4 w-4" />
                  </div>
                  <span className="font-mono text-[0.58rem] font-bold text-rose-400/90 px-2 py-0.5 rounded-full bg-rose-950/40 border border-rose-500/20 uppercase">
                    Manual CDR
                  </span>
                </div>
                <h3 className="text-sm sm:text-base font-bold text-white font-mono leading-snug">
                  Manual CDR Excel Spreadsheet Analysis
                </h3>
                <p className="text-xs text-white/70 leading-relaxed font-sans">
                  Telecom Call Detail Records arrive in millions of rows, requiring manual lookups that miss subtle co-location overlaps.
                </p>
              </div>
              <div className="pt-2.5 border-t border-rose-500/10 text-[0.65rem] font-mono space-y-0.5">
                <span className="text-white/40 block">Evidentiary Impact:</span>
                <span className="text-rose-400 font-bold block">72+ Hour Golden Lag</span>
              </div>
            </div>

            {/* Problem 3 */}
            <div className="group rounded-2xl border border-rose-500/20 bg-gradient-to-b from-[#140b10] to-[#0d090d] p-4 sm:p-5 space-y-3 hover:border-rose-500/40 hover:-translate-y-1 transition-all duration-300 shadow-md flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    <Radio className="h-4 w-4" />
                  </div>
                  <span className="font-mono text-[0.58rem] font-bold text-rose-400/90 px-2 py-0.5 rounded-full bg-rose-950/40 border border-rose-500/20 uppercase">
                    Burner Evasion
                  </span>
                </div>
                <h3 className="text-sm sm:text-base font-bold text-white font-mono leading-snug">
                  Burner SIM & IMEI Hardware Hopping
                </h3>
                <p className="text-xs text-white/70 leading-relaxed font-sans">
                  Cartels rotate prepaid SIMs every 24–48h and swap handsets across cell towers to defeat static phone watchlists.
                </p>
              </div>
              <div className="pt-2.5 border-t border-rose-500/10 text-[0.65rem] font-mono space-y-0.5">
                <span className="text-white/40 block">Evidentiary Impact:</span>
                <span className="text-rose-400 font-bold block">Watchlists Obsolete</span>
              </div>
            </div>

            {/* Problem 4 */}
            <div className="group rounded-2xl border border-rose-500/20 bg-gradient-to-b from-[#140b10] to-[#0d090d] p-4 sm:p-5 space-y-3 hover:border-rose-500/40 hover:-translate-y-1 transition-all duration-300 shadow-md flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    <FileText className="h-4 w-4" />
                  </div>
                  <span className="font-mono text-[0.58rem] font-bold text-rose-400/90 px-2 py-0.5 rounded-full bg-rose-950/40 border border-rose-500/20 uppercase">
                    Dossier Delay
                  </span>
                </div>
                <h3 className="text-sm sm:text-base font-bold text-white font-mono leading-snug">
                  Delayed Court Dossiers & Evidence Loss
                </h3>
                <p className="text-xs text-white/70 leading-relaxed font-sans">
                  Building court-admissible dossiers connecting GPS, call records, and suspects takes weeks of manual assembly.
                </p>
              </div>
              <div className="pt-2.5 border-t border-rose-500/10 text-[0.65rem] font-mono space-y-0.5">
                <span className="text-white/40 block">Evidentiary Impact:</span>
                <span className="text-rose-400 font-bold block">65% Case Dismissals</span>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* 2. SOLUTION SECTION: STRUCTURED PATH WITH ANIMATED THREADS */}
        {/* ========================================================================= */}
        <StructuredPathSolution />


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
        {/* 5. PRICING & ENTERPRISE DEPLOYMENT SECTION */}
        {/* ========================================================================= */}
        <section id="pricing" className="scroll-mt-28 space-y-12">
          <span id="business-model" className="sr-only" />

          {/* Section Header */}
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#df0095]/30 bg-pink-950/20 px-3.5 py-1 text-xs font-mono font-bold uppercase tracking-wider text-pink-300">
              <Sparkles className="h-3.5 w-3.5 text-[#df0095]" />
              <span>05 · Transparent Public Safety Pricing</span>
            </div>
            <h2 className="text-3xl sm:text-5xl font-black uppercase text-white font-mono tracking-tight">
              Predictable Plans, Powerful AI
            </h2>
            <p className="text-sm sm:text-base text-white/70 font-sans leading-relaxed">
              Start free with basic case testing, or equip your entire investigative unit with real-time multi-modal crime correlation.
            </p>
          </div>

          {/* 3 Pricing Tier Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2">
            {/* Free Plan */}
            <div className="rounded-3xl border border-white/10 bg-[#0d0d16] p-7 sm:p-8 space-y-6 flex flex-col justify-between hover:border-slate-400/40 transition-all">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-slate-300 px-3 py-1 rounded-full bg-white/5 border border-white/10">
                    FREE TIER
                  </span>
                  <span className="text-2xl">🆓</span>
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white font-mono">Free Explorer</h3>
                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="font-mono font-black text-4xl text-white">₹0</span>
                  </div>
                  <p className="text-xs text-white/60 font-sans mt-2 leading-relaxed">
                    Perfect for testing, research & initial field exploration.
                  </p>
                </div>

                <div className="pt-4 border-t border-white/10 space-y-2.5 text-xs text-white/80 font-sans">
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span><strong>10 cases/month</strong> FIR / Case Analysis</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span>Limited Data Sources Access</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span>Basic Crime Pattern Detection</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span>Basic Hotspot Detection</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span>Interactive Crime Map (Basic)</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span>30 days Historical Data</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-emerald-400 shrink-0" />
                    <span>Community Support</span>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-white/10">
                <Link
                  href="/overview"
                  className="w-full inline-flex items-center justify-center py-3 rounded-full border border-white/20 bg-white/5 hover:bg-white/10 text-white font-mono text-xs font-bold uppercase tracking-wider transition-all"
                >
                  Get Started Free →
                </Link>
              </div>
            </div>

            {/* Monthly Pro Plan (Highlighted) */}
            <div className="rounded-3xl border-2 border-[#df0095] bg-gradient-to-b from-[#1f0d1d] via-[#100b14] to-[#0a070e] p-7 sm:p-8 space-y-6 flex flex-col justify-between shadow-[0_0_40px_rgba(223,0,149,0.35)] relative lg:scale-[1.03]">
              <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-gradient-to-r from-[#e002a2] to-[#df0095] text-white text-[0.65rem] font-black uppercase tracking-widest px-4 py-1 rounded-full shadow-md whitespace-nowrap">
                POPULAR · INVESTIGATORS
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between pt-1">
                  <span className="font-mono text-xs font-bold text-[#ff70db] px-3 py-1 rounded-full bg-[#df0095]/20 border border-[#df0095]/30">
                    MONTHLY PRO
                  </span>
                  <span className="text-2xl">🚀</span>
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white font-mono">Monthly Pro</h3>
                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="font-mono font-black text-4xl text-white">₹499</span>
                    <span className="text-sm text-white/60 font-sans">/ month</span>
                  </div>
                  <p className="text-xs text-white/70 font-sans mt-2 leading-relaxed">
                    Designed for active station investigators, inspectors & cyber crime units.
                  </p>
                </div>

                <div className="pt-4 border-t border-white/10 space-y-2.5 text-xs text-white/90 font-sans">
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-[#df0095] shrink-0" />
                    <span><strong>Unlimited</strong> FIR / Case Analysis</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-[#df0095] shrink-0" />
                    <span><strong>All Supported Sources</strong> (FIR, CDR, OSINT)</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-[#df0095] shrink-0" />
                    <span><strong>Advanced AI</strong> Pattern Detection</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-[#df0095] shrink-0" />
                    <span>Hotspot Detection &amp; AI Insights</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-[#df0095] shrink-0" />
                    <span>Interactive Crime Map (Advanced)</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-[#df0095] shrink-0" />
                    <span>Trend Analysis &amp; Report Export</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-[#df0095] shrink-0" />
                    <span><strong>2 Years</strong> Historical Data</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-[#df0095] shrink-0" />
                    <span>Priority Processing &amp; Support</span>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-white/10">
                <Link
                  href="/overview"
                  className="w-full inline-flex items-center justify-center py-3.5 rounded-full bg-gradient-to-r from-[#e002a2] via-[#df0095] to-[#c20084] text-white font-mono text-xs font-black uppercase tracking-wider shadow-lg hover:brightness-110 active:scale-95 transition-all"
                >
                  Start Monthly Pro →
                </Link>
              </div>
            </div>

            {/* Yearly Pro Plan */}
            <div className="rounded-3xl border border-purple-500/40 bg-[#0d0d18] p-7 sm:p-8 space-y-6 flex flex-col justify-between hover:border-purple-400 transition-all shadow-[0_0_30px_rgba(168,85,247,0.15)] relative">
              <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-[0.65rem] font-black uppercase tracking-widest px-4 py-1 rounded-full shadow-md whitespace-nowrap">
                👑 BEST VALUE · 2 MONTHS FREE
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between pt-1">
                  <span className="font-mono text-xs font-bold text-purple-300 px-3 py-1 rounded-full bg-purple-950/40 border border-purple-500/30">
                    YEARLY PRO
                  </span>
                  <span className="text-2xl">👑</span>
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white font-mono">Yearly Pro</h3>
                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="font-mono font-black text-4xl text-white">₹4,999</span>
                    <span className="text-sm text-white/60 font-sans">/ year</span>
                  </div>
                  <p className="text-xs text-white/70 font-sans mt-2 leading-relaxed">
                    Maximum value for police commissionerates & intelligence divisions.
                  </p>
                </div>

                <div className="pt-4 border-t border-white/10 space-y-2.5 text-xs text-white/80 font-sans">
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-purple-400 shrink-0" />
                    <span><strong>Everything in Monthly Pro</strong></span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-purple-400 shrink-0" />
                    <span><strong>5+ Years</strong> Historical Crime Data</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-purple-400 shrink-0" />
                    <span>Save ₹1,000 (17% Annual Discount)</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-purple-400 shrink-0" />
                    <span>Multi-Modal AI Correlation Suite</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-purple-400 shrink-0" />
                    <span>High-Priority GPU Queue Allocation</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Check className="h-4 w-4 text-purple-400 shrink-0" />
                    <span>Dedicated Intelligence Support Desk</span>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-white/10">
                <Link
                  href="/overview"
                  className="w-full inline-flex items-center justify-center py-3 rounded-full border border-purple-500/50 bg-purple-950/40 hover:bg-purple-900/50 text-white font-mono text-xs font-bold uppercase tracking-wider transition-all"
                >
                  Get Yearly Pro →
                </Link>
              </div>
            </div>
          </div>

          {/* Detailed Downside Comparison Table */}
          <div className="pt-4">
            <div className="rounded-3xl border border-white/10 bg-[#090812]/90 backdrop-blur-xl p-6 sm:p-8 space-y-5 shadow-2xl">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-4">
                <div>
                  <h3 className="text-xl font-mono font-black text-white uppercase tracking-tight">
                    Detailed Capability Comparison
                  </h3>
                  <p className="text-xs text-white/60 font-sans mt-1">
                    Side-by-side breakdown of features, data sources, and analytical limits.
                  </p>
                </div>
                <span className="text-xs font-mono text-[#df0095] bg-pink-950/40 border border-[#df0095]/30 px-3 py-1 rounded-full w-fit">
                  All Prices in INR (₹)
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs sm:text-sm">
                  <thead>
                    <tr className="border-b border-white/10 text-white font-mono text-xs uppercase tracking-wider">
                      <th className="py-3.5 px-4 font-bold w-[34%]">Capability</th>
                      <th className="py-3.5 px-4 font-bold text-center w-[20%] text-slate-300">🆓 Free</th>
                      <th className="py-3.5 px-4 font-bold text-center w-[23%] text-[#ff70db] bg-pink-950/20">
                        🚀 Monthly Pro
                      </th>
                      <th className="py-3.5 px-4 font-bold text-center w-[23%] text-purple-300">
                        👑 Yearly Pro
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 font-sans">
                    {[
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
                    ].map((row, rIdx) => (
                      <tr
                        key={rIdx}
                        className={rIdx % 2 === 1 ? "bg-white/[0.02]" : "bg-transparent"}
                      >
                        <td className="py-3 px-4 font-medium text-white/90">
                          {row.feature}
                        </td>
                        <td className="py-3 px-4 text-center font-mono text-white/60">
                          {row.free}
                        </td>
                        <td className="py-3 px-4 text-center font-mono font-bold text-[#ff70db] bg-pink-950/15">
                          {row.monthly}
                        </td>
                        <td className="py-3 px-4 text-center font-mono font-bold text-purple-300">
                          {row.yearly}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Enterprise Public Safety Deployment Tiers Header */}
          <div className="pt-8 border-t border-white/10 text-center max-w-2xl mx-auto space-y-2">
            <h3 className="text-xl font-mono font-black text-white uppercase tracking-tight">
              Enterprise &amp; Sovereign Deployment
            </h3>
            <p className="text-xs text-white/60 font-sans">
              For state police headquarters, state CID wings, and national defense intelligence agencies requiring dedicated on-premise air-gapped infrastructure.
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
