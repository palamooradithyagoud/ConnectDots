import { CrimeRecord } from "@/types/crime";
import { X, MapPin, Calendar, Clock, ShieldAlert, FileText, Trash2, ExternalLink } from "lucide-react";
import NLPAnalysisCard from "@/components/NLPAnalysisCard";

interface CrimeDetailModalProps {
  crime: CrimeRecord | null;
  onClose: () => void;
  onDelete?: (id: string) => void;
  onUpdate?: () => void;
}

export default function CrimeDetailModal({ crime, onClose, onDelete, onUpdate }: CrimeDetailModalProps) {
  if (!crime) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="glass-panel w-full max-w-3xl rounded-xs border border-white/15 bg-midnight-surface p-6 shadow-card-glass relative max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-white/10 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[0.7rem] font-bold tracking-[0.2em] uppercase text-brand">
                Incident Detail
              </span>
              <span className="rounded-full bg-brand/10 border border-brand/30 px-2 py-0.5 text-[0.65rem] font-mono font-bold text-brand">
                {crime.status}
              </span>
            </div>
            <h2 className="mt-1 text-2xl font-black uppercase tracking-tight text-white font-mono">
              {crime.record_id}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-xs p-1 text-white/50 hover:bg-white/10 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Grid */}
        <div className="mt-6 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="rounded-xs border border-white/5 bg-white/5 p-3">
              <span className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40 flex items-center gap-1">
                <ShieldAlert className="h-3.5 w-3.5 text-brand" /> Category / Type
              </span>
              <p className="mt-1 font-bold text-white uppercase text-sm">
                {crime.category}
              </p>
              <p className="text-xs text-white/60">{crime.crime_type}</p>
            </div>

            <div className="rounded-xs border border-white/5 bg-white/5 p-3">
              <span className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40 flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5 text-brand" /> Location
              </span>
              <p className="mt-1 font-bold text-white text-sm">{crime.location_name}</p>
              <p className="text-xs font-mono text-white/60">
                {crime.latitude.toFixed(6)}, {crime.longitude.toFixed(6)}
              </p>
            </div>

            <div className="rounded-xs border border-white/5 bg-white/5 p-3">
              <span className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40 flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5 text-brand" /> Occurred Timestamp
              </span>
              <p className="mt-1 font-bold text-white text-sm font-mono">
                {new Date(crime.occurred_at).toLocaleString()}
              </p>
              <p className="text-xs text-white/60">UTC Standardized</p>
            </div>

            <div className="rounded-xs border border-white/5 bg-white/5 p-3">
              <span className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40 flex items-center gap-1">
                <FileText className="h-3.5 w-3.5 text-brand" /> Data Source
              </span>
              <p className="mt-1 font-bold text-white text-sm">{crime.source}</p>
              <p className="text-xs text-white/60">Verified Agency</p>
            </div>
          </div>

          {/* Description */}
          {crime.description && (
            <div className="rounded-xs border border-white/5 bg-white/5 p-4">
              <span className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40">
                Original Incident Description
              </span>
              <p className="mt-2 text-sm text-white/85 leading-relaxed">
                {crime.description}
              </p>
            </div>
          )}

          {/* Phase 2: NLP Intelligence & Understanding */}
          <NLPAnalysisCard crimeId={crime.id} onAnalysisUpdated={onUpdate} />

          {/* PostGIS Geolocation metadata */}
          <div className="rounded-xs border border-brand/20 bg-brand/5 p-4">
            <span className="text-[0.65rem] font-bold uppercase tracking-wider text-brand flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" /> Spatial PostGIS Representation
            </span>
            <p className="mt-1 text-xs font-mono text-white/80">
              GEOGRAPHY(Point, 4326): POINT({crime.longitude} {crime.latitude})
            </p>
            <a
              href={`https://www.google.com/maps?q=${crime.latitude},${crime.longitude}`}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-flex items-center gap-1 text-[0.7rem] font-bold uppercase text-brand hover:underline"
            >
              Open External Geolocation <ExternalLink className="h-3 w-3" />
            </a>
          </div>

          {/* Extra metadata */}
          {crime.extra_metadata && Object.keys(crime.extra_metadata).length > 0 && (
            <div className="rounded-xs border border-white/5 bg-black/40 p-4">
              <span className="text-[0.65rem] font-bold uppercase tracking-wider text-white/40">
                Unstructured / Raw Metadata (Phase 2 & 3 Hooks)
              </span>
              <pre className="mt-2 text-xs font-mono text-emerald-400 overflow-x-auto p-2 bg-black/60 rounded">
                {JSON.stringify(crime.extra_metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="mt-8 flex items-center justify-between border-t border-white/10 pt-4">
          {onDelete ? (
            <button
              onClick={() => onDelete(crime.id)}
              className="inline-flex items-center gap-1.5 text-xs font-bold uppercase text-rose-400 hover:text-rose-300 transition-colors"
            >
              <Trash2 className="h-4 w-4" /> Delete Incident
            </button>
          ) : <div />}

          <button
            onClick={onClose}
            className="rounded-xs border border-white/20 px-4 py-2 text-xs font-bold uppercase text-white hover:bg-white/10 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
