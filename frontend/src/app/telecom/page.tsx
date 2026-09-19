"use client";

import React, { useState, useEffect } from "react";
import {
  PhoneCall,
  Search,
  UploadCloud,
  FileText,
  Clock,
  User,
  ShieldAlert,
  ArrowUpRight,
  ArrowDownLeft,
  Layers,
  Activity,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  RefreshCw,
  TrendingUp,
  MapPin,
  ChevronRight,
  Network
} from "lucide-react";
import InteractiveGraph from "@/components/investigation/InteractiveGraph";
import { GraphNode, GraphEdge } from "@/types/investigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PhoneProfile {
  id: string;
  normalized_number: string;
  country_code: string;
  national_number: string;
  number_type: string;
  carrier?: string;
  created_at?: string;
  metrics: {
    total_calls: number;
    outbound_calls: number;
    inbound_calls: number;
    total_duration_seconds: number;
    outbound_duration_seconds: number;
    inbound_duration_seconds: number;
    unique_contacts_count: number;
    first_activity?: string;
    last_activity?: string;
    hourly_distribution: Record<string, number>;
  };
  associated_crimes: Array<{
    crime_id: string;
    record_id: string;
    category: string;
    crime_type: string;
    location_name: string;
    occurred_at?: string;
    relationship_type: string;
    confidence: number;
    confidence_type: string;
    source_text?: string;
  }>;
  associated_persons: Array<{
    person_name: string;
    role: string;
    confidence: number;
    confidence_type: string;
    source?: string;
  }>;
  top_contacts: Array<{
    phone_id: string;
    normalized_number: string;
    call_count: number;
    total_duration: number;
  }>;
}

interface CrossCaseLink {
  connection_type: string;
  crime_1: { id: string; record_id: string; category: string; location_name: string };
  crime_2: { id: string; record_id: string; category: string; location_name: string };
  shared_phone?: string;
  phone_1?: string;
  phone_2?: string;
  call_count?: number;
  evidence: string;
  confidence: number;
  confidence_type: string;
}

interface CdrItem {
  id: string;
  caller_number?: string;
  callee_number?: string;
  call_timestamp: string;
  duration_seconds: number;
  call_type: string;
  location_or_tower?: string;
}

export default function TelecomPage() {
  const [activeTab, setActiveTab] = useState<"search" | "cross_case" | "cdrs" | "import">("search");
  const [searchQuery, setSearchQuery] = useState<string>("9876543210");
  const [profile, setProfile] = useState<PhoneProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Cross-case linkages state
  const [crossCaseLinks, setCrossCaseLinks] = useState<CrossCaseLink[]>([]);
  const [loadingCrossCase, setLoadingCrossCase] = useState<boolean>(false);

  // Raw CDRs state
  const [cdrs, setCdrs] = useState<CdrItem[]>([]);
  const [loadingCdrs, setLoadingCdrs] = useState<boolean>(false);

  // Graph state for current phone
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);

  // Ingestion state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [dryRun, setDryRun] = useState<boolean>(true);
  const [importLoading, setImportLoading] = useState<boolean>(false);
  const [importResult, setImportResult] = useState<any>(null);

  const fetchPhoneProfile = async (query: string) => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/telecom/phones/${encodeURIComponent(query.trim())}`);
      if (!res.ok) {
        throw new Error(res.status === 404 ? `No record found for phone "${query}".` : `Failed to load profile (${res.status})`);
      }
      const data = await res.json();
      setProfile(data);

      // Also fetch communication neighborhood
      fetchGraphNeighborhood(data.normalized_number);
    } catch (err: any) {
      setError(err.message || "Error fetching telecom record.");
      setProfile(null);
      setGraphNodes([]);
      setGraphEdges([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchGraphNeighborhood = async (phoneNum: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/telecom/phones/${encodeURIComponent(phoneNum)}/neighborhood?depth=2&max_nodes=40`);
      if (res.ok) {
        const data = await res.json();
        setGraphNodes(data.nodes || []);
        setGraphEdges(data.edges || []);
      }
    } catch (e) {
      console.warn("Could not load telecom graph neighborhood:", e);
    }
  };

  const fetchCrossCase = async () => {
    setLoadingCrossCase(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/telecom/cross-case?limit=50`);
      if (res.ok) {
        const data = await res.json();
        setCrossCaseLinks(data);
      }
    } catch (e) {
      console.error("Error loading cross-case telecom links:", e);
    } finally {
      setLoadingCrossCase(false);
    }
  };

  const fetchCdrs = async () => {
    setLoadingCdrs(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/telecom/cdr?page=1&page_size=30`);
      if (res.ok) {
        const data = await res.json();
        setCdrs(data.items || []);
      }
    } catch (e) {
      console.error("Error loading CDRs:", e);
    } finally {
      setLoadingCdrs(false);
    }
  };

  const handleImportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setImportLoading(true);
    setImportResult(null);

    const formData = new FormData();
    formData.append("file", uploadFile);

    try {
      const res = await fetch(`${API_BASE}/api/v1/telecom/cdr/import?dry_run=${dryRun}`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setImportResult(data);
      if (!dryRun && res.ok) {
        fetchCdrs();
        fetchCrossCase();
      }
    } catch (err: any) {
      setImportResult({ message: `Upload failed: ${err.message}` });
    } finally {
      setImportLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "cross_case") fetchCrossCase();
    if (activeTab === "cdrs") fetchCdrs();
  }, [activeTab]);

  return (
    <div className="min-h-screen bg-midnight text-white pb-20">
      {/* Top Banner */}
      <div className="border-b border-white/10 bg-gradient-to-r from-emerald-950/40 via-midnight to-blue-950/30 px-6 py-8 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-[0.7rem] font-black uppercase tracking-wider text-emerald-400">
                <PhoneCall className="h-3.5 w-3.5" />
                Telecommunications Intelligence
              </div>
              <h1 className="mt-2 text-3xl font-black tracking-tight text-white font-mono sm:text-4xl">
                CDR & PHONE <span className="text-brand">ANALYSIS</span>
              </h1>
              <p className="mt-1 text-sm text-white/60">
                Cross-case criminal discovery through phone records, CDR call frequency, and communication graphs.
              </p>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 p-1 text-xs">
              <button
                onClick={() => setActiveTab("search")}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-bold transition-colors ${
                  activeTab === "search" ? "bg-brand text-midnight" : "text-white/70 hover:text-white"
                }`}
              >
                <Search className="h-3.5 w-3.5" />
                Phone Lookup
              </button>
              <button
                onClick={() => setActiveTab("cross_case")}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-bold transition-colors ${
                  activeTab === "cross_case" ? "bg-brand text-midnight" : "text-white/70 hover:text-white"
                }`}
              >
                <Network className="h-3.5 w-3.5" />
                Cross-Case Linkages
              </button>
              <button
                onClick={() => setActiveTab("cdrs")}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-bold transition-colors ${
                  activeTab === "cdrs" ? "bg-brand text-midnight" : "text-white/70 hover:text-white"
                }`}
              >
                <FileText className="h-3.5 w-3.5" />
                Call Logs
              </button>
              <button
                onClick={() => setActiveTab("import")}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-bold transition-colors ${
                  activeTab === "import" ? "bg-brand text-midnight" : "text-white/70 hover:text-white"
                }`}
              >
                <UploadCloud className="h-3.5 w-3.5" />
                CDR Ingestion
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-6 py-8 lg:px-12">
        {/* Tab 1: Phone Search & Investigation */}
        {activeTab === "search" && (
          <div className="flex flex-col gap-8">
            {/* Search Box */}
            <div className="rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
              <label className="text-xs font-bold uppercase tracking-wider text-white/50">
                Search Target Phone Number
              </label>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  fetchPhoneProfile(searchQuery);
                }}
                className="mt-2 flex flex-col gap-3 sm:flex-row"
              >
                <div className="relative flex-1">
                  <PhoneCall className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-white/40" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Enter phone number (e.g. +91 9876543210 or 9876543210)..."
                    className="w-full rounded-lg border border-white/15 bg-midnight/90 py-3 pl-12 pr-4 text-sm text-white placeholder-white/40 focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand font-mono"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-metallic inline-flex items-center justify-center gap-2 rounded-lg px-6 py-3 text-xs font-black uppercase tracking-wider"
                >
                  {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                  Investigate Phone
                </button>
              </form>
              <div className="mt-2 text-[0.7rem] text-white/40">
                Supports formatting variants: +91 9876543210, 919876543210, 09876543210, and international E.164 numbers.
              </div>
            </div>

            {/* Error state */}
            {error && (
              <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                {error}
              </div>
            )}

            {/* Profile Display */}
            {profile && (
              <div className="flex flex-col gap-8">
                {/* Header Profile & Metric Cards */}
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="rounded-xl border border-white/10 bg-white/5 p-5">
                    <div className="text-[0.7rem] font-bold uppercase tracking-wider text-white/50">Normalized Identity</div>
                    <div className="mt-2 text-2xl font-black text-brand font-mono">{profile.normalized_number}</div>
                    <div className="mt-1 text-[0.7rem] text-white/40">
                      Type: <span className="font-semibold text-white/80">{profile.number_type}</span> · Region: +{profile.country_code}
                    </div>
                  </div>

                  <div className="rounded-xl border border-white/10 bg-white/5 p-5">
                    <div className="text-[0.7rem] font-bold uppercase tracking-wider text-white/50">Total Call Activity</div>
                    <div className="mt-2 text-2xl font-black text-white font-mono">{profile.metrics.total_calls} Calls</div>
                    <div className="mt-1 text-[0.7rem] text-white/40">
                      <span className="text-emerald-400">{profile.metrics.outbound_calls} Outbound</span> ·{" "}
                      <span className="text-blue-400">{profile.metrics.inbound_calls} Inbound</span>
                    </div>
                  </div>

                  <div className="rounded-xl border border-white/10 bg-white/5 p-5">
                    <div className="text-[0.7rem] font-bold uppercase tracking-wider text-white/50">Cumulative Airtime</div>
                    <div className="mt-2 text-2xl font-black text-white font-mono">
                      {Math.round(profile.metrics.total_duration_seconds / 60)} Mins
                    </div>
                    <div className="mt-1 text-[0.7rem] text-white/40">
                      {profile.metrics.unique_contacts_count} Unique Interlocutors
                    </div>
                  </div>

                  <div className="rounded-xl border border-white/10 bg-white/5 p-5">
                    <div className="text-[0.7rem] font-bold uppercase tracking-wider text-white/50">Linked Crime Cases</div>
                    <div className="mt-2 text-2xl font-black text-amber-400 font-mono">
                      {profile.associated_crimes.length} Incidents
                    </div>
                    <div className="mt-1 text-[0.7rem] text-white/40">
                      {profile.associated_persons.length} Connected Person(s)
                    </div>
                  </div>
                </div>

                {/* Main 2-Column Section */}
                <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
                  {/* Associated Crimes Card */}
                  <div className="rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
                    <div className="flex items-center justify-between border-b border-white/10 pb-3">
                      <div className="flex items-center gap-2">
                        <ShieldAlert className="h-4 w-4 text-amber-400" />
                        <h3 className="text-sm font-black uppercase tracking-wider font-mono text-white">
                          Associated Incident Reports ({profile.associated_crimes.length})
                        </h3>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-col gap-3">
                      {profile.associated_crimes.length === 0 ? (
                        <div className="py-8 text-center text-xs text-white/40">
                          No direct police crime reports mention this telephone number.
                        </div>
                      ) : (
                        profile.associated_crimes.map((c, i) => (
                          <div key={i} className="rounded-lg border border-white/10 bg-midnight/60 p-4">
                            <div className="flex items-center justify-between">
                              <span className="font-mono text-xs font-bold text-brand">{c.record_id}</span>
                              <span className="rounded bg-amber-500/10 px-2 py-0.5 text-[0.65rem] font-bold text-amber-400 uppercase">
                                {c.relationship_type.replace(/_/g, " ")}
                              </span>
                            </div>
                            <div className="mt-1 text-xs font-medium text-white">{c.crime_type} · {c.location_name}</div>
                            {c.source_text && (
                              <div className="mt-2 rounded bg-black/30 p-2 text-[0.7rem] italic text-white/70 border-l-2 border-brand">
                                "{c.source_text}"
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Top Frequent Contacts Card */}
                  <div className="rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
                    <div className="flex items-center justify-between border-b border-white/10 pb-3">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-emerald-400" />
                        <h3 className="text-sm font-black uppercase tracking-wider font-mono text-white">
                          Top Frequent Contacts ({profile.top_contacts.length})
                        </h3>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-col gap-2">
                      {profile.top_contacts.length === 0 ? (
                        <div className="py-8 text-center text-xs text-white/40">
                          No CDR communication records registered for this number.
                        </div>
                      ) : (
                        profile.top_contacts.map((contact, i) => (
                          <div
                            key={i}
                            onClick={() => {
                              setSearchQuery(contact.normalized_number);
                              fetchPhoneProfile(contact.normalized_number);
                            }}
                            className="flex cursor-pointer items-center justify-between rounded-lg border border-white/5 bg-midnight/60 p-3 hover:border-brand/40 transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              <div className="flex h-8 w-8 items-center justify-center rounded bg-white/5 text-xs font-mono font-bold text-white/70">
                                #{i + 1}
                              </div>
                              <div>
                                <div className="font-mono text-xs font-bold text-white hover:text-brand">
                                  {contact.normalized_number}
                                </div>
                                <div className="text-[0.65rem] text-white/40">
                                  {Math.round(contact.total_duration / 60)} mins cumulative airtime
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="rounded bg-emerald-500/10 px-2 py-1 text-[0.65rem] font-bold text-emerald-400 font-mono">
                                {contact.call_count} calls
                              </span>
                              <ChevronRight className="h-4 w-4 text-white/30" />
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>

                {/* Visual Communication Subgraph */}
                {graphNodes.length > 0 && (
                  <div className="rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-md">
                    <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
                      <div className="flex items-center gap-2">
                        <Network className="h-4 w-4 text-brand" />
                        <h3 className="text-sm font-black uppercase tracking-wider font-mono text-white">
                          Communication Network Subgraph (2-Hop Traversal)
                        </h3>
                      </div>
                      <div className="text-xs text-white/50">
                        {graphNodes.length} Nodes · {graphEdges.length} Relationships
                      </div>
                    </div>
                    <div className="h-[450px] w-full rounded-lg overflow-hidden border border-white/10 bg-midnight">
                      <InteractiveGraph
                        nodes={graphNodes}
                        edges={graphEdges}
                        selectedNodeId={null}
                        selectedEdge={null}
                        onSelectNode={() => {}}
                        onSelectEdge={() => {}}
                      />
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Cross-Case Linkages */}
        {activeTab === "cross_case" && (
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-black font-mono uppercase tracking-wider text-white">
                  Cross-Case Telecommunication Linkages
                </h2>
                <p className="text-xs text-white/60">
                  Criminal cases automatically linked through shared phone numbers or CDR call exchanges.
                </p>
              </div>
              <button
                onClick={fetchCrossCase}
                disabled={loadingCrossCase}
                className="btn-metallic inline-flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-bold"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loadingCrossCase ? "animate-spin" : ""}`} />
                Refresh
              </button>
            </div>

            {loadingCrossCase ? (
              <div className="py-16 text-center text-xs text-white/40">Analyzing cross-case linkages...</div>
            ) : crossCaseLinks.length === 0 ? (
              <div className="rounded-xl border border-white/10 bg-white/5 py-16 text-center text-xs text-white/40">
                No cross-case telecommunication connections detected yet. Import CDR records to establish communication links.
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                {crossCaseLinks.map((link, idx) => (
                  <div key={idx} className="rounded-xl border border-white/10 bg-white/5 p-5 backdrop-blur-md">
                    <div className="flex items-center justify-between">
                      <span className="rounded bg-brand/10 px-2 py-0.5 text-[0.65rem] font-black uppercase tracking-wider text-brand">
                        {link.connection_type.replace(/_/g, " ")}
                      </span>
                      <span className="text-[0.7rem] font-bold text-emerald-400">
                        {Math.round(link.confidence * 100)}% Confidence
                      </span>
                    </div>

                    <div className="mt-4 flex items-center justify-between gap-2 rounded-lg bg-midnight/70 p-3 border border-white/5">
                      <div className="flex flex-col">
                        <span className="font-mono text-xs font-bold text-white">{link.crime_1.record_id}</span>
                        <span className="text-[0.7rem] text-white/50">{link.crime_1.category} · {link.crime_1.location_name}</span>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-brand font-mono">
                        <span>←→</span>
                      </div>
                      <div className="flex flex-col text-right">
                        <span className="font-mono text-xs font-bold text-white">{link.crime_2.record_id}</span>
                        <span className="text-[0.7rem] text-white/50">{link.crime_2.category} · {link.crime_2.location_name}</span>
                      </div>
                    </div>

                    <div className="mt-3 text-xs text-white/80 leading-relaxed">
                      {link.evidence}
                    </div>

                    <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between text-[0.7rem] text-white/40">
                      <span>Source: Telecommunications Fusion</span>
                      <span className="uppercase font-bold text-white/60">{link.confidence_type}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Raw CDR Call Logs */}
        {activeTab === "cdrs" && (
          <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-black font-mono uppercase tracking-wider text-white">
                  Call Detail Records (CDR) Registry
                </h2>
                <p className="text-xs text-white/60">
                  Audited telecommunication event records with deterministic SHA-256 deduplication.
                </p>
              </div>
              <button
                onClick={fetchCdrs}
                disabled={loadingCdrs}
                className="btn-metallic inline-flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-bold"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loadingCdrs ? "animate-spin" : ""}`} />
                Refresh Logs
              </button>
            </div>

            {loadingCdrs ? (
              <div className="py-16 text-center text-xs text-white/40">Loading CDR logs...</div>
            ) : cdrs.length === 0 ? (
              <div className="rounded-xl border border-white/10 bg-white/5 py-16 text-center text-xs text-white/40">
                No CDR records available. Ingest a CDR CSV or JSON file to populate records.
              </div>
            ) : (
              <div className="overflow-hidden rounded-xl border border-white/10 bg-white/5">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-white/10 bg-white/5 text-[0.65rem] font-black uppercase tracking-wider text-white/50">
                    <tr>
                      <th className="p-3">Timestamp</th>
                      <th className="p-3">Caller</th>
                      <th className="p-3">Callee</th>
                      <th className="p-3">Duration</th>
                      <th className="p-3">Type</th>
                      <th className="p-3">Tower Location</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 font-mono">
                    {cdrs.map((c) => (
                      <tr key={c.id} className="hover:bg-white/5 transition-colors">
                        <td className="p-3 text-white/70">
                          {new Date(c.call_timestamp).toLocaleString()}
                        </td>
                        <td className="p-3 font-bold text-emerald-400">{c.caller_number || "N/A"}</td>
                        <td className="p-3 font-bold text-blue-400">{c.callee_number || "N/A"}</td>
                        <td className="p-3 text-white/80">{c.duration_seconds}s</td>
                        <td className="p-3">
                          <span className="rounded bg-white/10 px-1.5 py-0.5 text-[0.65rem] uppercase">
                            {c.call_type}
                          </span>
                        </td>
                        <td className="p-3 text-white/60 font-sans">{c.location_or_tower || "Unknown"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Ingestion Dropzone */}
        {activeTab === "import" && (
          <div className="mx-auto max-w-2xl">
            <div className="rounded-xl border border-white/10 bg-white/5 p-8 backdrop-blur-md">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand/10 text-brand">
                  <UploadCloud className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-lg font-black font-mono uppercase tracking-wider text-white">
                    Ingest Call Detail Records (CDR)
                  </h2>
                  <p className="text-xs text-white/60">
                    Upload CSV or JSON CDR batch files with automated phone normalization.
                  </p>
                </div>
              </div>

              <form onSubmit={handleImportSubmit} className="mt-6 flex flex-col gap-6">
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-bold uppercase text-white/70">Choose File (.csv or .json)</label>
                  <input
                    type="file"
                    accept=".csv,.json"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="block w-full cursor-pointer rounded-lg border border-white/15 bg-midnight p-3 text-xs text-white/80 file:mr-4 file:rounded file:border-0 file:bg-brand file:px-3 file:py-1.5 file:text-xs file:font-black file:uppercase file:text-midnight hover:file:bg-brand/80"
                  />
                </div>

                <div className="flex items-center justify-between rounded-lg bg-midnight/60 p-4 border border-white/10">
                  <div>
                    <div className="text-xs font-bold text-white">Dry Run Simulation</div>
                    <div className="text-[0.7rem] text-white/40">
                      Validate schema and normalize numbers without writing to database
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={dryRun}
                    onChange={(e) => setDryRun(e.target.checked)}
                    className="h-4 w-4 rounded border-white/20 bg-midnight accent-brand"
                  />
                </div>

                <button
                  type="submit"
                  disabled={importLoading || !uploadFile}
                  className="btn-metallic inline-flex items-center justify-center gap-2 rounded-lg py-3 text-xs font-black uppercase tracking-wider disabled:opacity-50"
                >
                  {importLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <UploadCloud className="h-4 w-4" />}
                  {dryRun ? "Execute Dry-Run Preview" : "Commit Ingestion to Database"}
                </button>
              </form>

              {/* Ingestion Response Output */}
              {importResult && (
                <div className="mt-6 rounded-lg border border-white/10 bg-midnight p-4 text-xs font-mono">
                  <div className="flex items-center gap-2 font-bold text-brand">
                    <CheckCircle2 className="h-4 w-4" />
                    {importResult.message}
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-2 text-[0.7rem] text-white/70">
                    <div>Total: {importResult.total_rows}</div>
                    <div className="text-emerald-400">Valid: {importResult.valid_count}</div>
                    <div className="text-rose-400">Rejected: {importResult.rejected_count}</div>
                  </div>
                  {importResult.rejections && importResult.rejections.length > 0 && (
                    <div className="mt-4 max-h-40 overflow-y-auto rounded bg-black/40 p-2 text-[0.65rem] text-rose-300">
                      <div className="font-bold mb-1">Rejection Details:</div>
                      {importResult.rejections.map((r: any, i: number) => (
                        <div key={i}>
                          Row {r.row_number}: [{r.error_category}] {r.error_message}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
