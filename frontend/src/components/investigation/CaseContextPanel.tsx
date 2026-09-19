"use client";

import React from "react";
import {
  FileText,
  User,
  PhoneCall,
  Car,
  Crosshair,
  Share2,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  TrendingUp,
  Bot,
  MapPin,
  Calendar,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import { useInvestigation } from "@/context/InvestigationContext";

export default function CaseContextPanel() {
  const {
    caseContext,
    loadingCase,
    caseError,
    selectedPersonId,
    selectedPhoneId,
    selectPerson,
    selectPhone,
    selectCrime,
    runAgentInvestigation,
  } = useInvestigation();

  if (loadingCase) {
    return (
      <div className="flex h-full min-h-[480px] flex-col items-center justify-center rounded-2xl border border-white/10 bg-midnight/70 p-6 text-center backdrop-blur-xl">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand border-t-transparent mb-3" />
        <p className="text-xs font-mono text-white/50">Loading Case Context & Entities...</p>
      </div>
    );
  }

  if (caseError || !caseContext) {
    return (
      <div className="flex h-full min-h-[480px] flex-col items-center justify-center rounded-2xl border border-white/10 bg-midnight/70 p-6 text-center backdrop-blur-xl">
        <AlertCircle className="h-8 w-8 text-rose-400 mb-2" />
        <p className="text-xs font-mono text-white/70">{caseError || "No active case selected."}</p>
      </div>
    );
  }

  const {
    record_id,
    category,
    crime_type,
    location_name,
    occurred_at,
    description,
    extracted_people,
    extracted_phones,
    extracted_vehicles,
    connected_cases,
    key_individuals,
    validation_summary,
    total_evidence_count,
  } = caseContext;

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-white/10 bg-midnight/80 p-4 backdrop-blur-xl shadow-2xl overflow-y-auto max-h-[580px] text-xs font-mono">
      {/* Dossier Header */}
      <div className="flex items-start justify-between border-b border-white/10 pb-3">
        <div>
          <div className="flex items-center gap-1.5 text-[0.65rem] font-bold text-brand uppercase tracking-wider">
            <FileText className="h-3 w-3" />
            <span>FIR DOSSIER</span>
          </div>
          <h2 className="text-base font-black text-white font-mono mt-0.5">
            CASE {record_id}
          </h2>
          <div className="flex items-center gap-2 mt-1 text-[0.7rem] text-white/60">
            <span className="rounded bg-brand/20 px-1.5 py-0.5 font-bold text-brand-accent">
              {category}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <MapPin className="h-2.5 w-2.5 text-emerald-400" />
              {location_name}
            </span>
          </div>
        </div>

        {/* Validation Status Badge */}
        <div className="flex flex-col items-end">
          <div className="flex items-center gap-1 text-[0.65rem] font-bold text-emerald-400">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>{validation_summary.validated} VALIDATED</span>
          </div>
          <span className="text-[0.6rem] text-white/40">
            {validation_summary.under_review} pending review
          </span>
        </div>
      </div>

      {/* Incident Narrative Summary */}
      <div className="rounded-xl border border-white/5 bg-black/40 p-2.5 text-white/80 leading-relaxed text-[0.72rem]">
        <span className="font-bold text-white/40 block text-[0.65rem] uppercase mb-1">
          Police Report Excerpt
        </span>
        {description ? (
          <p>{description}</p>
        ) : (
          <p className="italic text-white/40">No FIR narrative statement attached.</p>
        )}
      </div>

      {/* Contextual AI Launch Trigger */}
      <button
        onClick={() => runAgentInvestigation(`Investigate Case ${record_id} and trace all connected cases and phone linkages.`)}
        className="flex items-center justify-between w-full rounded-xl border border-brand/30 bg-brand/10 px-3 py-2 text-[0.72rem] font-bold text-white hover:bg-brand/20 transition group"
      >
        <span className="flex items-center gap-2">
          <Bot className="h-3.5 w-3.5 text-brand" />
          <span>Ask AI about Case {record_id}</span>
        </span>
        <ChevronRight className="h-3.5 w-3.5 text-brand group-hover:translate-x-0.5 transition-transform" />
      </button>

      {/* Extracted People */}
      <div>
        <div className="flex items-center justify-between text-[0.65rem] font-bold text-white/40 uppercase mb-1.5">
          <span className="flex items-center gap-1">
            <User className="h-3 w-3 text-purple-400" />
            <span>Associated People ({extracted_people.length})</span>
          </span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {extracted_people.length > 0 ? (
            extracted_people.map((p) => {
              const isSelected = selectedPersonId === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => selectPerson(p.id)}
                  className={`inline-flex items-center gap-1.5 rounded-lg border px-2 py-1 text-[0.7rem] transition ${
                    isSelected
                      ? "border-purple-400 bg-purple-500/30 text-white font-bold"
                      : "border-white/10 bg-white/[0.04] text-white/80 hover:bg-white/[0.08]"
                  }`}
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-purple-400" />
                  <span>{p.label}</span>
                  <span className="text-[0.6rem] text-white/40">({p.role || "ASSOCIATED"})</span>
                </button>
              );
            })
          ) : (
            <span className="text-[0.7rem] italic text-white/40">No individuals extracted.</span>
          )}
        </div>
      </div>

      {/* Extracted Phones */}
      <div>
        <div className="flex items-center justify-between text-[0.65rem] font-bold text-white/40 uppercase mb-1.5">
          <span className="flex items-center gap-1">
            <PhoneCall className="h-3 w-3 text-cyan-400" />
            <span>Telecom Lines ({extracted_phones.length})</span>
          </span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {extracted_phones.length > 0 ? (
            extracted_phones.map((ph) => {
              const isSelected = selectedPhoneId === ph.id;
              return (
                <button
                  key={ph.id}
                  onClick={() => selectPhone(ph.id)}
                  className={`inline-flex items-center gap-1.5 rounded-lg border px-2 py-1 text-[0.7rem] transition ${
                    isSelected
                      ? "border-cyan-400 bg-cyan-500/30 text-white font-bold"
                      : "border-white/10 bg-white/[0.04] text-white/80 hover:bg-white/[0.08]"
                  }`}
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                  <span>{ph.label}</span>
                  <span className="text-[0.6rem] text-white/40">({ph.role || "PHONE"})</span>
                </button>
              );
            })
          ) : (
            <span className="text-[0.7rem] italic text-white/40">No phone numbers associated.</span>
          )}
        </div>
      </div>

      {/* Connected Incidents */}
      <div>
        <div className="flex items-center justify-between text-[0.65rem] font-bold text-white/40 uppercase mb-1.5">
          <span className="flex items-center gap-1">
            <Share2 className="h-3 w-3 text-brand-accent" />
            <span>Connected Incidents ({connected_cases.length})</span>
          </span>
        </div>
        <div className="flex flex-col gap-1.5">
          {connected_cases.length > 0 ? (
            connected_cases.map((cc) => (
              <button
                key={cc.crime_id}
                onClick={() => selectCrime(cc.record_id)}
                className="flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] p-2 text-left hover:bg-white/[0.06] transition"
              >
                <div>
                  <span className="font-bold text-white">Case {cc.record_id}</span>
                  <span className="block text-[0.65rem] text-white/50">{cc.location_name} • {cc.category}</span>
                </div>
                <span className="rounded bg-brand/10 border border-brand/30 px-1.5 py-0.5 text-[0.6rem] font-bold text-brand-accent">
                  {cc.connection_type}
                </span>
              </button>
            ))
          ) : (
            <span className="text-[0.7rem] italic text-white/40">No cross-case linkages detected yet.</span>
          )}
        </div>
      </div>

      {/* Structural Centrality Summary */}
      {key_individuals.length > 0 && (
        <div className="border-t border-white/10 pt-3">
          <div className="flex items-center gap-1 text-[0.65rem] font-bold text-white/40 uppercase mb-1.5">
            <TrendingUp className="h-3 w-3 text-amber-400" />
            <span>Structurally Central Individuals</span>
          </div>
          <div className="flex flex-col gap-1.5">
            {key_individuals.slice(0, 3).map((ki) => (
              <div
                key={ki.person_id}
                className="flex items-center justify-between rounded-lg border border-white/5 bg-black/40 p-2"
              >
                <div>
                  <span className="font-bold text-white">{ki.name}</span>
                  <span className="block text-[0.6rem] text-white/40">
                    Deg: {ki.degree_centrality.toFixed(2)} • Bet: {ki.betweenness_centrality.toFixed(2)}
                  </span>
                </div>
                <span className="rounded bg-amber-500/10 border border-amber-500/30 px-1.5 py-0.5 text-[0.6rem] font-bold text-amber-400">
                  Top Centrality
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evidence Footprint */}
      <div className="flex items-center justify-between border-t border-white/10 pt-2 text-[0.68rem] text-white/50">
        <span>TOTAL CORROBORATING EVIDENCE:</span>
        <span className="font-bold text-brand-accent">{total_evidence_count} items</span>
      </div>
    </div>
  );
}
