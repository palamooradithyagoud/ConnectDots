"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import Image from "next/image";
import AgenticBall from "@/components/ui/agentic-ball";
import {
  executeAgentInvestigation,
  fetchAgentExamples,
  fetchAgentTools,
  AgentInvestigationResponse,
  AgentExampleItem,
  AgentToolDefinition,
} from "@/lib/agent-api";
import {
  Bot,
  Send,
  Loader2,
  Sparkles,
  FileText,
  ShieldAlert,
  Database,
  Search,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Terminal,
  Share2,
  Users,
  Tag,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatMessage {
  id: string;
  sender: "user" | "agent";
  text?: string;
  response?: AgentInvestigationResponse;
  timestamp: string;
  error?: string;
}

export default function AIAgentPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [examples, setExamples] = useState<AgentExampleItem[]>([]);
  const [tools, setTools] = useState<AgentToolDefinition[]>([]);
  const [showToolsDrawer, setShowToolsDrawer] = useState(false);
  const [expandedTraces, setExpandedTraces] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Load real examples and tools on mount
  useEffect(() => {
    fetchAgentExamples().then((data) => {
      if (data.length > 0) {
        setExamples(data);
      } else {
        // Fallback default domain questions matching the database
        setExamples([
          {
            title: "Robbery & Theft Records",
            scenario: "Case Search",
            question: "Find all criminal records related to Robbery or Theft.",
          },
          {
            title: "Cyber Fraud Investigation",
            scenario: "Case Search",
            question: "Search for all cases involving Cyber Fraud.",
          },
          {
            title: "Key Individuals & Centrality",
            scenario: "Graph Analysis",
            question: "Who are the structurally central individuals across registered cases?",
          },
          {
            title: "Phone & CDR Linkage",
            scenario: "Telecom Analysis",
            question: "Find criminal cases connected through shared phone numbers.",
          },
        ]);
      }
    });

    fetchAgentTools().then((data) => {
      setTools(data);
    });
  }, []);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const toggleTrace = (id: string) => {
    setExpandedTraces((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleSend = async (queryText?: string) => {
    const textToSend = (queryText || inputQuery).trim();
    if (!textToSend || isLoading) return;

    const userMessageId = `user-${Date.now()}`;
    const agentMessageId = `agent-${Date.now()}`;

    const newMessages: ChatMessage[] = [
      ...messages,
      {
        id: userMessageId,
        sender: "user",
        text: textToSend,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ];

    setMessages(newMessages);
    setInputQuery("");
    setIsLoading(true);

    try {
      const response = await executeAgentInvestigation(textToSend);
      setMessages((prev) => [
        ...prev,
        {
          id: agentMessageId,
          sender: "agent",
          response,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } catch (err: any) {
      console.error("Agent error:", err);
      setMessages((prev) => [
        ...prev,
        {
          id: agentMessageId,
          sender: "agent",
          error: err.message || "Failed to query the criminal records database. Please try again.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setInputQuery("");
  };

  return (
    <div className="min-h-[calc(100vh-5rem)] flex flex-col gap-4 text-slate-100 max-w-5xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.08] pb-4">
        <div className="flex items-center gap-3">
          <div className="relative p-1.5 rounded-xl bg-purple-950/40 border border-purple-500/30 shrink-0">
            <Image
              src="/logo.png"
              alt="ConnectDots Logo"
              width={34}
              height={34}
              className="h-8 w-8 object-contain drop-shadow-[0_0_10px_rgba(168,85,247,0.4)]"
            />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-white tracking-tight">
                AI Criminal Records Investigation Agent
              </h1>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[0.62rem] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                Live Database
              </span>
            </div>
            <p className="text-xs text-white/50">
              Direct criminal records investigation via SQL, Neo4j Knowledge Graph, and Telecom CDR
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {tools.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowToolsDrawer(!showToolsDrawer)}
              className="text-xs border-white/10 bg-white/[0.04] text-white/70 hover:text-white"
            >
              <Terminal className="h-3.5 w-3.5 mr-1.5 text-purple-400" />
              {tools.length} Investigation Tools
            </Button>
          )}

          {messages.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearChat}
              className="text-xs text-white/50 hover:text-white"
            >
              <RotateCcw className="h-3.5 w-3.5 mr-1.5" />
              New Query
            </Button>
          )}
        </div>
      </div>

      {/* Tools List Accordion Drawer (when toggled) */}
      {showToolsDrawer && tools.length > 0 && (
        <div className="rounded-xl border border-purple-500/30 bg-[#0c0c18] p-4 text-xs">
          <div className="flex items-center justify-between mb-3 border-b border-white/[0.06] pb-2">
            <span className="font-mono text-purple-300 font-bold uppercase tracking-wider">
              Connected Backend Investigation Tools ({tools.length})
            </span>
            <button
              onClick={() => setShowToolsDrawer(false)}
              className="text-white/40 hover:text-white text-xs"
            >
              Close
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-48 overflow-y-auto pr-1">
            {tools.map((t) => (
              <div
                key={t.name}
                className="p-2 rounded bg-white/[0.02] border border-white/[0.04] flex flex-col gap-0.5"
              >
                <span className="font-mono font-bold text-white text-[0.72rem]">{t.name}</span>
                <span className="text-[0.68rem] text-white/50 line-clamp-2">{t.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Conversation Canvas */}
      <div className="flex-1 flex flex-col gap-4">
        {/* Empty State: Prompt Suggestions */}
        {messages.length === 0 && !isLoading && (
          <div className="flex-1 flex flex-col items-center justify-center py-10 px-4 text-center">
            <div className="p-4 rounded-2xl bg-[#0e0e1a] border border-purple-500/25 mb-4 shadow-[0_0_40px_rgba(168,85,247,0.25)] flex items-center justify-center">
              <Image
                src="/logo.png"
                alt="ConnectDots Logo"
                width={84}
                height={84}
                className="h-20 w-20 object-contain drop-shadow-[0_0_25px_rgba(168,85,247,0.45)]"
                priority
              />
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Ask anything about the criminal records
            </h2>
            <p className="text-xs text-white/50 max-w-md mt-1 leading-relaxed">
              Ask natural language questions to search FIR records, examine suspect linkages, trace CDR towers, or analyze criminal patterns.
            </p>

            {/* Example Queries */}
            <div className="mt-6 w-full max-w-2xl flex flex-col gap-2">
              <div className="text-[0.68rem] uppercase font-mono tracking-wider text-white/40 text-left">
                Suggested Investigation Questions:
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
                {examples.slice(0, 4).map((ex, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(ex.question)}
                    className="p-3 rounded-xl border border-white/[0.08] bg-white/[0.02] hover:bg-purple-600/10 hover:border-purple-500/40 transition-all text-left flex flex-col gap-1 group cursor-pointer"
                  >
                    <div className="flex items-center justify-between text-[0.65rem] font-mono text-purple-300">
                      <span>{ex.title}</span>
                      <Sparkles className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    <div className="text-xs text-white/80 group-hover:text-white font-medium">
                      "{ex.question}"
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Message Stream */}
        {messages.map((msg) => (
          <div key={msg.id} className="flex flex-col gap-2">
            {/* User Message */}
            {msg.sender === "user" && (
              <div className="flex justify-end">
                <div className="max-w-2xl rounded-2xl bg-gradient-to-r from-purple-700 to-indigo-700 text-white px-4 py-3 shadow-md">
                  <div className="text-xs font-mono text-white/70 mb-1">Investigation Query</div>
                  <div className="text-sm font-medium leading-relaxed whitespace-pre-wrap">
                    {msg.text}
                  </div>
                  <div className="text-[0.62rem] text-white/60 text-right mt-1 font-mono">
                    {msg.timestamp}
                  </div>
                </div>
              </div>
            )}

            {/* Agent Message */}
            {msg.sender === "agent" && (
              <div className="flex flex-col gap-3 rounded-2xl border border-white/[0.08] bg-[#0c0c16] p-5 shadow-lg">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-1 rounded-lg bg-purple-950/40 border border-purple-500/30 shrink-0">
                      <Image
                        src="/logo.png"
                        alt="ConnectDots Logo"
                        width={20}
                        height={20}
                        className="h-5 w-5 object-contain"
                      />
                    </div>
                    <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                      ConnectDots Investigation Briefing
                    </span>
                  </div>

                  {msg.response && (
                    <div className="flex items-center gap-3 text-[0.68rem] font-mono text-white/40">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {msg.response.total_duration_ms.toFixed(0)} ms
                      </span>
                      <span className="px-2 py-0.5 rounded bg-white/[0.04] text-purple-300">
                        {msg.response.evidence.length} Evidence Records
                      </span>
                    </div>
                  )}
                </div>

                {/* Error State */}
                {msg.error && (
                  <div className="p-3 rounded-lg bg-red-950/20 border border-red-500/30 text-red-400 text-xs flex items-start gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                    <div>{msg.error}</div>
                  </div>
                )}

                {/* Response Content */}
                {msg.response && (
                  <div className="flex flex-col gap-4">
                    {/* Summary */}
                    <div className="text-sm text-slate-200 leading-relaxed font-sans whitespace-pre-line">
                      {msg.response.summary}
                    </div>

                    {/* Findings Cards (if any) */}
                    {msg.response.findings && msg.response.findings.length > 0 && (
                      <div className="flex flex-col gap-2 pt-2">
                        <div className="text-[0.68rem] font-mono uppercase tracking-wider text-purple-300 flex items-center gap-1.5">
                          <CheckCircle2 className="h-3 w-3" />
                          Key Findings ({msg.response.findings.length})
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                          {msg.response.findings.map((f, idx) => (
                            <div
                              key={idx}
                              className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 flex flex-col gap-1"
                            >
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-bold text-white">{f.title}</span>
                                {f.validation_status && (
                                  <span className="text-[0.6rem] font-mono px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                                    {f.validation_status}
                                  </span>
                                )}
                              </div>
                              <p className="text-[0.72rem] text-white/60 leading-relaxed">
                                {f.details}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Key Individuals (if any) */}
                    {msg.response.key_individuals && msg.response.key_individuals.length > 0 && (
                      <div className="flex flex-col gap-2 pt-2">
                        <div className="text-[0.68rem] font-mono uppercase tracking-wider text-amber-300 flex items-center gap-1.5">
                          <Users className="h-3 w-3" />
                          Key Individuals ({msg.response.key_individuals.length})
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                          {msg.response.key_individuals.map((ind, idx) => (
                            <div
                              key={idx}
                              className="rounded-xl border border-amber-500/20 bg-amber-950/10 p-2.5 flex flex-col gap-1"
                            >
                              <span className="text-xs font-bold text-white">
                                {ind.display_name}
                              </span>
                              <div className="flex items-center gap-2 text-[0.65rem] font-mono text-amber-400">
                                <span>Degree: {ind.degree_centrality?.toFixed(2)}</span>
                                <span>PR: {ind.pagerank?.toFixed(2)}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Verifiable Evidence Items */}
                    {msg.response.evidence && msg.response.evidence.length > 0 && (
                      <div className="flex flex-col gap-2 pt-2">
                        <div className="text-[0.68rem] font-mono uppercase tracking-wider text-white/40 flex items-center gap-1.5">
                          <Database className="h-3 w-3" />
                          Corroborated Database Records ({msg.response.evidence.length})
                        </div>
                        <div className="flex flex-col gap-1.5 max-h-48 overflow-y-auto pr-1">
                          {msg.response.evidence.map((ev, idx) => (
                            <div
                              key={idx}
                              className="rounded-lg bg-black/40 border border-white/[0.04] p-2 text-xs flex items-start justify-between gap-2"
                            >
                              <div className="flex items-start gap-2">
                                <span className="px-1.5 py-0.5 rounded text-[0.6rem] font-mono uppercase bg-white/[0.06] text-white/60 shrink-0 mt-0.5">
                                  {ev.evidence_type}
                                </span>
                                <span className="text-white/80 text-xs leading-snug">
                                  {ev.summary}
                                </span>
                              </div>
                              <span className="text-[0.6rem] font-mono text-purple-300/80 shrink-0">
                                {ev.source_system}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Tool Execution Trace (Expandable) */}
                    {msg.response.tool_trace && msg.response.tool_trace.length > 0 && (
                      <div className="border-t border-white/[0.06] pt-2">
                        <button
                          type="button"
                          onClick={() => toggleTrace(msg.id)}
                          className="flex items-center gap-1.5 text-[0.68rem] font-mono text-white/40 hover:text-white transition-colors cursor-pointer"
                        >
                          {expandedTraces[msg.id] ? (
                            <ChevronUp className="h-3 w-3" />
                          ) : (
                            <ChevronDown className="h-3 w-3" />
                          )}
                          <span>
                            Tool Execution Trace ({msg.response.tool_trace.length} tools executed in{" "}
                            {msg.response.total_duration_ms.toFixed(0)}ms)
                          </span>
                        </button>

                        {expandedTraces[msg.id] && (
                          <div className="mt-2 flex flex-col gap-1.5 font-mono text-xs bg-black/50 p-3 rounded-lg border border-white/[0.04]">
                            {msg.response.tool_trace.map((t, idx) => (
                              <div
                                key={idx}
                                className="flex items-center justify-between text-[0.7rem] text-white/70"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="text-purple-400 font-bold">{t.tool}</span>
                                  <span className="text-white/40">({t.purpose})</span>
                                </div>
                                <div className="flex items-center gap-2 text-white/50">
                                  <span>{t.result_count} results</span>
                                  <span>{t.duration_ms.toFixed(1)}ms</span>
                                  <span
                                    className={`px-1 rounded text-[0.6rem] ${
                                      t.status === "SUCCESS"
                                        ? "text-emerald-400 bg-emerald-950/30"
                                        : "text-amber-400 bg-amber-950/30"
                                    }`}
                                  >
                                    {t.status}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-center gap-3 rounded-2xl border border-purple-500/30 bg-[#0c0c16] p-4">
            <Loader2 className="h-5 w-5 text-purple-400 animate-spin" />
            <div className="flex flex-col">
              <span className="text-xs font-bold text-white">
                Querying Criminal Records Database...
              </span>
              <span className="text-[0.68rem] text-white/50 font-mono">
                Running classification, allowlisted tools, and evidence synthesis
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Query Input Bar */}
      <div className="sticky bottom-4 rounded-2xl border border-white/10 bg-[#0c0c18]/95 backdrop-blur-md p-3 shadow-2xl">
        <div className="flex items-end gap-2">
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask any question about criminal records (e.g., 'Find all cases of robbery', 'Who are the central suspects?')..."
            className="flex-1 bg-transparent text-sm text-white placeholder:text-white/30 focus:outline-none resize-none max-h-32 py-1.5 px-2 leading-relaxed font-sans"
          />
          <Button
            onClick={() => handleSend()}
            disabled={!inputQuery.trim() || isLoading}
            size="sm"
            className="rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs px-4 h-9 shrink-0 shadow-brand-glow disabled:opacity-40"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
        <div className="flex items-center justify-between text-[0.62rem] text-white/40 pt-2 px-1 font-mono">
          <span>Press Enter to send, Shift+Enter for newline</span>
          <span>16 safe read-only tools active</span>
        </div>
      </div>
    </div>
  );
}
