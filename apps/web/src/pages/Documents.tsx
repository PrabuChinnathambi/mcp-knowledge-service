import React, { useEffect, useState, useRef } from "react";
import {
  UploadCloud,
  FileText,
  Trash2,
  CheckCircle2,
  RefreshCw,
  Search,
  Check,
  AlertCircle,
} from "lucide-react";
import { api, type DocumentItem } from "../services/api";
import { useApp } from "../context/AppContext";

export const Documents: React.FC = () => {
  const { currentWorkspace } = useApp();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const docs = await api.getDocuments();
      setDocuments(docs);
    } catch (err: any) {
      console.error("Failed to load documents", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    setUploading(true);
    setUploadSuccess(null);
    setUploadError(null);

    try {
      await api.uploadDocument(file, currentWorkspace);
      setUploadSuccess(`Successfully ingested "${file.name}" into ${currentWorkspace}!`);
      await loadDocuments();
    } catch (err: any) {
      setUploadError(
        err.response?.data?.detail || "Upload failed. Please check supported extensions (.md, .txt, .pdf, .docx, .xlsx)"
      );
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDelete = async (docId: string, title: string) => {
    if (!confirm(`Are you sure you want to delete "${title}"?`)) return;
    try {
      await api.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete document.");
    }
  };

  const filteredDocs = documents.filter(
    (d) =>
      d.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.workspace_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Document Management</h1>
        <p className="text-sm text-slate-500 mt-1">
          Upload and index enterprise documents. Automatically parsed, chunked, and vectorized with 768-dim embeddings.
        </p>
      </div>

      {/* Drag-and-drop Upload Area */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          handleFileUpload(e.dataTransfer.files);
        }}
        className="relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-white p-8 text-center hover:border-indigo-500 hover:bg-indigo-50/20 transition cursor-pointer"
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".md,.txt,.pdf,.docx,.xlsx"
          className="hidden"
          onChange={(e) => handleFileUpload(e.target.files)}
        />

        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 mb-3">
          <UploadCloud className="h-6 w-6" />
        </div>

        <h3 className="text-sm font-semibold text-slate-900">
          Click to upload or drag & drop documents
        </h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          Target workspace: <strong className="text-indigo-600 font-semibold">{currentWorkspace}</strong>.
          Supported formats: <strong>.md, .txt, .pdf, .docx, .xlsx</strong> (Max 50MB)
        </p>

        {uploading && (
          <div className="mt-4 flex items-center gap-2 text-xs font-semibold text-indigo-600">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Extracting text, computing 768-dim embeddings, and inserting into vector store...
          </div>
        )}

        {uploadSuccess && (
          <div className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200/60">
            <Check className="h-4 w-4" />
            {uploadSuccess}
          </div>
        )}

        {uploadError && (
          <div className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-rose-600 bg-rose-50 px-3 py-1.5 rounded-lg border border-rose-200/60">
            <AlertCircle className="h-4 w-4" />
            {uploadError}
          </div>
        )}
      </div>

      {/* Documents Table */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-2xs">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-5">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search documents by title or workspace..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-slate-50/50 pl-9 pr-3 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none"
            />
          </div>
          <button
            onClick={loadDocuments}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="pb-3">Title & Source</th>
                <th className="pb-3">Workspace</th>
                <th className="pb-3">Chunks</th>
                <th className="pb-3">Format</th>
                <th className="pb-3">Size</th>
                <th className="pb-3">Status</th>
                <th className="pb-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    No matching documents found.
                  </td>
                </tr>
              ) : (
                filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/50 transition">
                    <td className="py-3.5 font-medium text-slate-900 flex items-center gap-2.5">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                        <FileText className="h-4 w-4" />
                      </div>
                      <div>
                        <div className="font-semibold text-slate-900">{doc.title}</div>
                        <div className="text-[10px] text-slate-400 font-mono max-w-xs truncate">
                          {doc.source_uri}
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5">
                      <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700">
                        {doc.workspace_id}
                      </span>
                    </td>
                    <td className="py-3.5 font-semibold text-slate-800">{doc.chunks_count}</td>
                    <td className="py-3.5 uppercase font-medium text-slate-500 text-[10px]">
                      {doc.content_type.split("/")[1] || "text"}
                    </td>
                    <td className="py-3.5 text-slate-500">{(doc.byte_size / 1024).toFixed(1)} KB</td>
                    <td className="py-3.5">
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 border border-emerald-200/50">
                        <CheckCircle2 className="h-3 w-3" />
                        {doc.status}
                      </span>
                    </td>
                    <td className="py-3.5 text-right">
                      <button
                        onClick={() => handleDelete(doc.id, doc.title)}
                        className="rounded-md p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 transition cursor-pointer"
                        title="Delete Document"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
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
