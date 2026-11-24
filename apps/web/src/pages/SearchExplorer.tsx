import React, { useState } from "react";
import { Search, Layers, Database, ChevronDown, ChevronUp, Sparkles, Filter } from "lucide-react";
import { api, type SearchChunk } from "../services/api";
import { useApp } from "../context/AppContext";

export const SearchExplorer: React.FC = () => {
  const { currentWorkspace, setCurrentWorkspace, workspaces } = useApp();
  const [query, setQuery] = useState<string>("probation remote work policy");
  const [results, setResults] = useState<SearchChunk[]>([]);
  const [topScore, setTopScore] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const data = await api.search(query, currentWorkspace, 10);
      setResults(data.results);
      setTopScore(data.top_vector_score);
    } catch (err: any) {
      console.error("Search failed", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Search Explorer</h1>
        <p className="text-sm text-slate-500 mt-1">
          Inspect the hybrid retrieval engine combining dense vector cosine similarity (<code className="text-indigo-600 font-mono text-xs">&lt;=&gt;</code>) and PostgreSQL full-text search (<code className="text-indigo-600 font-mono text-xs">tsvector</code>) fused via Reciprocal Rank Fusion (RRF k=60).
        </p>
      </div>

      {/* Search Input Bar */}
      <form onSubmit={handleSearch} className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-2xs space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter search query..."
              className="w-full rounded-lg border border-slate-200 bg-slate-50/50 pl-10 pr-4 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs">
              <Filter className="h-3.5 w-3.5 text-slate-400" />
              <select
                value={currentWorkspace}
                onChange={(e) => setCurrentWorkspace(e.target.value)}
                className="bg-transparent font-medium text-slate-700 focus:outline-none cursor-pointer"
              >
                {workspaces.map((ws) => (
                  <option key={ws} value={ws}>
                    {ws}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50 transition shadow-xs cursor-pointer"
            >
              <Sparkles className="h-3.5 w-3.5" />
              Run Hybrid Search
            </button>
          </div>
        </div>

        {topScore !== null && (
          <div className="flex items-center gap-4 text-xs text-slate-500 pt-2 border-t border-slate-100">
            <span>Results returned: <strong className="text-slate-800">{results.length}</strong></span>
            <span>•</span>
            <span>Top Vector Score: <strong className="text-indigo-600 font-mono">{topScore.toFixed(4)}</strong></span>
            <span>•</span>
            <span>Fusion Algorithm: <strong className="text-slate-800">RRF (k=60)</strong></span>
          </div>
        )}
      </form>

      {/* Results Listing */}
      <div className="space-y-4">
        {results.length === 0 ? (
          <div className="rounded-xl border border-slate-200/80 bg-white p-12 text-center text-slate-400 shadow-2xs">
            <Layers className="h-8 w-8 mx-auto mb-2 text-slate-300" />
            <p className="text-sm font-medium text-slate-600">No retrieval results to display.</p>
            <p className="text-xs text-slate-400 mt-1">Run a search query above to inspect ranked chunks and scores.</p>
          </div>
        ) : (
          results.map((chunk, index) => {
            const isExpanded = expandedId === chunk.chunk_id;
            return (
              <div
                key={chunk.chunk_id}
                className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-2xs transition hover:border-indigo-200"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-50 text-[11px] font-bold text-indigo-700">
                        #{index + 1}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900">{chunk.title}</h3>
                      <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600">
                        Section: {chunk.section}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono">{chunk.source_uri}</div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="text-xs font-bold text-indigo-600 font-mono">
                        {(chunk.score * 100).toFixed(2)}%
                      </div>
                      <div className="text-[10px] text-slate-400">RRF Score</div>
                    </div>
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : chunk.chunk_id)}
                      className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 transition cursor-pointer"
                      title={isExpanded ? "Collapse" : "Expand Chunk Content"}
                    >
                      {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                {/* Content Preview */}
                <div className={`mt-3 rounded-lg bg-slate-50/80 p-3.5 text-xs text-slate-700 leading-relaxed ${
                  isExpanded ? "" : "line-clamp-2"
                }`}>
                  {chunk.content}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
