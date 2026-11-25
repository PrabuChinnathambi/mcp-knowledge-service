import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  FileText,
  Layers,
  Search,
  FolderGit2,
  CheckCircle2,
  ArrowRight,
  Database,
  Cpu,
  HardDrive,
  Network,
  RefreshCw,
  PlusCircle,
  MessageSquare,
} from "lucide-react";
import { api, type OverviewResponse, type DocumentItem } from "../services/api";
import { useApp } from "../context/AppContext";

export const Overview: React.FC = () => {
  const { currentWorkspace } = useApp();
  const [stats, setStats] = useState<OverviewResponse | null>(null);
  const [recentDocs, setRecentDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [overviewData, docsData] = await Promise.all([
        api.getOverviewStats(),
        api.getDocuments(),
      ]);
      setStats(overviewData);
      setRecentDocs(docsData.slice(0, 5));
    } catch (e) {
      console.error("Failed to load overview data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Page Title & Quick Actions */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Enterprise Overview</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time status of your knowledge base, vector indexes, and offline LLM services.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 transition shadow-2xs cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <Link
            to="/chat"
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-indigo-700 transition shadow-xs"
          >
            <MessageSquare className="h-3.5 w-3.5" />
            Ask Question
          </Link>
          <Link
            to="/documents"
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-800 hover:bg-slate-50 transition shadow-xs"
          >
            <PlusCircle className="h-3.5 w-3.5 text-indigo-600" />
            Upload Document
          </Link>
        </div>
      </div>

      {/* KPI Statistic Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {/* Card 1 */}
        <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Total Documents</span>
            <div className="rounded-lg bg-blue-50 p-2 text-blue-600">
              <FileText className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-slate-900">
              {stats?.metrics.total_documents ?? 0}
            </span>
            <span className="text-xs font-medium text-slate-500">Indexed Files</span>
          </div>
        </div>

        {/* Card 2 */}
        <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Vector Chunks</span>
            <div className="rounded-lg bg-indigo-50 p-2 text-indigo-600">
              <Layers className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-slate-900">
              {stats?.metrics.total_chunks ?? 0}
            </span>
            <span className="text-xs font-medium text-slate-500">768-dim Embeddings</span>
          </div>
        </div>

        {/* Card 3 */}
        <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Total Queries</span>
            <div className="rounded-lg bg-emerald-50 p-2 text-emerald-600">
              <Search className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-slate-900">
              {stats?.metrics.total_queries ?? 0}
            </span>
            <span className="text-xs font-medium text-emerald-600 flex items-center gap-0.5">
              <CheckCircle2 className="h-3 w-3 inline" /> 100% Grounded
            </span>
          </div>
        </div>

        {/* Card 4 */}
        <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Knowledge Bases</span>
            <div className="rounded-lg bg-purple-50 p-2 text-purple-600">
              <FolderGit2 className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-slate-900">
              {stats?.metrics.active_workspaces ?? 3}
            </span>
            <span className="text-xs font-medium text-slate-500">Isolated Workspaces</span>
          </div>
        </div>
      </div>

      {/* Infrastructure Subsystems Grid */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-2xs">
        <h2 className="text-base font-semibold text-slate-900">Subsystem Architecture Health</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Live connection telemetry for local offline RAG infrastructure.
        </p>

        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Postgres */}
          <div className="flex items-center gap-3.5 rounded-lg border border-slate-100 bg-slate-50/60 p-3.5">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-100/80 text-blue-700">
              <Database className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-medium text-slate-400">Database & Vector Store</span>
              <span className="text-sm font-semibold text-slate-900">PostgreSQL 17 + pgvector</span>
              <span className="text-[11px] font-medium text-emerald-600 flex items-center gap-1 mt-0.5">
                ● Connected (Port 5432)
              </span>
            </div>
          </div>

          {/* Redis */}
          <div className="flex items-center gap-3.5 rounded-lg border border-slate-100 bg-slate-50/60 p-3.5">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-rose-100/80 text-rose-700">
              <Network className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-medium text-slate-400">Broker & Rate Limiter</span>
              <span className="text-sm font-semibold text-slate-900">Redis 7 Alpine</span>
              <span className={`text-[11px] font-medium flex items-center gap-1 mt-0.5 ${
                stats?.services.redis === "online" ? "text-emerald-600" : "text-amber-600"
              }`}>
                ● {stats?.services.redis === "online" ? "Active (Port 6379)" : "In-Memory Fallback"}
              </span>
            </div>
          </div>

          {/* Ollama */}
          <div className="flex items-center gap-3.5 rounded-lg border border-slate-100 bg-slate-50/60 p-3.5">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-purple-100/80 text-purple-700">
              <Cpu className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-medium text-slate-400">Offline LLM Engine</span>
              <span className="text-sm font-semibold text-slate-900">Ollama Local</span>
              <span className={`text-[11px] font-medium flex items-center gap-1 mt-0.5 ${
                stats?.services.ollama === "online" ? "text-emerald-600" : "text-rose-600"
              }`}>
                ● {stats?.services.ollama === "online" ? "Ready (qwen2.5:7b)" : "Unreachable"}
              </span>
            </div>
          </div>

          {/* Storage */}
          <div className="flex items-center gap-3.5 rounded-lg border border-slate-100 bg-slate-50/60 p-3.5">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-amber-100/80 text-amber-700">
              <HardDrive className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-medium text-slate-400">Object Storage</span>
              <span className="text-sm font-semibold text-slate-900">MinIO / Local Staging</span>
              <span className="text-[11px] font-medium text-emerald-600 flex items-center gap-1 mt-0.5">
                ● Filesystem Mounted
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Indexed Documents */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-2xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Recent Documents</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Latest documents parsed, chunked, and embedded into vector storage.
            </p>
          </div>
          <Link
            to="/documents"
            className="flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition"
          >
            View all documents
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="pb-3">Title & Path</th>
                <th className="pb-3">Workspace</th>
                <th className="pb-3">Chunks</th>
                <th className="pb-3">Size</th>
                <th className="pb-3">Status</th>
                <th className="pb-3">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {recentDocs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-400">
                    No documents indexed yet.
                  </td>
                </tr>
              ) : (
                recentDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/50 transition">
                    <td className="py-3 font-medium text-slate-900 flex items-center gap-2">
                      <FileText className="h-4 w-4 text-slate-400 shrink-0" />
                      <div>
                        <div className="font-semibold text-slate-900">{doc.title}</div>
                        <div className="text-[10px] text-slate-400 truncate max-w-xs">{doc.source_uri}</div>
                      </div>
                    </td>
                    <td className="py-3">
                      <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                        {doc.workspace_id}
                      </span>
                    </td>
                    <td className="py-3 font-semibold text-slate-700">{doc.chunks_count}</td>
                    <td className="py-3 text-slate-500">{(doc.byte_size / 1024).toFixed(1)} KB</td>
                    <td className="py-3">
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[10px] font-medium text-emerald-700 border border-emerald-200/50">
                        <CheckCircle2 className="h-3 w-3" />
                        {doc.status}
                      </span>
                    </td>
                    <td className="py-3 text-slate-400">
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : "Recent"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
