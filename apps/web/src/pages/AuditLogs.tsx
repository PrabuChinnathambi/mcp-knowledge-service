import React, { useEffect, useState } from "react";
import { ScrollText, RefreshCw, CheckCircle2, Clock, User, AlertCircle, ChevronDown, ChevronUp } from "lucide-react";
import { api, type AuditLog } from "../services/api";

export const AuditLogs: React.FC = () => {
  const [traces, setTraces] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [expandedTraceId, setExpandedTraceId] = useState<string | null>(null);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditLogs(50);
      setTraces(data);
    } catch (err: any) {
      console.error("Failed to load audit logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Audit Logs & Execution Traces</h1>
          <p className="text-sm text-slate-500 mt-1">
            Complete telemetry of all RAG questions, retrieval queries, citations, and execution latency.
          </p>
        </div>
        <button
          onClick={loadLogs}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 transition cursor-pointer"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Traces Table */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-2xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="pb-3">Trace ID</th>
                <th className="pb-3">Query</th>
                <th className="pb-3">Workspace</th>
                <th className="pb-3">User</th>
                <th className="pb-3">Latency</th>
                <th className="pb-3">Status</th>
                <th className="pb-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {traces.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No execution traces recorded yet.
                  </td>
                </tr>
              ) : (
                traces.map((trace) => {
                  const isExpanded = expandedTraceId === trace.trace_id;
                  return (
                    <React.Fragment key={trace.trace_id}>
                      <tr className="hover:bg-slate-50/50 transition">
                        <td className="py-3.5 font-mono text-[11px] font-medium text-indigo-600">
                          {trace.trace_id}
                        </td>
                        <td className="py-3.5 font-medium text-slate-900 max-w-xs truncate">
                          {trace.query_text}
                        </td>
                        <td className="py-3.5">
                          <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600">
                            {trace.workspace_id}
                          </span>
                        </td>
                        <td className="py-3.5 text-slate-600 flex items-center gap-1.5">
                          <User className="h-3 w-3 text-slate-400" />
                          {trace.user_id}
                        </td>
                        <td className="py-3.5 text-slate-500 font-mono">
                          {trace.latency_ms} ms
                        </td>
                        <td className="py-3.5">
                          <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                            trace.status === "answered"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200/50"
                              : "bg-rose-50 text-rose-700 border border-rose-200/50"
                          }`}>
                            {trace.status === "answered" ? (
                              <CheckCircle2 className="h-3 w-3" />
                            ) : (
                              <AlertCircle className="h-3 w-3" />
                            )}
                            {trace.status}
                          </span>
                        </td>
                        <td className="py-3.5 text-right">
                          <button
                            onClick={() => setExpandedTraceId(isExpanded ? null : trace.trace_id)}
                            className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 transition cursor-pointer"
                          >
                            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                          </button>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan={7} className="bg-slate-50 p-4">
                            <pre className="text-[11px] font-mono text-slate-800 bg-white p-3 rounded-lg border border-slate-200 overflow-x-auto max-h-60">
                              {JSON.stringify(trace.data, null, 2)}
                            </pre>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
