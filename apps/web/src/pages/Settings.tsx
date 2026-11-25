import React, { useEffect, useState } from "react";
import { Settings as SettingsIcon, Database, Cpu, HardDrive, Network, ExternalLink, CheckCircle2 } from "lucide-react";
import { api, type OverviewResponse } from "../services/api";

export const Settings: React.FC = () => {
  const [stats, setStats] = useState<OverviewResponse | null>(null);
  const [models, setModels] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([api.getOverviewStats(), api.getModels()])
      .then(([s, m]) => {
        setStats(s);
        setModels(m);
      })
      .catch((e) => console.error(e));
  }, []);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">System Settings & Infrastructure</h1>
        <p className="text-sm text-slate-500 mt-1">
          Configuration telemetry for offline local LLMs, vector database connections, and API gateways.
        </p>
      </div>

      {/* Infrastructure Telemetry */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-2xs space-y-6">
        <h2 className="text-base font-semibold text-slate-900">Connected Services</h2>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {/* PostgreSQL */}
          <div className="rounded-xl border border-slate-200/80 p-4 bg-slate-50/50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <div className="font-semibold text-sm text-slate-900">PostgreSQL Vector Store</div>
                <div className="text-xs text-slate-500">Port 5432 • pgvector v0.8.7 • HNSW Index</div>
              </div>
            </div>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Connected
            </span>
          </div>

          {/* Redis */}
          <div className="rounded-xl border border-slate-200/80 p-4 bg-slate-50/50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-rose-100 text-rose-700">
                <Network className="h-5 w-5" />
              </div>
              <div>
                <div className="font-semibold text-sm text-slate-900">Redis Broker & SlowAPI Limiter</div>
                <div className="text-xs text-slate-500">Port 6379 • Fixed-Window Rate Limiting</div>
              </div>
            </div>
            <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
              stats?.services.redis === "online" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
            }`}>
              <CheckCircle2 className="h-3.5 w-3.5" />
              {stats?.services.redis === "online" ? "Connected" : "Memory Fallback"}
            </span>
          </div>

          {/* Ollama */}
          <div className="rounded-xl border border-slate-200/80 p-4 bg-slate-50/50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100 text-purple-700">
                <Cpu className="h-5 w-5" />
              </div>
              <div>
                <div className="font-semibold text-sm text-slate-900">Ollama Local Engine</div>
                <div className="text-xs text-slate-500">Port 11434 • GPU Acceleration Enabled</div>
              </div>
            </div>
            <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
              stats?.services.ollama === "online" ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
            }`}>
              <CheckCircle2 className="h-3.5 w-3.5" />
              {stats?.services.ollama === "online" ? "Operational" : "Offline"}
            </span>
          </div>

          {/* MinIO */}
          <div className="rounded-xl border border-slate-200/80 p-4 bg-slate-50/50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
                <HardDrive className="h-5 w-5" />
              </div>
              <div>
                <div className="font-semibold text-sm text-slate-900">Object Storage (MinIO)</div>
                <div className="text-xs text-slate-500">Port 9000 • S3 API • Local Staging Fallback</div>
              </div>
            </div>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Ready
            </span>
          </div>
        </div>
      </div>

      {/* Available Local Models */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-2xs space-y-4">
        <h2 className="text-base font-semibold text-slate-900">Integrated Offline Models</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-lg border border-slate-200 p-4">
            <div className="text-xs font-semibold uppercase text-indigo-600">Default Model</div>
            <div className="text-sm font-bold text-slate-900 mt-1">qwen2.5:7b-instruct</div>
            <div className="text-xs text-slate-500 mt-0.5">High precision instruction following & strict JSON output</div>
          </div>
          <div className="rounded-lg border border-slate-200 p-4">
            <div className="text-xs font-semibold uppercase text-blue-600">Fast Model</div>
            <div className="text-sm font-bold text-slate-900 mt-1">llama3.2:3b</div>
            <div className="text-xs text-slate-500 mt-0.5">Ultra-low latency inference for edge compute</div>
          </div>
          <div className="rounded-lg border border-slate-200 p-4">
            <div className="text-xs font-semibold uppercase text-purple-600">Reasoning Model</div>
            <div className="text-sm font-bold text-slate-900 mt-1">deepseek-r1:1.5b</div>
            <div className="text-xs text-slate-500 mt-0.5">Deep chain-of-thought analysis for complex queries</div>
          </div>
        </div>
      </div>

      {/* API Documentation Link */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-2xs flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Interactive Swagger REST Documentation</h2>
          <p className="text-xs text-slate-500 mt-1">
            Access the complete OpenAPI schema, testing sandbox, and documentation at <code className="text-indigo-600 font-mono">http://localhost:8000/docs</code>
          </p>
        </div>
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700 transition"
        >
          Open Swagger UI
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>
    </div>
  );
};
