"use client";

import React, { useState, useRef, useEffect, useMemo } from "react";
import { GraphNode, GraphEdge } from "@/types/investigation";
import {
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Layers,
  MapPin,
  Car,
  Crosshair,
  Zap,
  User,
  ShieldAlert,
  Building,
  Maximize2,
  Minimize2,
  PhoneCall,
  TrendingUp
} from "lucide-react";
import { cn } from "@/lib/utils";

interface InteractiveGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNodeId: string | null;
  selectedEdge: GraphEdge | null;
  onSelectNode: (node: GraphNode | null) => void;
  onSelectEdge: (edge: GraphEdge | null) => void;
  onDrillDownCrime?: (crimeId: string) => void;
  highlightedNodeIds?: Set<string>;
  highlightedEdgeIds?: Set<string>;
  onLaunchInvestigation?: (entityId: string, label: string) => void;
}

interface PositionedNode extends GraphNode {
  x: number;
  y: number;
}

export default function InteractiveGraph({
  nodes,
  edges,
  selectedNodeId,
  selectedEdge,
  onSelectNode,
  onSelectEdge,
  onDrillDownCrime,
  highlightedNodeIds,
  highlightedEdgeIds,
  onLaunchInvestigation,
}: InteractiveGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  const toggleFullscreen = async () => {
    try {
      if (!isFullscreen) {
        if (containerRef.current?.requestFullscreen) {
          await containerRef.current.requestFullscreen();
        }
        setIsFullscreen(true);
      } else {
        if (document.fullscreenElement && document.exitFullscreen) {
          await document.exitFullscreen();
        }
        setIsFullscreen(false);
      }
    } catch {
      setIsFullscreen((prev) => !prev);
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  // Custom dragged positions per node id
  const [nodePositions, setNodePositions] = useState<Record<string, { x: number; y: number }>>({});

  // Canvas Panning State
  const [isPanning, setIsPanning] = useState<boolean>(false);
  const [panStart, setPanStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Node Dragging State
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const [nodeDragOffset, setNodeDragOffset] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [hasMovedDuringDrag, setHasMovedDuringDrag] = useState<boolean>(false);

  // Pinch-to-zoom Touch State
  const [initialPinchDistance, setInitialPinchDistance] = useState<number | null>(null);
  const [initialPinchZoom, setInitialPinchZoom] = useState<number>(1);

  // Compute 2D node layout using an orbital / radial force layout around center, merged with customized dragged positions
  const layoutNodes: PositionedNode[] = useMemo(() => {
    if (!nodes || nodes.length === 0) return [];

    const width = 800;
    const height = 550;
    const centerX = width / 2;
    const centerY = height / 2;

    // Find primary center node (first crime or center_node_id)
    const centerNode = nodes.find(n => n.label === "Crime") || nodes[0];
    const otherNodes = nodes.filter(n => n.id !== centerNode.id);

    const positioned: PositionedNode[] = [
      {
        ...centerNode,
        x: centerX,
        y: centerY,
      },
    ];

    // Group other nodes by label/type for organized orbital rings
    const entityNodes = otherNodes.filter(n => ["Location", "Vehicle", "Weapon", "ModusOperandi", "Person", "Organization", "Phone"].includes(n.label));
    const relatedCrimes = otherNodes.filter(n => n.label === "Crime");
    const clusterNodes = otherNodes.filter(n => ["CrimeCluster", "Pattern"].includes(n.label));

    // Ring 1: Direct extracted entities (Radius 150)
    const r1 = 150;
    entityNodes.forEach((node, idx) => {
      const angle = (idx / Math.max(entityNodes.length, 1)) * 2 * Math.PI - Math.PI / 2;
      positioned.push({
        ...node,
        x: centerX + r1 * Math.cos(angle),
        y: centerY + r1 * Math.sin(angle),
      });
    });

    // Ring 2: Related Crime incidents (Radius 260)
    const r2 = 260;
    relatedCrimes.forEach((node, idx) => {
      const angle = (idx / Math.max(relatedCrimes.length, 1)) * 2 * Math.PI + Math.PI / 4;
      positioned.push({
        ...node,
        x: centerX + r2 * Math.cos(angle),
        y: centerY + r2 * Math.sin(angle),
      });
    });

    // Ring 3: Clusters and Patterns (Radius 330)
    const r3 = 330;
    clusterNodes.forEach((node, idx) => {
      const angle = (idx / Math.max(clusterNodes.length, 1)) * 2 * Math.PI + Math.PI / 3;
      positioned.push({
        ...node,
        x: centerX + r3 * Math.cos(angle),
        y: centerY + r3 * Math.sin(angle),
      });
    });

    // Apply any interactive dragged positions
    return positioned.map(node => {
      const customPos = nodePositions[node.id];
      if (customPos) {
        return { ...node, x: customPos.x, y: customPos.y };
      }
      return node;
    });
  }, [nodes, nodePositions]);

  const nodeMap = useMemo(() => {
    const map = new Map<string, PositionedNode>();
    layoutNodes.forEach(n => {
      map.set(n.id, n);
      // Also map with clean IDs for robust edge resolution
      if (n.id.startsWith("crime:")) {
        map.set(n.id.replace("crime:", ""), n);
      }
    });
    return map;
  }, [layoutNodes]);

  // Color mapping based on node type
  const getNodeColor = (label: string) => {
    switch (label) {
      case "Crime":
        return { bg: "#7c3aed", border: "#a78bfa", text: "#ede9fe", ring: "rgba(124, 58, 237, 0.4)" };
      case "Location":
        return { bg: "#059669", border: "#34d399", text: "#d1fae5", ring: "rgba(5, 150, 105, 0.4)" };
      case "Vehicle":
        return { bg: "#d97706", border: "#fbbf24", text: "#fef3c7", ring: "rgba(217, 119, 6, 0.4)" };
      case "Weapon":
        return { bg: "#e11d48", border: "#fb7185", text: "#ffe4e6", ring: "rgba(225, 29, 72, 0.4)" };
      case "ModusOperandi":
        return { bg: "#0891b2", border: "#22d3ee", text: "#cffafe", ring: "rgba(8, 145, 178, 0.4)" };
      case "CrimeCluster":
        return { bg: "#2563eb", border: "#60a5fa", text: "#dbeafe", ring: "rgba(37, 99, 235, 0.4)" };
      case "Pattern":
        return { bg: "#ea580c", border: "#fb923c", text: "#ffedd5", ring: "rgba(234, 88, 12, 0.4)" };
      case "Person":
        return { bg: "#c026d3", border: "#e879f9", text: "#fae8ff", ring: "rgba(192, 38, 211, 0.4)" };
      case "Organization":
        return { bg: "#4f46e5", border: "#818cf8", text: "#e0e7ff", ring: "rgba(79, 70, 229, 0.4)" };
      case "Phone":
        return { bg: "#0d9488", border: "#2dd4bf", text: "#ccfbf1", ring: "rgba(13, 148, 136, 0.4)" };
      default:
        return { bg: "#475569", border: "#94a3b8", text: "#f1f5f9", ring: "rgba(71, 85, 105, 0.4)" };
    }
  };

  const getNodeIcon = (label: string) => {
    switch (label) {
      case "Crime":
        return <ShieldAlert className="h-3.5 w-3.5" />;
      case "Location":
        return <MapPin className="h-3.5 w-3.5" />;
      case "Vehicle":
        return <Car className="h-3.5 w-3.5" />;
      case "Weapon":
        return <Crosshair className="h-3.5 w-3.5" />;
      case "ModusOperandi":
        return <Zap className="h-3.5 w-3.5" />;
      case "CrimeCluster":
        return <Layers className="h-3.5 w-3.5" />;
      case "Pattern":
        return <TrendingUp className="h-3.5 w-3.5" />;
      case "Person":
        return <User className="h-3.5 w-3.5" />;
      case "Organization":
        return <Building className="h-3.5 w-3.5" />;
      case "Phone":
        return <PhoneCall className="h-3.5 w-3.5" />;
      default:
        return <ShieldAlert className="h-3.5 w-3.5" />;
    }
  };

  const getNodeLabelText = (node: GraphNode) => {
    const p = node.properties || {};
    if (node.label === "Crime") return p.record_id || p.category || node.id;
    if (node.label === "Phone") return p.number || node.id.replace("phone:", "");
    return p.canonical_name || p.name || p.pattern || p.description || node.id.split(":").pop() || node.id;
  };

  // Helper: Convert screen viewport coordinates to transformed SVG viewBox space
  const getSvgCoords = (clientX: number, clientY: number) => {
    if (!svgRef.current) return { x: clientX, y: clientY };
    const rect = svgRef.current.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return { x: clientX, y: clientY };
    const scaleX = 800 / rect.width;
    const scaleY = 550 / rect.height;
    const svgX = (clientX - rect.left) * scaleX;
    const svgY = (clientY - rect.top) * scaleY;
    return {
      x: (svgX - pan.x) / zoom,
      y: (svgY - pan.y) / zoom,
    };
  };

  // Node Drag Initiation
  const startNodeDrag = (node: PositionedNode, clientX: number, clientY: number, e: React.SyntheticEvent) => {
    e.stopPropagation();
    const coords = getSvgCoords(clientX, clientY);
    setDraggingNodeId(node.id);
    setNodeDragOffset({
      x: node.x - coords.x,
      y: node.y - coords.y,
    });
    setHasMovedDuringDrag(false);
  };

  // Pointer/Touch Movement Engine
  const handlePointerMove = (clientX: number, clientY: number) => {
    if (draggingNodeId) {
      setHasMovedDuringDrag(true);
      const coords = getSvgCoords(clientX, clientY);
      const newX = coords.x + nodeDragOffset.x;
      const newY = coords.y + nodeDragOffset.y;
      setNodePositions(prev => ({
        ...prev,
        [draggingNodeId]: { x: newX, y: newY },
      }));
    } else if (isPanning) {
      setPan({
        x: clientX - panStart.x,
        y: clientY - panStart.y,
      });
    }
  };

  const handlePointerUp = () => {
    setIsPanning(false);
    setDraggingNodeId(null);
    setInitialPinchDistance(null);
  };

  // Global window listeners for ultra-smooth drag release and mouse tracking
  useEffect(() => {
    if (!draggingNodeId && !isPanning) return;

    const handleGlobalMouseMove = (e: MouseEvent) => {
      handlePointerMove(e.clientX, e.clientY);
    };

    const handleGlobalMouseUp = () => {
      handlePointerUp();
    };

    const handleGlobalTouchMove = (e: TouchEvent) => {
      if (e.touches.length === 1) {
        handlePointerMove(e.touches[0].clientX, e.touches[0].clientY);
      }
    };

    const handleGlobalTouchEnd = () => {
      handlePointerUp();
    };

    window.addEventListener("mousemove", handleGlobalMouseMove);
    window.addEventListener("mouseup", handleGlobalMouseUp);
    window.addEventListener("touchmove", handleGlobalTouchMove, { passive: true });
    window.addEventListener("touchend", handleGlobalTouchEnd);

    return () => {
      window.removeEventListener("mousemove", handleGlobalMouseMove);
      window.removeEventListener("mouseup", handleGlobalMouseUp);
      window.removeEventListener("touchmove", handleGlobalTouchMove);
      window.removeEventListener("touchend", handleGlobalTouchEnd);
    };
  }, [draggingNodeId, isPanning, nodeDragOffset, panStart, zoom, pan]);

  // Mouse pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    if (target.tagName === "svg" || target.tagName === "rect") {
      setIsPanning(true);
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    handlePointerMove(e.clientX, e.clientY);
  };

  const handleMouseUp = () => {
    handlePointerUp();
  };

  // Touch pan & pinch-zoom handlers
  const getTouchDistance = (t1: React.Touch, t2: React.Touch) => {
    const dx = t1.clientX - t2.clientX;
    const dy = t1.clientY - t2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      const dist = getTouchDistance(e.touches[0], e.touches[1]);
      setInitialPinchDistance(dist);
      setInitialPinchZoom(zoom);
      setIsPanning(false);
      setDraggingNodeId(null);
    } else if (e.touches.length === 1) {
      const t = e.touches[0];
      const target = e.target as HTMLElement;
      if (target.tagName === "svg" || target.tagName === "rect") {
        setIsPanning(true);
        setPanStart({ x: t.clientX - pan.x, y: t.clientY - pan.y });
      }
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (e.touches.length === 2 && initialPinchDistance !== null) {
      const dist = getTouchDistance(e.touches[0], e.touches[1]);
      const scale = dist / initialPinchDistance;
      const newZoom = Math.min(Math.max(initialPinchZoom * scale, 0.4), 2.5);
      setZoom(newZoom);
    } else if (e.touches.length === 1) {
      handlePointerMove(e.touches[0].clientX, e.touches[0].clientY);
    }
  };

  const handleTouchEnd = () => {
    handlePointerUp();
  };

  // Wheel zoom
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setZoom(prev => Math.min(Math.max(prev + delta, 0.4), 2.5));
  };

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 2.5));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.4));
  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setNodePositions({});
    onSelectNode(null);
    onSelectEdge(null);
  };

  if (!nodes || nodes.length === 0) {
    return (
      <div className="flex h-[520px] w-full flex-col items-center justify-center rounded-xl border border-white/10 bg-midnight/60 p-8 text-center backdrop-blur-md">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-white/40 mb-4 shadow-inner">
          <Layers className="h-8 w-8 animate-pulse text-brand/60" />
        </div>
        <h3 className="text-base font-semibold text-white/90">Knowledge Graph Canvas Ready</h3>
        <p className="mt-1 max-w-sm text-xs text-white/50">
          Enter an investigator query or select a crime record to visualize connected entities, weapons, vehicles, and multi-signal patterns.
        </p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        "overflow-hidden select-none transition-all duration-300",
        isFullscreen
          ? "fixed inset-0 z-[9999] h-screen w-screen rounded-none border-0 bg-[#050509]"
          : "relative h-[560px] w-full rounded-xl border border-white/10 bg-midnight/90 backdrop-blur-xl shadow-2xl"
      )}
      style={{ touchAction: "none" }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onWheel={handleWheel}
    >
      {/* Top Floating Controls */}
      <div className="absolute top-4 left-4 z-20 flex items-center gap-2 rounded-lg border border-white/10 bg-black/70 px-3 py-1.5 backdrop-blur-md">
        <div className="flex items-center gap-1.5 text-[0.7rem] font-mono font-bold text-white/80">
          <span className="h-2 w-2 rounded-full bg-brand animate-pulse" />
          <span>{layoutNodes.length} NODES</span>
          <span className="text-white/20">|</span>
          <span>{edges.length} EDGES</span>
        </div>
      </div>

      <div className="absolute top-4 right-4 z-20 flex items-center gap-1.5 rounded-lg border border-white/10 bg-black/70 p-1 backdrop-blur-md shadow-lg">
        <button
          onClick={handleZoomIn}
          title="Zoom In"
          className="rounded p-1.5 text-white/70 hover:bg-white/10 hover:text-white transition-colors"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
        <button
          onClick={handleZoomOut}
          title="Zoom Out"
          className="rounded p-1.5 text-white/70 hover:bg-white/10 hover:text-white transition-colors"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <button
          onClick={handleReset}
          title="Reset View"
          className="rounded p-1.5 text-white/70 hover:bg-white/10 hover:text-white transition-colors"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
        <div className="h-4 w-px bg-white/20 mx-0.5" />
        <button
          onClick={toggleFullscreen}
          title={isFullscreen ? "Exit Fullscreen (Esc)" : "Open in Full Screen"}
          className="rounded p-1.5 text-white/70 hover:bg-white/10 hover:text-white transition-colors group"
        >
          {isFullscreen ? (
            <Minimize2 className="h-4 w-4 text-purple-400 group-hover:scale-110 transition-transform" />
          ) : (
            <Maximize2 className="h-4 w-4 group-hover:scale-110 transition-transform" />
          )}
        </button>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-20 flex flex-wrap items-center gap-3 rounded-lg border border-white/10 bg-black/80 px-3 py-2 text-[0.65rem] font-mono text-white/70 backdrop-blur-md">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-purple-500" /> Crime
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-500" /> Location
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-amber-500" /> Vehicle
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-rose-500" /> Weapon
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-cyan-500" /> M.O.
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-blue-500" /> Cluster
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-orange-500" /> Pattern
        </div>
        <div className="h-3 w-px bg-white/20" />
        <div className="flex items-center gap-1.5 text-emerald-400" title="Investigator Validated / Explicit Fact">
          <span className="h-0.5 w-3 bg-emerald-400" /> Validated / Explicit
        </div>
        <div className="flex items-center gap-1.5 text-cyan-400" title="AI-Derived hypothesis pending review">
          <span className="h-0.5 w-3 border-b border-dashed border-cyan-400" /> AI-Derived (Pending)
        </div>
        <div className="flex items-center gap-1.5 text-indigo-400" title="Modified by investigator">
          <span className="h-0.5 w-3 bg-indigo-400" /> Modified
        </div>
        <div className="flex items-center gap-1.5 text-rose-400" title="Rejected during review">
          <span className="h-0.5 w-3 border-b border-dotted border-rose-400" /> Rejected
        </div>
      </div>

      {/* Main SVG Visualization */}
      <svg
        ref={svgRef}
        className={`h-full w-full ${isPanning ? "cursor-grabbing" : draggingNodeId ? "cursor-grabbing" : "cursor-grab"}`}
        style={{ touchAction: "none" }}
        viewBox="0 0 800 550"
      >
        <defs>
          <radialGradient id="grid-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#7c3aed" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#000000" stopOpacity="0" />
          </radialGradient>
          <pattern id="dot-grid" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1" fill="rgba(255,255,255,0.06)" />
          </pattern>
        </defs>

        {/* Ambient Grid Background */}
        <rect width="100%" height="100%" fill="url(#dot-grid)" />
        <rect width="100%" height="100%" fill="url(#grid-glow)" />

        <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
          {/* Edges Layer */}
          {edges.map((edge, idx) => {
            const srcNode = nodeMap.get(edge.source);
            const tgtNode = nodeMap.get(edge.target);
            if (!srcNode || !tgtNode) return null;

            const p = edge.properties || {};
            const st = p.status || (p.confidence_type === "explicit" ? "EXPLICIT" : "AI_DERIVED");
            const isSelected = selectedEdge === edge;

            let strokeColor = "rgba(34, 211, 238, 0.65)"; // AI-derived cyan
            let isDashed = true;
            let strokeWidth = isSelected ? 3.5 : 1.8;

            if (st === "VALIDATED" || st === "EXPLICIT") {
              strokeColor = "rgba(16, 185, 129, 0.85)";
              isDashed = false;
              strokeWidth = isSelected ? 3.5 : 2.2;
            } else if (st === "MODIFIED") {
              strokeColor = "rgba(99, 102, 241, 0.85)";
              isDashed = false;
              strokeWidth = isSelected ? 3.5 : 2.2;
            } else if (st === "REJECTED") {
              strokeColor = "rgba(244, 63, 94, 0.5)";
              isDashed = true;
              strokeWidth = isSelected ? 3.0 : 1.4;
            }

            const midX = (srcNode.x + tgtNode.x) / 2;
            const midY = (srcNode.y + tgtNode.y) / 2;

            return (
              <g
                key={`edge-${idx}`}
                className="cursor-pointer transition-all duration-200 hover:opacity-100"
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectEdge(edge);
                  onSelectNode(null);
                }}
              >
                <line
                  x1={srcNode.x}
                  y1={srcNode.y}
                  x2={tgtNode.x}
                  y2={tgtNode.y}
                  stroke={strokeColor}
                  strokeWidth={strokeWidth}
                  strokeDasharray={isDashed ? "5,4" : "none"}
                  className="transition-all hover:stroke-white"
                />

                {/* Subtle relation text badge */}
                <g transform={`translate(${midX}, ${midY})`}>
                  <rect
                    x="-28"
                    y="-8"
                    width="56"
                    height="16"
                    rx="4"
                    fill="#0f172a"
                    stroke={strokeColor}
                    strokeWidth="0.8"
                    opacity="0.9"
                  />
                  <text
                    textAnchor="middle"
                    dominantBaseline="central"
                    fill="#cbd5e1"
                    fontSize="7"
                    fontFamily="monospace"
                    fontWeight="bold"
                  >
                    {edge.relation.replace(/_/g, " ").slice(0, 10)}
                  </text>
                </g>
              </g>
            );
          })}

          {/* Nodes Layer */}
          {layoutNodes.map((node) => {
            const colors = getNodeColor(node.label);
            const isSelected = selectedNodeId === node.id;
            const isHovered = hoveredNodeId === node.id;
            const labelText = getNodeLabelText(node);
            const isCrime = node.label === "Crime";
            const radius = isCrime ? 24 : 18;

            const isHighlighted = Boolean(
              highlightedNodeIds?.has(node.id) ||
              (node.properties?.record_id && highlightedNodeIds?.has(node.properties.record_id)) ||
              (node.properties?.number && highlightedNodeIds?.has(node.properties.number)) ||
              (node.properties?.canonical_name && highlightedNodeIds?.has(node.properties.canonical_name)) ||
              (node.id.startsWith("crime:") && highlightedNodeIds?.has(node.id.replace("crime:", ""))) ||
              (node.id.startsWith("phone:") && highlightedNodeIds?.has(node.id.replace("phone:", ""))) ||
              (node.id.startsWith("person:") && highlightedNodeIds?.has(node.id.replace("person:", "")))
            );

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                className="cursor-grab active:cursor-grabbing select-none transition-opacity duration-200"
                style={{ touchAction: "none" }}
                onMouseDown={(e) => startNodeDrag(node, e.clientX, e.clientY, e)}
                onTouchStart={(e) => {
                  if (e.touches.length === 1) {
                    startNodeDrag(node, e.touches[0].clientX, e.touches[0].clientY, e);
                  }
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  if (!hasMovedDuringDrag) {
                    onSelectNode(node);
                    onSelectEdge(null);
                  }
                }}
                onMouseEnter={() => setHoveredNodeId(node.id)}
                onMouseLeave={() => setHoveredNodeId(null)}
              >
                {/* AI Discovery Beacon Ring */}
                {isHighlighted && (
                  <circle
                    r={radius + 12}
                    fill="none"
                    stroke="#22d3ee"
                    strokeWidth="2"
                    strokeDasharray="4,3"
                    className="animate-spin"
                    opacity="0.9"
                  />
                )}

                {/* Glow ring when selected or hovered */}
                {(isSelected || isHovered) && (
                  <circle
                    r={radius + 8}
                    fill="none"
                    stroke={colors.border}
                    strokeWidth="2.5"
                    opacity="0.8"
                    className="animate-pulse"
                  />
                )}

                {/* Base Node Circle */}
                <circle
                  r={radius}
                  fill={colors.bg}
                  stroke={colors.border}
                  strokeWidth={isSelected ? 3 : 1.5}
                  style={{ filter: "drop-shadow(0 4px 12px rgba(0,0,0,0.5))" }}
                />

                {/* Centered Node Icon */}
                <g transform="translate(-7, -7)" fill={colors.text} color={colors.text}>
                  {getNodeIcon(node.label)}
                </g>

                {/* Label text pill below node */}
                <g transform={`translate(0, ${radius + 12})`}>
                  <rect
                    x={-(labelText.length * 3.8 + 10)}
                    y="-9"
                    width={labelText.length * 7.6 + 20}
                    height="18"
                    rx="5"
                    fill="rgba(15, 23, 42, 0.92)"
                    stroke={colors.border}
                    strokeWidth="0.8"
                  />
                  <text
                    textAnchor="middle"
                    dominantBaseline="central"
                    fill={colors.text}
                    fontSize="8.5"
                    fontWeight="bold"
                    fontFamily="monospace"
                  >
                    {labelText.length > 20 ? `${labelText.slice(0, 18)}…` : labelText}
                  </text>
                </g>
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}
