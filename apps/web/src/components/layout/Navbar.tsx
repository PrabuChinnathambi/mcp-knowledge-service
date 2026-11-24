import React from "react";
import { FolderGit2, Activity, Cpu, Layers } from "lucide-react";
import { useApp } from "../../context/AppContext";

export const Navbar: React.FC = () => {
  const { currentWorkspace, workspaces, setCurrentWorkspace, backendOnline } = useApp();

  return (
    <header className="sticky top-0 z-10 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white/80 px-6 backdrop-blur-md">
      {/* Workspace Selector */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50/50 px-3 py-1.5 shadow-2xs">
          <FolderGit2 className="h-4 w-4 text-indigo-600" />
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Workspace:</span>
          <select
            value={currentWorkspace}
            onChange={(e) => setCurrentWorkspace(e.target.value)}
            className="cursor-pointer bg-transparent text-sm font-semibold text-slate-800 focus:outline-none"
          >
            {workspaces.map((ws) => (
              <option key={ws} value={ws}>
                {ws}
              </option>
            ))}
          </select>
        </div>

        <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-500 bg-slate-100/60 rounded-full px-2.5 py-1">
          <Layers className="h-3 w-3 text-slate-400" />
          <span>768-dim Vectors (nomic-embed-text)</span>
        </div>
      </div>

      {/* Right Status Controls */}
      <div className="flex items-center gap-3">
        {/* Model Indicator */}
        <div className="hidden md:flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white shadow-2xs">
          <Cpu className="h-3.5 w-3.5 text-indigo-500" />
          <span>Local Model:</span>
          <span className="font-semibold text-slate-900">qwen2.5:7b-instruct</span>
        </div>

        {/* System Health Badge */}
        <div
          className={`flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium transition ${
            backendOnline
              ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
              : "bg-rose-50 text-rose-700 border border-rose-200/60"
          }`}
        >
          <span className="relative flex h-2 w-2">
            <span
              className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${
                backendOnline ? "bg-emerald-400" : "bg-rose-400"
              }`}
            />
            <span
              className={`relative inline-flex h-2 w-2 rounded-full ${
                backendOnline ? "bg-emerald-500" : "bg-rose-500"
              }`}
            />
          </span>
          <Activity className="h-3.5 w-3.5" />
          <span>{backendOnline ? "Gateway Online" : "Gateway Offline"}</span>
        </div>
      </div>
    </header>
  );
};
