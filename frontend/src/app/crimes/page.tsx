"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Search,
  Filter,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Eye,
  RefreshCw,
  Trash2,
  MapPin,
  Calendar,
} from "lucide-react";
import { fetchCrimes, deleteCrime } from "@/lib/api";
import { CrimeRecord, CrimeListResponse } from "@/types/crime";
import CrimeDetailModal from "@/components/CrimeDetailModal";

const CATEGORIES = [
  "ALL",
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

export default function CrimeExplorerPage() {
  const [data, setData] = useState<CrimeListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("ALL");
  const [locationFilter, setLocationFilter] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [sortBy, setSortBy] = useState("occurred_at");
  const [order, setOrder] = useState<"asc" | "desc">("desc");

  const [selectedCrime, setSelectedCrime] = useState<CrimeRecord | null>(null);

  const loadCrimes = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchCrimes({
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
        category: category !== "ALL" ? category : undefined,
        location: locationFilter.trim() || undefined,
        sort_by: sortBy,
        order,
      });
      setData(res);
    } catch (err) {
      console.error("Failed to load crimes:", err);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, category, locationFilter, sortBy, order]);

  useEffect(() => {
    loadCrimes();
  }, [loadCrimes]);

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to permanently delete this crime incident?")) return;
    try {
      await deleteCrime(id);
      setSelectedCrime(null);
      loadCrimes();
    } catch (err: any) {
      alert(`Error deleting record: ${err.message}`);
    }
  };

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setOrder(order === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setOrder("desc");
    }
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <span className="text-[0.7rem] font-bold tracking-[0.3em] uppercase text-brand">
            Structured Dataset
          </span>
          <h1 className="mt-1 text-3xl font-black uppercase tracking-tight text-white font-mono">
            Crime Incident Explorer
          </h1>
          <p className="mt-1 text-sm text-white/60">
            Validated incidents stored with WGS84 coordinates in PostgreSQL + PostGIS.
          </p>
        </div>

        <button
          onClick={loadCrimes}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-4 py-2 text-xs font-bold uppercase tracking-wider text-white/80 hover:bg-white/[0.08] hover:text-white transition-all self-start active:scale-95"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-brand-300" : ""}`} />
          <span>Refresh Records</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="glass-panel p-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/40" />
          <input
            type="text"
            placeholder="Search record ID, type, location..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full rounded-lg border border-white/10 bg-black/40 py-2 pl-9 pr-3 text-xs text-white placeholder-white/40 focus:border-brand focus:outline-none transition"
          />
        </div>

        {/* Category Filter */}
        <div className="relative">
          <select
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              setPage(1);
            }}
            className="w-full rounded-lg border border-white/10 bg-black/40 py-2 px-3 text-xs text-white uppercase focus:border-brand focus:outline-none transition"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c} className="bg-midnight text-white">
                {c === "ALL" ? "All Categories" : c}
              </option>
            ))}
          </select>
        </div>

        {/* Location filter */}
        <div className="relative">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/40" />
          <input
            type="text"
            placeholder="Filter location / neighborhood..."
            value={locationFilter}
            onChange={(e) => {
              setLocationFilter(e.target.value);
              setPage(1);
            }}
            className="w-full rounded-lg border border-white/10 bg-black/40 py-2 pl-9 pr-3 text-xs text-white placeholder-white/40 focus:border-brand focus:outline-none transition"
          />
        </div>

        {/* Page Size & Count info */}
        <div className="flex items-center justify-between gap-2 px-2 text-xs font-mono text-white/60">
          <span>Found: <strong className="text-white">{data?.total ?? 0}</strong></span>
          <div className="flex items-center gap-1">
            <span>Rows:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="rounded-lg border border-white/10 bg-black/40 py-1 px-2 text-xs text-white focus:outline-none"
            >
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
            </select>
          </div>
        </div>
      </div>

      {/* High-density Data Table */}
      <div className="glass-panel overflow-hidden border border-white/10">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-white/10 bg-black/30 text-[0.68rem] font-bold uppercase tracking-wider text-white/50 select-none">
              <tr>
                <th
                  onClick={() => handleSort("record_id")}
                  className="py-3 px-4 cursor-pointer hover:text-white"
                >
                  <div className="flex items-center gap-1">
                    Record ID <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort("category")}
                  className="py-3 px-4 cursor-pointer hover:text-white"
                >
                  <div className="flex items-center gap-1">
                    Category / Type <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort("location_name")}
                  className="py-3 px-4 cursor-pointer hover:text-white"
                >
                  <div className="flex items-center gap-1">
                    Location <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort("occurred_at")}
                  className="py-3 px-4 cursor-pointer hover:text-white"
                >
                  <div className="flex items-center gap-1">
                    Date & Time <ArrowUpDown className="h-3 w-3" />
                  </div>
                </th>
                <th className="py-3 px-4">Coordinates (Lat, Lon)</th>
                <th className="py-3 px-4">Source</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-xs text-white/40">
                    <RefreshCw className="mx-auto h-5 w-5 animate-spin mb-2 text-brand" />
                    Querying PostgreSQL / PostGIS records...
                  </td>
                </tr>
              ) : data && data.items.length > 0 ? (
                data.items.map((item) => {
                  const occurred = new Date(item.occurred_at);
                  return (
                    <tr
                      key={item.id}
                      onClick={() => setSelectedCrime(item)}
                      className="hover:bg-white/5 cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-4 font-bold text-white tracking-wide">
                        {item.record_id}
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-bold text-brand uppercase block">
                          {item.category}
                        </span>
                        <span className="text-[0.68rem] text-white/50">{item.crime_type}</span>
                      </td>
                      <td className="py-3 px-4 text-white/90 font-sans">
                        {item.location_name}
                      </td>
                      <td className="py-3 px-4 text-white/70">
                        <div>{occurred.toLocaleDateString()}</div>
                        <div className="text-[0.68rem] text-white/40">{occurred.toLocaleTimeString()}</div>
                      </td>
                      <td className="py-3 px-4 text-white/80">
                        {item.latitude.toFixed(4)}, {item.longitude.toFixed(4)}
                      </td>
                      <td className="py-3 px-4 text-white/60 font-sans truncate max-w-[140px]">
                        {item.source}
                      </td>
                      <td className="py-3 px-4">
                        <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[0.65rem] text-emerald-400 font-bold uppercase">
                          {item.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => setSelectedCrime(item)}
                            className="rounded-xs p-1 text-white/40 hover:text-white transition-colors"
                            title="View Record Details"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(item.id)}
                            className="rounded-xs p-1 text-rose-400/60 hover:text-rose-400 transition-colors"
                            title="Delete Record"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-xs text-white/40">
                    No crime incidents matching the selected criteria found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-between border-t border-white/10 px-4 py-3 text-xs font-mono text-white/60">
            <div>
              Page <strong className="text-white">{data.page}</strong> of {data.total_pages}
            </div>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="flex items-center gap-1 rounded-xs border border-white/10 px-3 py-1.5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-3.5 w-3.5" /> Prev
              </button>
              <button
                disabled={page >= data.total_pages}
                onClick={() => setPage(page + 1)}
                className="flex items-center gap-1 rounded-xs border border-white/10 px-3 py-1.5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                Next <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Record Details Modal */}
      <CrimeDetailModal
        crime={selectedCrime}
        onClose={() => setSelectedCrime(null)}
        onDelete={handleDelete}
      />
    </div>
  );
}
