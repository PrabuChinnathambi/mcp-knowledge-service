import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FolderGit2, FileText, Layers, Plus, ExternalLink, ShieldCheck } from "lucide-react";
import { api, type DocumentItem } from "../services/api";
import { useApp } from "../context/AppContext";

export const KnowledgeBases: React.FC = () => {
  const { workspaces, setCurrentWorkspace } = useApp();
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    api.getDocuments()
      .then((data) => setDocs(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Knowledge Bases</h1>
          <p className="text-sm text-slate-500 mt-1">
            Isolated multi-tenant workspaces with role-based access control and separate vector namespaces.
          </p>
        </div>
        <Link
          to="/documents"
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-indigo-700 transition shadow-xs"
        >
          <Plus className="h-4 w-4" />
          Add Documents
        </Link>
      </div>

      {/* Grid of Workspaces */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {workspaces.map((ws) => {
          const wsDocs = docs.filter((d) => d.workspace_id === ws);
          const totalChunks = wsDocs.reduce((acc, d) => acc + d.chunks_count, 0);

          return (
            <div
              key={ws}
              className="flex flex-col justify-between rounded-xl border border-slate-200/80 bg-white p-6 shadow-2xs hover:shadow-xs transition"
            >
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
                    <FolderGit2 className="h-5 w-5" />
                  </div>
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200/60">
                    <ShieldCheck className="h-3 w-3" />
                    RBAC Active
                  </span>
                </div>

                <h3 className="mt-4 text-base font-bold text-slate-900 capitalize tracking-tight">{ws}</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Isolated workspace namespace for {ws} documentation, runbooks, and policies.
                </p>

                <div className="mt-6 grid grid-cols-2 gap-3 border-t border-slate-100 pt-4 text-xs">
                  <div>
                    <span className="text-[11px] text-slate-400 uppercase tracking-wider">Documents</span>
                    <div className="mt-1 flex items-center gap-1.5 font-bold text-slate-900">
                      <FileText className="h-3.5 w-3.5 text-slate-400" />
                      {loading ? "..." : wsDocs.length}
                    </div>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-400 uppercase tracking-wider">Vector Chunks</span>
                    <div className="mt-1 flex items-center gap-1.5 font-bold text-slate-900">
                      <Layers className="h-3.5 w-3.5 text-indigo-400" />
                      {loading ? "..." : totalChunks}
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex items-center gap-2 border-t border-slate-100 pt-4">
                <Link
                  to="/chat"
                  onClick={() => setCurrentWorkspace(ws)}
                  className="flex-1 text-center rounded-lg bg-slate-900 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition"
                >
                  Chat in {ws}
                </Link>
                <Link
                  to="/search"
                  onClick={() => setCurrentWorkspace(ws)}
                  className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition"
                  title="Search Workspace"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
