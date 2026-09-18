"use client";

import { useEffect, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import { MapPin, Filter, RefreshCw, Layers, ShieldAlert, Compass } from "lucide-react";
import { fetchLocations } from "@/lib/api";
import { GeoJSONFeatureCollection } from "@/types/crime";

// Dynamic import for Leaflet map component with SSR disabled
const MapView = dynamic(() => import("@/components/MapView"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[600px] w-full items-center justify-center rounded-xs border border-white/10 bg-black/60 font-mono text-xs text-white/50">
      <RefreshCw className="h-5 w-5 animate-spin text-brand mr-2" />
      Loading PostGIS Map Projection...
    </div>
  ),
});

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

export default function SpatialMapPage() {
  const [data, setData] = useState<GeoJSONFeatureCollection | null>(null);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("ALL");

  const loadPoints = useCallback(async () => {
    setLoading(true);
    try {
      const geojson = await fetchLocations(category !== "ALL" ? category : undefined);
      setData(geojson);
    } catch (err) {
      console.error("Failed to load map coordinates:", err);
    } finally {
      setLoading(false);
    }
  }, [category]);

  useEffect(() => {
    loadPoints();
  }, [loadPoints]);

  const features = data?.features || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-white/10 pb-6">
        <div>
          <span className="text-[0.7rem] font-bold tracking-[0.3em] uppercase text-brand">
            Geospatial Intelligence
          </span>
          <h1 className="mt-1 text-3xl font-black uppercase tracking-tight text-white font-mono">
            Spatial Crime Visualizer
          </h1>
          <p className="mt-1 text-sm text-white/60">
            Interactive PostGIS spatial mapping with coordinate verification and category clustering.
          </p>
        </div>

        {/* Filter controls */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="rounded-xs border border-white/10 bg-midnight px-3 py-2 text-xs font-mono font-bold uppercase text-white focus:border-brand focus:outline-none"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c} className="bg-midnight text-white">
                  {c === "ALL" ? "All Crime Types" : c}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={loadPoints}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xs border border-white/10 bg-white/5 px-3 py-2 text-xs font-bold uppercase tracking-wider text-white hover:bg-white/10 transition-all"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Map Card */}
      <div className="glass-panel rounded-xs p-4 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-mono text-white/60 px-1">
          <div className="flex items-center gap-2">
            <Compass className="h-4 w-4 text-brand" />
            <span>
              Plotted Incidents: <strong className="text-white">{features.length}</strong>
            </span>
          </div>
          <div className="text-[0.7rem] text-white/40">
            Projections rendered via EPSG:4326 PostGIS GEOGRAPHY(POINT)
          </div>
        </div>

        {/* Dynamic Leaflet Map */}
        <div className="h-[640px] w-full">
          <MapView features={features} selectedCategory={category} />
        </div>
      </div>
    </div>
  );
}
