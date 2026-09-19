"use client";

import React, { useEffect, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import {
  MapPin,
  RefreshCw,
  Layers,
  Compass,
  Maximize2,
  ExternalLink,
} from "lucide-react";
import { useInvestigation } from "@/context/InvestigationContext";
import { GeoJSONFeatureCollection } from "@/types/crime";

// Dynamic import for Leaflet map component with SSR disabled
const MapView = dynamic(() => import("@/components/MapView"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[380px] w-full items-center justify-center rounded-xl border border-white/10 bg-black/60 font-mono text-xs text-white/50">
      <RefreshCw className="h-5 w-5 animate-spin text-brand mr-2" />
      Loading PostGIS Spatial Corridor...
    </div>
  ),
});

export default function GeographicIntelligencePanel() {
  const { caseContext, selectedCrimeId, selectCrime } = useInvestigation();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  const [geoData, setGeoData] = useState<GeoJSONFeatureCollection | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchLocations = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiUrl}/crimes/locations?limit=200`);
      if (res.ok) {
        const data = await res.json();
        setGeoData(data);
      }
    } catch (err) {
      console.warn("Could not fetch crime locations:", err);
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchLocations();
  }, [fetchLocations]);

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-midnight/80 p-4 backdrop-blur-xl shadow-2xl text-xs font-mono h-[420px]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <Compass className="h-4 w-4 text-emerald-400" />
          <h3 className="font-bold uppercase tracking-wider text-white">
            Geographic Intelligence & Spatial Corridors
          </h3>
        </div>

        {caseContext?.location_name && (
          <div className="flex items-center gap-1 text-[0.68rem] text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
            <MapPin className="h-3 w-3" />
            <span>Target: {caseContext.location_name}</span>
          </div>
        )}
      </div>

      {/* Embedded Map Canvas */}
      <div className="flex-1 rounded-xl overflow-hidden border border-white/10 relative">
        {geoData && geoData.features ? (
          <MapView features={geoData.features} />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-white/40">
            <RefreshCw className="h-4 w-4 animate-spin mr-2 text-brand" />
            Rendering spatial layers...
          </div>
        )}
      </div>
    </div>
  );
}
