"use client";

import React, { useState } from "react";
import {
  Clock,
  Filter,
  FileText,
  PhoneCall,
  ShieldCheck,
  Bot,
  AlertTriangle,
  ChevronRight,
  RefreshCw,
  Search,
} from "lucide-react";
import { useInvestigation } from "@/context/InvestigationContext";

const EVENT_FILTERS = [
  { id: "ALL", label: "All Events" },
  { id: "CRIME_INCIDENT", label: "FIR Incidents" },
  { id: "CDR_COMMUNICATION", label: "CDR Calls" },
  { id: "INVESTIGATOR_DECISION", label: "Reviews" },
  { id: "AGENT_FINDING", label: "AI Findings" },
];

export default function InvestigationTimeline() {
  const {
    timelineEvents,
    loadingTimeline,
    setTimelineFilter,
    selectCrime,
    selectPhone,
    selectPerson,
  } = useInvestigation();

  const [activeFilter, setActiveFilter] = useState<string>("ALL");
  const [searchTerm, setSearchTerm] = useState<string>("");

  const handleFilterClick = (filterId: string) => {
    setActiveFilter(filterId);
    setTimelineFilter(filterId === "ALL" ? {} : { eventType: filterId });
  };

  const filteredEvents = timelineEvents.filter((evt) => {
    if (activeFilter !== "ALL" && evt.event_type !== activeFilter) return false;
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      return (
        evt.title.toLowerCase().includes(q) ||
        evt.description.toLowerCase().includes(q) ||
        (evt.citation && evt.citation.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const getEventIcon = (type: string) => {
    switch (type) {
      case "CRIME_INCIDENT":
        return <FileText className="h-3.5 w-3.5 text-purple-400" />;
      case "CDR_COMMUNICATION":
        return <PhoneCall className="h-3.5 w-3.5 text-cyan-400" />;
      case "INVESTIGATOR_DECISION":
        return <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />;
      case "AGENT_FINDING":
        return <Bot className="h-3.5 w-3.5 text-brand-accent" />;
      default:
        return <Clock className="h-3.5 w-3.5 text-white/50" />;
    }
  };

  const getStatusBadge = (status?: string | null) => {
    if (!status) return null;
    const st = status.toUpperCase();
    if (st === "VALIDATED") {
      return <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-[0.6rem] font-bold text-emerald-400">VALIDATED</span>;
    }
    if (st === "REJECTED") {
      return <span className="rounded bg-rose-500/20 px-1.5 py-0.5 text-[0.6rem] font-bold text-rose-400">REJECTED</span>;
    }
    return <span className="rounded bg-cyan-500/20 px-1.5 py-0.5 text-[0.6rem] font-bold text-cyan-400">AI-DERIVED</span>;
  };

  const handleEventClick = (evt: any) => {
    if (evt.entity_type === "Crime" && evt.entity_id) {
      selectCrime(evt.entity_name || evt.entity_id);
    } else if (evt.entity_type === "Phone" && evt.entity_id) {
      selectPhone(evt.entity_id);
    } else if (evt.entity_type === "Person" && evt.entity_id) {
      selectPerson(evt.entity_id);
    }
  };

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-midnight/80 p-4 backdrop-blur-xl shadow-2xl text-xs font-mono h-[420px]">
      {/* Header & Filter Ribbon */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-brand" />
          <h3 className="font-bold uppercase tracking-wider text-white">Investigation Timeline</h3>
          <span className="rounded-full bg-white/10 px-2 py-0.5 text-[0.65rem] text-white/60">
            {filteredEvents.length} events
          </span>
        </div>

        {/* Search input in timeline */}
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-white/40" />
          <input
            type="text"
            placeholder="Search timeline..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-44 rounded-lg border border-white/10 bg-black/40 pl-7 pr-2 py-1 text-[0.7rem] text-white placeholder-white/30 focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap gap-1.5 border-b border-white/5 pb-2">
        {EVENT_FILTERS.map((f) => (
          <button
            key={f.id}
            onClick={() => handleFilterClick(f.id)}
            className={`rounded-lg px-2.5 py-1 text-[0.68rem] transition ${
              activeFilter === f.id
                ? "bg-brand text-white font-bold"
                : "bg-white/[0.04] text-white/60 hover:bg-white/[0.08] hover:text-white"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Chronological Event Stream */}
      <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
        {loadingTimeline ? (
          <div className="flex h-32 items-center justify-center text-white/40">
            <RefreshCw className="h-4 w-4 animate-spin mr-2 text-brand" />
            Loading Chronological Sequence...
          </div>
        ) : filteredEvents.length > 0 ? (
          filteredEvents.map((evt, idx) => (
            <div
              key={evt.id || idx}
              onClick={() => handleEventClick(evt)}
              className="flex items-start gap-3 rounded-xl border border-white/5 bg-white/[0.02] p-2.5 hover:bg-white/[0.06] hover:border-brand/30 transition cursor-pointer group"
            >
              {/* Event Icon with Line */}
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-black/50 shadow-inner">
                {getEventIcon(evt.event_type)}
              </div>

              {/* Event Details */}
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center justify-between gap-1">
                  <span className="font-bold text-white group-hover:text-brand-accent transition">
                    {evt.title}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {getStatusBadge(evt.validation_status)}
                    <span className="text-[0.65rem] text-white/40">
                      {new Date(evt.timestamp).toLocaleString(undefined, {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </div>

                <p className="mt-1 text-[0.7rem] text-white/70 leading-relaxed line-clamp-2">
                  {evt.description}
                </p>

                {/* Source & Citation Footer */}
                <div className="mt-1.5 flex items-center gap-2 text-[0.62rem] text-white/40">
                  <span className="rounded bg-black/40 px-1 py-0.5">{evt.source}</span>
                  {evt.citation && (
                    <span className="font-bold text-brand-accent">[{evt.citation}]</span>
                  )}
                  {evt.entity_name && (
                    <span>• Focus: {evt.entity_name}</span>
                  )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="flex h-32 flex-col items-center justify-center text-center text-white/40">
            <Clock className="h-6 w-6 text-white/20 mb-1" />
            <p>No timeline records matching current filters.</p>
          </div>
        )}
      </div>
    </div>
  );
}
