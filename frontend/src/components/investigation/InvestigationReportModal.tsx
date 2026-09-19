"use client";

import React from "react";
import {
  FileText,
  Printer,
  Download,
  X,
  ShieldCheck,
  AlertTriangle,
  Scale,
  MapPin,
  Clock,
  Share2,
  Users,
  PhoneCall,
  CheckCircle2,
} from "lucide-react";
import { useInvestigation } from "@/context/InvestigationContext";

export default function InvestigationReportModal() {
  const { isReportModalOpen, closeReportModal, activeReport } = useInvestigation();

  if (!isReportModalOpen || !activeReport) return null;

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadMarkdown = () => {
    const md = `
# ${activeReport.title}
*Generated at: ${activeReport.generated_at}*
*Investigator Unit: ${activeReport.scope.investigator_unit || "Special Investigation Unit"}*

---

## 1. INVESTIGATION SCOPE
- **Case ID**: ${activeReport.record_id}
- **Category**: ${activeReport.scope.category}
- **Jurisdiction**: ${activeReport.scope.jurisdiction}
- **Date Reported**: ${activeReport.scope.date_reported}
- **Reporting Source**: ${activeReport.scope.reporting_source}

## 2. EXECUTIVE SUMMARY
${activeReport.executive_summary}

## 3. CONNECTED CASES
${activeReport.connected_cases.map(c => `- Case ${c.record_id} (${c.category}): ${c.evidence} [${c.connection_type}]`).join("\n")}

## 4. PEOPLE & STRUCTURAL CENTRALITY
*Zero Guilt Notice: Centrality metrics strictly quantify structural graph connectivity within observed data and do not infer criminal culpability.*
${activeReport.people_findings.map(p => `- **${p.name}**: Degree=${p.centrality_metrics?.degree}, Betweenness=${p.centrality_metrics?.betweenness}, PageRank=${p.centrality_metrics?.pagerank}. ${p.structural_role}`).join("\n")}

## 5. TELECOMMUNICATIONS INTELLIGENCE
${activeReport.telecom_findings.map(t => `- Phone ${t.normalized_number}: ${t.relationship} [${t.validation_status}] Citation: ${t.citation}`).join("\n")}

## 6. TIMELINE OF EVENTS
${activeReport.timeline.map(t => `- ${t.timestamp}: [${t.event_type}] ${t.title} - ${t.description}`).join("\n")}

## 7. CORROBORATING EVIDENCE INVENTORY
${activeReport.evidence_inventory.map(e => `- [${e.citation}] ${e.evidence_type} (${e.validation_status}): ${e.summary}`).join("\n")}

## 8. STATUTORY LIMITATIONS & LEGAL MANDATE
${activeReport.statutory_limitations.map(l => `- ${l}`).join("\n")}
    `.trim();

    const blob = new Blob([md], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Investigation_Report_${activeReport.record_id}.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-2xl border border-white/10 bg-midnight p-6 shadow-2xl font-mono text-xs text-white/90">
        {/* Top Control Bar */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4 sticky top-0 bg-midnight z-10">
          <div className="flex items-center gap-2 text-brand">
            <FileText className="h-5 w-5" />
            <span className="font-bold uppercase tracking-wider text-sm text-white">
              Official Investigation Dossier
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white/80 hover:bg-white/10 hover:text-white transition"
            >
              <Printer className="h-3.5 w-3.5" />
              <span>Print</span>
            </button>
            <button
              onClick={handleDownloadMarkdown}
              className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white/80 hover:bg-white/10 hover:text-white transition"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Export MD</span>
            </button>
            <button
              onClick={closeReportModal}
              className="rounded-lg p-1.5 text-white/50 hover:bg-white/10 hover:text-white transition"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Report Content */}
        <div className="space-y-6 pt-4 leading-relaxed">
          {/* Header Banner */}
          <div className="rounded-xl border border-brand/20 bg-brand/5 p-4">
            <div className="flex items-center justify-between">
              <span className="text-[0.65rem] font-bold text-brand uppercase tracking-[0.2em]">
                CONNECTDOTS CRIMINAL NETWORK ANALYSIS REPORT
              </span>
              <span className="text-[0.65rem] text-white/40">
                DATE: {new Date(activeReport.generated_at).toLocaleString()}
              </span>
            </div>
            <h1 className="text-lg font-black uppercase text-white mt-1">
              {activeReport.title}
            </h1>
            <div className="flex flex-wrap gap-4 mt-2 text-[0.7rem] text-white/70">
              <div><strong className="text-white/40">TARGET CASE:</strong> {activeReport.record_id}</div>
              <div><strong className="text-white/40">JURISDICTION:</strong> {activeReport.scope.jurisdiction}</div>
              <div><strong className="text-white/40">INVESTIGATOR:</strong> {activeReport.scope.investigator_unit}</div>
            </div>
          </div>

          {/* Section 1: Executive Summary */}
          <div>
            <h2 className="text-xs font-black text-brand uppercase tracking-wider mb-1.5 border-b border-white/10 pb-1">
              1. Executive Summary
            </h2>
            <p className="text-white/80 text-[0.75rem]">{activeReport.executive_summary}</p>
          </div>

          {/* Section 2: Connected Cases */}
          <div>
            <h2 className="text-xs font-black text-brand uppercase tracking-wider mb-1.5 border-b border-white/10 pb-1">
              2. Correlated Incidents & Linkages
            </h2>
            {activeReport.connected_cases.length > 0 ? (
              <div className="space-y-2">
                {activeReport.connected_cases.map((c) => (
                  <div key={c.crime_id} className="rounded-lg border border-white/5 bg-black/40 p-2.5 flex items-start justify-between">
                    <div>
                      <span className="font-bold text-white">Case {c.record_id} ({c.category})</span>
                      <p className="text-[0.7rem] text-white/60 mt-0.5">{c.evidence}</p>
                    </div>
                    <span className="rounded bg-brand/20 px-2 py-0.5 text-[0.65rem] font-bold text-brand-accent">
                      {c.connection_type}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="italic text-white/40">No cross-case linkages detected.</p>
            )}
          </div>

          {/* Section 3: People & Structural Centrality */}
          <div>
            <h2 className="text-xs font-black text-brand uppercase tracking-wider mb-1.5 border-b border-white/10 pb-1">
              3. Structural Centrality Analysis
            </h2>
            <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-2 text-[0.68rem] text-amber-300 mb-2">
              <Scale className="h-3.5 w-3.5 inline mr-1" />
              <strong>Neutral Centrality Principle:</strong> Metrics quantify topological network connectivity only within observed records. Centrality is not an inference of legal culpability.
            </div>
            <div className="space-y-2">
              {activeReport.people_findings.map((p, idx) => (
                <div key={idx} className="rounded-lg border border-white/5 bg-black/40 p-2.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">{p.name}</span>
                    <div className="flex gap-2 text-[0.65rem] text-brand-accent">
                      <span>Deg: {p.centrality_metrics?.degree?.toFixed(2)}</span>
                      <span>Bet: {p.centrality_metrics?.betweenness?.toFixed(2)}</span>
                      <span>PR: {p.centrality_metrics?.pagerank?.toFixed(2)}</span>
                    </div>
                  </div>
                  <p className="text-[0.7rem] text-white/60 mt-1">{p.structural_role}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Section 4: Telecommunications & CDR */}
          <div>
            <h2 className="text-xs font-black text-brand uppercase tracking-wider mb-1.5 border-b border-white/10 pb-1">
              4. Telecommunications & CDR Intelligence
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {activeReport.telecom_findings.map((t, idx) => (
                <div key={idx} className="rounded-lg border border-white/5 bg-black/40 p-2 text-[0.7rem]">
                  <span className="font-bold text-cyan-400">{t.normalized_number}</span>
                  <div className="text-white/50 text-[0.65rem] mt-0.5">
                    <span>Role: {t.relationship}</span> • <span>[{t.citation}]</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section 5: Timeline */}
          <div>
            <h2 className="text-xs font-black text-brand uppercase tracking-wider mb-1.5 border-b border-white/10 pb-1">
              5. Chronological Incident Sequence
            </h2>
            <div className="space-y-1.5">
              {activeReport.timeline.map((evt, idx) => (
                <div key={idx} className="flex items-center justify-between rounded border border-white/5 bg-black/30 p-1.5 text-[0.68rem]">
                  <span>{new Date(evt.timestamp).toLocaleString()}</span>
                  <span className="font-bold text-white/90">{evt.title}</span>
                  <span className="text-white/40">{evt.source}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Section 6: Statutory Limitations */}
          <div className="rounded-xl border border-white/10 bg-black/60 p-4 space-y-2">
            <h2 className="text-xs font-black text-rose-400 uppercase tracking-wider">
              Statutory Limitations & Human Oversight Mandate
            </h2>
            {activeReport.statutory_limitations.map((lim, idx) => (
              <p key={idx} className="text-[0.68rem] text-white/70 leading-relaxed">
                • {lim}
              </p>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
