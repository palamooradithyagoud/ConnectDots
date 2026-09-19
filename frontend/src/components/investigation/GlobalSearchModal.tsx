"use client";

import React, { useState, useEffect } from "react";
import {
  Search,
  X,
  FolderOpen,
  User,
  PhoneCall,
  ShieldCheck,
  ChevronRight,
  RefreshCw,
} from "lucide-react";
import { useInvestigation } from "@/context/InvestigationContext";
import { GlobalSearchResult, SearchHitItem } from "@/types/investigation";

export default function GlobalSearchModal() {
  const {
    isSearchModalOpen,
    closeSearchModal,
    loadCase,
    selectPerson,
    selectPhone,
    selectCrime,
  } = useInvestigation();

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const [query, setQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [results, setResults] = useState<GlobalSearchResult | null>(null);

  // Keyboard shortcut ⌘K or Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        // toggle search
        // can be handled via context
      } else if (e.key === "Escape" && isSearchModalOpen) {
        closeSearchModal();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSearchModalOpen, closeSearchModal]);

  const handleSearch = async (val: string) => {
    setQuery(val);
    if (!val.trim()) {
      setResults(null);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${apiUrl}/investigation/search?q=${encodeURIComponent(val.trim())}&limit=5`);
      if (res.ok) {
        const data: GlobalSearchResult = await res.json();
        setResults(data);
      }
    } catch (err) {
      console.warn("Search error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectHit = (hit: SearchHitItem) => {
    closeSearchModal();
    if (hit.entity_type === "CRIME") {
      const recId = hit.metadata?.record_id || hit.title.replace("Case ", "");
      loadCase(recId);
    } else if (hit.entity_type === "PERSON") {
      selectPerson(hit.id);
    } else if (hit.entity_type === "PHONE") {
      selectPhone(hit.id);
    }
  };

  if (!isSearchModalOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/80 pt-20 p-4 backdrop-blur-md">
      <div className="w-full max-w-xl rounded-2xl border border-white/10 bg-midnight p-4 shadow-2xl font-mono text-xs text-white">
        {/* Search Input Bar */}
        <div className="flex items-center gap-2 border-b border-white/10 pb-3">
          <Search className="h-4 w-4 text-brand" />
          <input
            autoFocus
            type="text"
            placeholder="Search cases, suspects, phones, or evidence ID..."
            value={query}
            onChange={(e) => handleSearch(e.target.value)}
            className="flex-1 bg-transparent text-sm text-white placeholder-white/40 focus:outline-none"
          />
          {loading && <RefreshCw className="h-4 w-4 animate-spin text-brand" />}
          <button
            onClick={closeSearchModal}
            className="rounded p-1 text-white/50 hover:bg-white/10 hover:text-white"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Categorized Results */}
        <div className="max-h-[60vh] overflow-y-auto pt-3 space-y-4">
          {results && results.total_results > 0 ? (
            <>
              {/* Crimes */}
              {results.crimes.length > 0 && (
                <div>
                  <span className="text-[0.65rem] font-bold text-white/40 uppercase tracking-wider block mb-1">
                    Cases & Incidents ({results.crimes.length})
                  </span>
                  <div className="space-y-1">
                    {results.crimes.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => handleSelectHit(c)}
                        className="flex items-center justify-between w-full rounded-lg border border-white/5 bg-white/[0.02] p-2 text-left hover:bg-brand/20 transition group"
                      >
                        <div className="flex items-center gap-2">
                          <FolderOpen className="h-4 w-4 text-purple-400" />
                          <div>
                            <span className="font-bold text-white group-hover:text-brand-accent">
                              {c.title}
                            </span>
                            <span className="block text-[0.65rem] text-white/50">{c.subtitle}</span>
                          </div>
                        </div>
                        <ChevronRight className="h-3.5 w-3.5 text-white/30 group-hover:text-white" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* People */}
              {results.people.length > 0 && (
                <div>
                  <span className="text-[0.65rem] font-bold text-white/40 uppercase tracking-wider block mb-1">
                    Individuals ({results.people.length})
                  </span>
                  <div className="space-y-1">
                    {results.people.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => handleSelectHit(p)}
                        className="flex items-center justify-between w-full rounded-lg border border-white/5 bg-white/[0.02] p-2 text-left hover:bg-brand/20 transition group"
                      >
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-purple-400" />
                          <div>
                            <span className="font-bold text-white group-hover:text-brand-accent">
                              {p.title}
                            </span>
                            <span className="block text-[0.65rem] text-white/50">{p.subtitle}</span>
                          </div>
                        </div>
                        <ChevronRight className="h-3.5 w-3.5 text-white/30 group-hover:text-white" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Phones */}
              {results.phones.length > 0 && (
                <div>
                  <span className="text-[0.65rem] font-bold text-white/40 uppercase tracking-wider block mb-1">
                    Telecommunications Lines ({results.phones.length})
                  </span>
                  <div className="space-y-1">
                    {results.phones.map((ph) => (
                      <button
                        key={ph.id}
                        onClick={() => handleSelectHit(ph)}
                        className="flex items-center justify-between w-full rounded-lg border border-white/5 bg-white/[0.02] p-2 text-left hover:bg-brand/20 transition group"
                      >
                        <div className="flex items-center gap-2">
                          <PhoneCall className="h-4 w-4 text-cyan-400" />
                          <div>
                            <span className="font-bold text-white group-hover:text-brand-accent">
                              {ph.title}
                            </span>
                            <span className="block text-[0.65rem] text-white/50">{ph.subtitle}</span>
                          </div>
                        </div>
                        <ChevronRight className="h-3.5 w-3.5 text-white/30 group-hover:text-white" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Reviews */}
              {results.reviews.length > 0 && (
                <div>
                  <span className="text-[0.65rem] font-bold text-white/40 uppercase tracking-wider block mb-1">
                    Validation Records ({results.reviews.length})
                  </span>
                  <div className="space-y-1">
                    {results.reviews.map((r) => (
                      <button
                        key={r.id}
                        onClick={() => handleSelectHit(r)}
                        className="flex items-center justify-between w-full rounded-lg border border-white/5 bg-white/[0.02] p-2 text-left hover:bg-brand/20 transition group"
                      >
                        <div className="flex items-center gap-2">
                          <ShieldCheck className="h-4 w-4 text-emerald-400" />
                          <div>
                            <span className="font-bold text-white group-hover:text-brand-accent">
                              {r.title}
                            </span>
                            <span className="block text-[0.65rem] text-white/50">{r.subtitle}</span>
                          </div>
                        </div>
                        <ChevronRight className="h-3.5 w-3.5 text-white/30 group-hover:text-white" />
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : query.trim() && !loading ? (
            <div className="text-center py-6 text-white/40">
              No matching records found for &ldquo;{query}&rdquo;
            </div>
          ) : (
            <div className="text-center py-6 text-white/30 text-[0.7rem]">
              Type a Case ID (e.g. 1042), Person name (e.g. Rajesh), or Phone (+91...) to search.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
