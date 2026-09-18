"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import {
  UploadCloud,
  FileCheck,
  AlertOctagon,
  CheckCircle2,
  RefreshCw,
  ArrowRight,
  Database,
  FileText,
  HelpCircle,
} from "lucide-react";
import { importCrimeFile } from "@/lib/api";
import { ImportResultResponse } from "@/types/crime";

export default function ImportPipelinePage() {
  const [file, setFile] = useState<File | null>(null);
  const [rawPreview, setRawPreview] = useState<string[][]>([]);
  const [validating, setValidating] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [validationResult, setValidationResult] = useState<ImportResultResponse | null>(null);
  const [commitResult, setCommitResult] = useState<ImportResultResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;

    setFile(selected);
    setValidationResult(null);
    setCommitResult(null);
    setError(null);

    // Read first few lines for raw preview
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      if (selected.name.endsWith(".csv")) {
        const lines = text.split("\n").filter((l) => l.trim().length > 0).slice(0, 6);
        const rows = lines.map((l) => l.split(","));
        setRawPreview(rows);
      } else if (selected.name.endsWith(".json")) {
        try {
          const parsed = JSON.parse(text);
          const sample = Array.isArray(parsed) ? parsed.slice(0, 5) : [parsed];
          const keys = sample.length > 0 ? Object.keys(sample[0]) : [];
          const rows = [keys, ...sample.map((obj) => keys.map((k) => String(obj[k] ?? "")))];
          setRawPreview(rows);
        } catch (e) {
          setRawPreview([]);
        }
      }
    };
    reader.readAsText(selected);
  };

  const handleValidate = async () => {
    if (!file) return;
    setValidating(true);
    setError(null);
    try {
      // Step 3: Run dry-run validation without DB insert
      const result = await importCrimeFile(file, true);
      setValidationResult(result);
    } catch (err: any) {
      setError(err.message || "Failed to run validation pipeline.");
    } finally {
      setValidating(false);
    }
  };

  const handleCommit = async () => {
    if (!file) return;
    setCommitting(true);
    setError(null);
    try {
      // Step 4: Commit valid records into PostgreSQL/PostGIS
      const result = await importCrimeFile(file, false);
      setCommitResult(result);
    } catch (err: any) {
      setError(err.message || "Failed to commit valid records.");
    } finally {
      setCommitting(false);
    }
  };

  const resetAll = () => {
    setFile(null);
    setRawPreview([]);
    setValidationResult(null);
    setCommitResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-white/10 pb-6">
        <span className="text-[0.7rem] font-bold tracking-[0.3em] uppercase text-brand">
          Ingestion & Quality Control
        </span>
        <h1 className="mt-1 text-3xl font-black uppercase tracking-tight text-white font-mono">
          Data Ingestion Pipeline
        </h1>
        <p className="mt-1 text-sm text-white/60">
          Upload raw crime datasets (CSV/JSON), inspect parsed rows, run pre-commit validation, and review rejection diagnostics.
        </p>
      </div>

      {error && (
        <div className="rounded-xs border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300">
          <div className="flex items-center gap-2 font-bold uppercase tracking-wider">
            <AlertOctagon className="h-4 w-4" /> Ingestion Notice
          </div>
          <p className="mt-1">{error}</p>
        </div>
      )}

      {/* Success Commitment Banner */}
      {commitResult && (
        <div className="glass-panel border-emerald-500/40 bg-emerald-500/10 p-6 rounded-xs space-y-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-7 w-7 text-emerald-400 shrink-0" />
            <div>
              <h2 className="text-base font-bold uppercase tracking-wide text-white">
                Ingestion Batch Committed Successfully
              </h2>
              <p className="text-xs text-white/70 mt-0.5">
                {commitResult.message}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link
              href="/crimes"
              className="btn-brand inline-flex items-center gap-2 rounded-xs px-4 py-2 text-xs font-bold uppercase tracking-wider"
            >
              <Database className="h-3.5 w-3.5" /> View in Crime Explorer
            </Link>
            <Link
              href="/map"
              className="btn-metallic inline-flex items-center gap-2 rounded-xs px-4 py-2 text-xs font-bold uppercase tracking-wider"
            >
              Explore Spatial Map <ArrowRight className="h-3.5 w-3.5" />
            </Link>
            <button
              onClick={resetAll}
              className="rounded-xs border border-white/10 px-4 py-2 text-xs font-bold uppercase text-white/60 hover:text-white"
            >
              Upload Another File
            </button>
          </div>
        </div>
      )}

      {/* Step 1: File Upload */}
      {!commitResult && (
        <div className="glass-panel rounded-xs p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div>
              <span className="text-[0.65rem] font-bold uppercase tracking-widest text-brand">
                Step 1
              </span>
              <h2 className="text-base font-bold uppercase tracking-tight text-white">
                Select CSV or JSON Dataset
              </h2>
            </div>
            {file && (
              <button
                onClick={resetAll}
                className="text-xs font-bold uppercase text-white/40 hover:text-white"
              >
                Clear File
              </button>
            )}
          </div>

          <div
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xs p-8 text-center cursor-pointer transition-all ${
              file
                ? "border-brand bg-brand/5"
                : "border-white/15 hover:border-brand/60 hover:bg-white/5"
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".csv,.json"
              className="hidden"
            />
            <UploadCloud className="mx-auto h-10 w-10 text-brand mb-3" />
            {file ? (
              <div>
                <p className="text-sm font-bold text-white font-mono">{file.name}</p>
                <p className="text-xs text-white/50 mt-1">
                  {(file.size / 1024).toFixed(1)} KB · Click to change file
                </p>
              </div>
            ) : (
              <div>
                <p className="text-sm font-bold text-white">
                  Drop crime dataset here, or <span className="text-brand underline">browse</span>
                </p>
                <p className="text-xs text-white/40 mt-1">
                  Supports standard CSV or JSON payloads containing coordinates and incident codes.
                </p>
              </div>
            )}
          </div>

          {/* Quick Helper / Benchmark Files */}
          <div className="rounded-xs border border-white/5 bg-white/5 p-3 flex items-start gap-2 text-xs text-white/60">
            <HelpCircle className="h-4 w-4 text-brand shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-white">Testing Benchmark:</span> You can test with{" "}
              <code className="text-brand font-mono">data/sample_crimes_valid.csv</code> or test rejection error handling with{" "}
              <code className="text-amber-400 font-mono">data/sample_crimes_with_errors.csv</code>.
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Raw Preview */}
      {file && rawPreview.length > 0 && !commitResult && (
        <div className="glass-panel rounded-xs p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div>
              <span className="text-[0.65rem] font-bold uppercase tracking-widest text-brand">
                Step 2
              </span>
              <h2 className="text-base font-bold uppercase tracking-tight text-white">
                Raw File Preview
              </h2>
            </div>
            <span className="text-xs font-mono text-white/40">Showing first 5 rows</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-[0.72rem] font-mono border border-white/10">
              <thead className="bg-black/50 text-white/50 border-b border-white/10 uppercase">
                <tr>
                  {rawPreview[0].map((header, i) => (
                    <th key={i} className="py-2 px-3">
                      {header.trim()}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-white/80">
                {rawPreview.slice(1).map((row, rowIdx) => (
                  <tr key={rowIdx} className="hover:bg-white/5">
                    {row.map((cell, colIdx) => (
                      <td key={colIdx} className="py-2 px-3 truncate max-w-[160px]">
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Start Validation Button */}
          {!validationResult && (
            <div className="pt-4 flex justify-end">
              <button
                onClick={handleValidate}
                disabled={validating}
                className="btn-brand inline-flex items-center gap-2 rounded-xs px-6 py-2.5 text-xs font-black uppercase tracking-wider"
              >
                {validating ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Validating Rows...
                  </>
                ) : (
                  <>
                    <FileCheck className="h-4 w-4" />
                    Start Validation (Dry Run)
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Step 3: Validation Diagnostic Results */}
      {validationResult && !commitResult && (
        <div className="glass-panel rounded-xs p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-white/10 pb-4">
            <div>
              <span className="text-[0.65rem] font-bold uppercase tracking-widest text-brand">
                Step 3
              </span>
              <h2 className="text-base font-bold uppercase tracking-tight text-white">
                Validation Diagnostic Report
              </h2>
              <p className="text-xs text-white/60 mt-0.5">
                Review accepted records and inspect rejection root causes before writing to PostGIS.
              </p>
            </div>

            {/* Ingestion Counts */}
            <div className="flex items-center gap-2 font-mono text-xs">
              <span className="rounded-xs border border-white/10 bg-white/5 px-3 py-1 text-white">
                Total: <strong>{validationResult.total_rows}</strong>
              </span>
              <span className="rounded-xs border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-emerald-400 font-bold">
                Valid: <strong>{validationResult.valid_count}</strong>
              </span>
              <span className="rounded-xs border border-rose-500/30 bg-rose-500/10 px-3 py-1 text-rose-400 font-bold">
                Rejected: <strong>{validationResult.rejected_count}</strong>
              </span>
            </div>
          </div>

          {/* Rejections Table if any exist */}
          {validationResult.rejections.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-rose-400">
                <AlertOctagon className="h-4 w-4" />
                Rejected Records ({validationResult.rejections.length})
              </div>

              <div className="overflow-x-auto rounded-xs border border-rose-500/20 bg-black/40">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="border-b border-rose-500/20 bg-rose-500/10 text-[0.65rem] font-bold uppercase text-rose-300">
                    <tr>
                      <th className="py-2.5 px-3">Row #</th>
                      <th className="py-2.5 px-3">Error Category</th>
                      <th className="py-2.5 px-3">Diagnostic Reason</th>
                      <th className="py-2.5 px-3">Raw Payload</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-[0.72rem]">
                    {validationResult.rejections.map((rej, idx) => (
                      <tr key={idx} className="hover:bg-rose-500/5">
                        <td className="py-2.5 px-3 font-bold text-white">
                          {rej.row_number ?? idx + 1}
                        </td>
                        <td className="py-2.5 px-3 text-rose-400 font-bold">
                          {rej.error_category}
                        </td>
                        <td className="py-2.5 px-3 text-white/90">
                          {rej.error_message}
                        </td>
                        <td className="py-2.5 px-3 text-white/50 truncate max-w-xs">
                          {JSON.stringify(rej.raw_data)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Valid Records Preview */}
          {validationResult.valid_count > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-400">
                <CheckCircle2 className="h-4 w-4" />
                Validated Records Sample ({validationResult.valid_count} ready to commit)
              </div>

              <div className="overflow-x-auto rounded-xs border border-emerald-500/20 bg-black/40">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="border-b border-emerald-500/20 bg-emerald-500/10 text-[0.65rem] font-bold uppercase text-emerald-300">
                    <tr>
                      <th className="py-2.5 px-3">Record ID</th>
                      <th className="py-2.5 px-3">Canonical Category</th>
                      <th className="py-2.5 px-3">Location</th>
                      <th className="py-2.5 px-3">Coordinates</th>
                      <th className="py-2.5 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-[0.72rem]">
                    {validationResult.preview_valid.map((v, idx) => (
                      <tr key={idx} className="hover:bg-white/5">
                        <td className="py-2.5 px-3 font-bold text-white">{v.record_id}</td>
                        <td className="py-2.5 px-3 text-brand font-bold">{v.category}</td>
                        <td className="py-2.5 px-3 text-white/80">{v.location_name}</td>
                        <td className="py-2.5 px-3 text-white/60">
                          {v.latitude}, {v.longitude}
                        </td>
                        <td className="py-2.5 px-3 text-emerald-400 font-bold">READY</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Commit Action Footer */}
          <div className="flex items-center justify-between border-t border-white/10 pt-4">
            <button
              onClick={resetAll}
              className="text-xs font-bold uppercase text-white/50 hover:text-white"
            >
              Cancel
            </button>

            <button
              onClick={handleCommit}
              disabled={committing || validationResult.valid_count === 0}
              className="btn-brand inline-flex items-center gap-2 rounded-xs px-6 py-2.5 text-xs font-black uppercase tracking-wider disabled:opacity-40 disabled:cursor-not-allowed shadow-brand-glow"
            >
              {committing ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Writing to PostGIS...
                </>
              ) : (
                <>
                  <Database className="h-4 w-4" />
                  Commit {validationResult.valid_count} Valid Records to Database
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
