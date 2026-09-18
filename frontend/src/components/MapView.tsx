"use client";

import { useEffect, useRef } from "react";
import { GeoJSONFeature } from "@/types/crime";

interface MapViewProps {
  features: GeoJSONFeature[];
  selectedCategory?: string;
}

const CATEGORY_COLORS: Record<string, string> = {
  THEFT: "#5227ff",
  BURGLARY: "#8b66ff",
  ROBBERY: "#fb2c36",
  ASSAULT: "#e40014",
  HOMICIDE: "#9f0712",
  VEHICLE_THEFT: "#441bdf",
  FRAUD: "#3080ff",
  CYBERCRIME: "#00d294",
  NARCOTICS: "#ac4bff",
  VANDALISM: "#f99c00",
  OTHER: "#94a3b8",
};

export default function MapView({ features }: MapViewProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window === "undefined" || !mapContainerRef.current) return;

    let isMounted = true;

    // Dynamically import Leaflet to prevent Next.js SSR window errors
    import("leaflet").then((L) => {
      if (!isMounted || !mapContainerRef.current) return;

      // Inject Leaflet CSS dynamically if not present
      if (!document.getElementById("leaflet-css")) {
        const link = document.createElement("link");
        link.id = "leaflet-css";
        link.rel = "stylesheet";
        link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
        document.head.appendChild(link);
      }

      // Initialize map instance if not already initialized
      if (!mapInstanceRef.current) {
        const initialCoords = features.length > 0
          ? [features[0].geometry.coordinates[1], features[0].geometry.coordinates[0]]
          : [12.9716, 77.5946]; // Default to Bangalore center

        const map = L.map(mapContainerRef.current, {
          center: initialCoords as [number, number],
          zoom: 12,
          attributionControl: false,
        });

        // Dark Matter Tile Layer
        L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
          maxZoom: 19,
          subdomains: "abcd",
        }).addTo(map);

        mapInstanceRef.current = map;
      }

      const map = mapInstanceRef.current;

      // Clear existing marker layers
      map.eachLayer((layer: any) => {
        if (layer instanceof L.CircleMarker) {
          map.removeLayer(layer);
        }
      });

      const bounds: [number, number][] = [];

      // Render features as styled circle markers
      features.forEach((feat) => {
        const [lon, lat] = feat.geometry.coordinates;
        if (lat && lon && !isNaN(lat) && !isNaN(lon)) {
          bounds.push([lat, lon]);

          const color = CATEGORY_COLORS[feat.properties.category] || "#5227ff";

          const marker = L.circleMarker([lat, lon], {
            radius: 7,
            fillColor: color,
            color: "#ffffff",
            weight: 1.5,
            opacity: 0.9,
            fillOpacity: 0.85,
          });

          const popupContent = `
            <div style="font-family: inherit; font-size: 12px; line-height: 1.4; padding: 4px;">
              <div style="color: ${color}; font-weight: 800; font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase;">
                ${feat.properties.category}
              </div>
              <div style="font-weight: 800; font-size: 13px; color: #fff; margin-top: 2px;">
                ${feat.properties.record_id}
              </div>
              <div style="color: rgba(255,255,255,0.85); margin-top: 4px;">
                <strong>${feat.properties.location}</strong>
              </div>
              <div style="color: rgba(255,255,255,0.5); font-size: 11px; margin-top: 2px;">
                ${feat.properties.occurred_at ? new Date(feat.properties.occurred_at).toLocaleString() : ""}
              </div>
              ${feat.properties.description ? `<div style="margin-top: 6px; color: rgba(255,255,255,0.7); font-size: 11px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 4px;">${feat.properties.description}</div>` : ""}
            </div>
          `;

          marker.bindPopup(popupContent);
          marker.addTo(map);
        }
      });

      // Fit bounds if multiple points exist
      if (bounds.length > 1) {
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
      } else if (bounds.length === 1) {
        map.setView(bounds[0], 13);
      }
    });

    return () => {
      isMounted = false;
    };
  }, [features]);

  return (
    <div className="relative w-full h-full min-h-[500px] rounded-xs overflow-hidden border border-white/10">
      <div ref={mapContainerRef} className="w-full h-full min-h-[500px] bg-black" />

      {/* Category Legend Overlay */}
      <div className="absolute bottom-4 left-4 z-[400] glass-panel p-3 rounded-xs text-[0.7rem] max-w-xs shadow-lg">
        <span className="font-bold tracking-wider uppercase text-white/50 block mb-2">
          PostGIS Crime Clusters
        </span>
        <div className="grid grid-cols-2 gap-x-3 gap-y-1 font-mono text-[0.68rem]">
          {Object.entries(CATEGORY_COLORS).slice(0, 8).map(([cat, col]) => (
            <div key={cat} className="flex items-center gap-1.5 text-white/80">
              <span className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: col }} />
              <span className="truncate">{cat}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
