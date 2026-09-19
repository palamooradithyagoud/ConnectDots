"use client";

import { useState } from "react";
import {
  Search,
  Sparkles,
  SlidersHorizontal,
  MapPin,
  Calendar,
  Crosshair,
  Car,
  ArrowRight,
  RefreshCw,
  AlertCircle,
  Cpu,
} from "lucide-react";
import { semanticSearch } from "@/lib/nlp-api";
import { fetchCrimeById } from "@/lib/api";
import { SemanticSearchResult, CrimeRecord } from "@/types/crime";
import CrimeDetailModal from "@/components/CrimeDetailModal";

const SAMPLE_QUERIES = [
  "Armed robbery at convenience store with knife threat",
  "Overnight break-in at showroom lock broken",
  "Motorcycle stolen from residential driveway",
  "Phishing scam corporate bank accounts",
  "Damage to public transit signage and bus shelter",
  "Possession of illicit synthetic substances",
];

const CATEGORIES = [
  "THEFT",
  "BURGLARY",
  "ROBBERY",
  "ASSAULT",
  "HOMICIDE",
  "VEHICLE_THEFT",
  "FRAUD",
  "CYBERCRIME",
  "NARCOTICS",
  "VANDALISM",
];

export default function SemanticSearchPage() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<string>("");
  const [similarityThreshold, setSimilarityThreshold] = useState<number>(0.40);
  const [location, setLocation] = useState("");
  const [results, setResults] = useState<SemanticSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Selected crime for detail modal
  const [selectedCrime, setSelectedCrime] = useState<CrimeRecord | null>(null);
  const [loadingCrime, setLoadingCrime] = useState(false);

  const handleSearch = async (overrideQuery?: string) => {
    const q = overrideQuery !== undefined ? overrideQuery : query;
    if (!q.trim()) return;

    if (overrideQuery) {
      setQuery(overrideQuery);
    }

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const resp = await semanticSearch({
        query: q,
        category: category || undefined,
        similarityThreshold: similarityThreshold,
        location: location || undefined,
        limit: 20,
      });
      setResults(resp.results);
    } catch (err: any) {
      setError(err.message || "Semantic search request failed");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDetail = async (crimeId: string) => {
    setLoadingCrime(true);
    try {
      const data = await fetchCrimeById(crimeId);
      setSelectedCrime(data);
    } catch (err) {
      console.error("Failed to load crime details:", err);
    } finally {
      setLoadingCrime(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Search Header */}
      <div className="border-b border-white/10 pb-6">
        <div className="flex items-center gap-2 mb-1">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-brand/30 bg-brand/10 px-2.5 py-0.5 text-[0.65rem] font-bold tracking-[0.2em] uppercase text-brand">
            <Cpu className="h-3 w-3" /> ConnectDots · Qdrant Vector Engine
          </span>
          <span className="text-[0.65rem] font-medium text-white/40 uppercase tracking-widest">
            384-Dim Semantic Retrieval
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black uppercase tracking-tight text-white font-mono">
          Semantic Crime Search
        </h1>
        <p className="mt-1 text-sm text-white/60">
          Query crime incidents using natural language, modus operandi patterns, or narrative descriptions.
        </p>
      </div>

      {/* Main Search Input & Filter Panel */}
      <div className="glass-panel rounded-xs p-6 space-y-5 border border-brand/30 shadow-brand-glow">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch();
          }}
          className="space-y-4"
        >
          {/* Query Bar */}
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe an incident, weapon, or modus operandi (e.g. 'armed robbery with knife at store')..."
              className="w-full rounded-xs border border-white/15 bg-black/50 py-3.5 pl-12 pr-28 text-sm font-mono text-white placeholder-white/40 focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
            />
            <Search className="absolute left-4 top-4 h-4 w-4 text-brand" />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="btn-brand absolute right-2 top-2 inline-flex items-center gap-2 rounded-xs px-4 py-2 text-xs font-black uppercase tracking-wider disabled:opacity-50"
            >
              <Sparkles className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              {loading ? "Searching..." : "Search"}
            </button>
          </div>

          {/* Quick Example Chips */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40">
              Sample Prompts:
            </span>
            {SAMPLE_QUERIES.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSearch(sample)}
                className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[0.68rem] text-white/70 hover:border-brand hover:text-white hover:bg-brand/10 transition-all text-left"
              >
                {sample}
              </button>
            ))}
          </div>

          {/* Advanced Controls Row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 border-t border-white/10 pt-4">
            {/* Category Filter */}
            <div>
              <label className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40 block mb-1">
                Filter by Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-xs border border-white/10 bg-midnight-surface px-3 py-2 text-xs font-mono text-white focus:border-brand focus:outline-none"
              >
                <option value="">All Categories</option>
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            {/* Location Substring Filter */}
            <div>
              <label className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40 block mb-1">
                Location Filter
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Indiranagar, MG Road..."
                  className="w-full rounded-xs border border-white/10 bg-midnight-surface py-2 pl-8 pr-3 text-xs font-mono text-white placeholder-white/30 focus:border-brand focus:outline-none"
                />
                <MapPin className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-white/40" />
              </div>
            </div>

            {/* Similarity Threshold Slider */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40">
                  Min Similarity Threshold
                </label>
                <span className="text-xs font-bold font-mono text-brand">
                  {Math.round(similarityThreshold * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0.30"
                max="0.90"
                step="0.05"
                value={similarityThreshold}
                onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
                className="w-full accent-brand cursor-pointer"
              />
            </div>
          </div>
        </form>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-xs border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Search Results */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
            <span>Search Results</span>
            {searched && (
              <span className="rounded-full bg-white/10 px-2 py-0.5 text-xs font-mono text-white/70">
                {results.length} matched
              </span>
            )}
          </h2>

          {searched && results.length > 0 && (
            <span className="text-xs font-mono text-white/40">
              Ranked by Qdrant Cosine Similarity
            </span>
          )}
        </div>

        {loading ? (
          <div className="glass-panel rounded-xs py-16 text-center space-y-3">
            <RefreshCw className="mx-auto h-6 w-6 animate-spin text-brand" />
            <p className="text-xs font-mono text-white/60">
              Encoding query with SentenceTransformer & searching Qdrant vector index...
            </p>
          </div>
        ) : results.length > 0 ? (
          <div className="space-y-3">
            {results.map((item) => {
              const scorePercent = Math.round(item.similarity_score * 100);
              return (
                <div
                  key={item.crime_id}
                  className="glass-panel rounded-xs p-5 hover:border-brand/50 transition-all group relative overflow-hidden"
                >
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    {/* Left: Incident info & narrative */}
                    <div className="space-y-2 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-xs font-mono font-bold text-white group-hover:text-brand transition-colors">
                          {item.record_id}
                        </span>
                        <span className="rounded-full border border-brand/30 bg-brand/10 px-2.5 py-0.5 text-[0.65rem] font-bold uppercase tracking-wider text-brand">
                          {item.predicted_category || item.category}
                        </span>
                        {item.location && (
                          <span className="inline-flex items-center gap-1 text-[0.7rem] text-white/60">
                            <MapPin className="h-3 w-3 text-brand" /> {item.location}
                          </span>
                        )}
                        {item.occurred_at && (
                          <span className="inline-flex items-center gap-1 text-[0.7rem] text-white/40 font-mono">
                            <Calendar className="h-3 w-3" /> {new Date(item.occurred_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>

                      {item.description && (
                        <p className="text-xs text-white/80 font-mono line-clamp-2">
                          &ldquo;{item.description}&rdquo;
                        </p>
                      )}

                      {/* Extracted badges (weapons, vehicles, MO) */}
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {item.weapons?.map((w, i) => (
                          <span key={`w-${i}`} className="inline-flex items-center gap-1 rounded-full border border-rose-500/30 bg-rose-500/10 px-2 py-0.5 text-[0.65rem] text-rose-300">
                            <Crosshair className="h-2.5 w-2.5" /> {w}
                          </span>
                        ))}
                        {item.vehicles?.map((v, i) => (
                          <span key={`v-${i}`} className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[0.65rem] text-amber-300">
                            <Car className="h-2.5 w-2.5" /> {v}
                          </span>
                        ))}
                        {item.modus_operandi?.map((mo, i) => (
                          <span key={`mo-${i}`} className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[0.65rem] font-bold text-white/70">
                            {mo.pattern}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Right: Similarity Score & Action */}
                    <div className="flex items-center gap-5 shrink-0 border-t md:border-t-0 md:border-l border-white/10 pt-3 md:pt-0 md:pl-5">
                      <div className="text-right">
                        <span className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40 block">
                          Semantic Match
                        </span>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-xl font-black font-mono text-white">
                            {scorePercent}%
                          </span>
                          <div className="w-12 h-2 rounded-full bg-white/10 overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-brand to-emerald-400 rounded-full"
                              style={{ width: `${scorePercent}%` }}
                            />
                          </div>
                        </div>
                      </div>

                      <button
                        onClick={() => handleOpenDetail(item.crime_id)}
                        disabled={loadingCrime}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-brand/40 bg-brand/10 hover:bg-brand/20 text-brand-200 px-3 py-2 text-xs font-bold uppercase tracking-wider transition-all"
                      >
                        Inspect <ArrowRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : searched ? (
          <div className="glass-panel py-16 text-center space-y-2">
            <p className="text-sm font-bold uppercase text-white">No Semantically Similar Incidents Found</p>
            <p className="text-xs text-white/50">
              Try lowering the similarity threshold slider or searching with broader keywords.
            </p>
          </div>
        ) : (
          <div className="glass-panel py-16 text-center space-y-2">
            <p className="text-sm font-bold uppercase text-white/60">Ready for Semantic Search</p>
            <p className="text-xs text-white/40">
              Type a crime description above or click one of the sample prompt buttons to search Qdrant.
            </p>
          </div>
        )}
      </div>

      {/* Crime Detail Modal with NLP Card */}
      {selectedCrime && (
        <CrimeDetailModal
          crime={selectedCrime}
          onClose={() => setSelectedCrime(null)}
        />
      )}
    </div>
  );
}
