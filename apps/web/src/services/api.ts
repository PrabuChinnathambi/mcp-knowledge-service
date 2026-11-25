import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Automatic JWT Bearer Authorization header injection
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("mcp_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 Unauthorized globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear expired token if rejected
      localStorage.removeItem("mcp_access_token");
      localStorage.removeItem("mcp_user");
    }
    return Promise.reject(error);
  }
);

// Types
export interface UserSession {
  user_id: string;
  role: string;
  workspaces: string[];
  access_token: string;
}

export interface OverviewMetrics {
  total_documents: number;
  total_chunks: number;
  total_queries: number;
  active_workspaces: number;
  workspaces: string[];
}

export interface ServiceHealth {
  postgres: "online" | "offline";
  redis: "online" | "offline";
  ollama: "online" | "offline";
  minio: "online" | "offline";
}

export interface OverviewResponse {
  metrics: OverviewMetrics;
  services: ServiceHealth;
}

export interface DocumentItem {
  id: string;
  title: string;
  workspace_id: string;
  source_uri: string;
  content_type: string;
  byte_size: number;
  status: string;
  version: number;
  embed_model: string;
  chunks_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface Citation {
  chunk_id: string;
  title: string;
  section: string;
  source_uri: string;
}

export interface AskResponse {
  trace_id: string;
  status: "answered" | "refused" | "failed";
  model?: string;
  answer: string;
  citations: Citation[];
  error?: string;
}

export interface SearchChunk {
  chunk_id: string;
  title: string;
  section: string;
  content: string;
  score: number;
  source_uri: string;
}

export interface SearchResponse {
  results: SearchChunk[];
  top_vector_score: number;
  trace: Record<string, unknown>;
}

export interface AuditLog {
  trace_id: string;
  user_id: string;
  workspace_id: string;
  query_text: string;
  status: string;
  latency_ms: number;
  created_at: string;
  data: Record<string, unknown>;
}

export interface UserItem {
  user_id: string;
  role: string;
  workspaces: string[];
  status: string;
}

export interface EvalSummary {
  pass_rate: number;
  total: number;
}

// API Service Layer
export const api = {
  // Auth
  async login(username: string, password: string): Promise<UserSession> {
    const res = await apiClient.post("/v1/auth/token", { username, password });
    const session: UserSession = {
      user_id: res.data.user_id,
      role: res.data.role,
      workspaces: res.data.workspaces,
      access_token: res.data.access_token,
    };
    localStorage.setItem("mcp_access_token", session.access_token);
    localStorage.setItem("mcp_user", JSON.stringify(session));
    return session;
  },

  logout() {
    localStorage.removeItem("mcp_access_token");
    localStorage.removeItem("mcp_user");
  },

  getCurrentUser(): UserSession | null {
    const raw = localStorage.getItem("mcp_user");
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  },

  // Overview / System Stats
  async getOverviewStats(): Promise<OverviewResponse> {
    const res = await apiClient.get<OverviewResponse>("/v1/overview/stats");
    return res.data;
  },

  // Workspaces
  async getWorkspaces(): Promise<string[]> {
    const res = await apiClient.get<{ user_id: string; workspaces: string[] }>("/v1/workspaces");
    return res.data.workspaces || [];
  },

  // LLM Models
  async getModels(): Promise<Array<{ id: string; installed: boolean; size_gb?: number }>> {
    const res = await apiClient.get<{ models: Array<{ id: string; installed: boolean; size_gb?: number }> }>("/v1/models");
    return res.data.models || [];
  },

  // Documents
  async getDocuments(workspaceId?: string): Promise<DocumentItem[]> {
    const params = workspaceId ? { workspace_id: workspaceId } : {};
    const res = await apiClient.get<{ documents: DocumentItem[] }>("/v1/documents", { params });
    return res.data.documents || [];
  },

  async uploadDocument(file: File, workspaceId: string, isAsync: boolean = false): Promise<unknown> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("workspace_id", workspaceId);

    const endpoint = isAsync ? "/v1/documents/upload/async" : "/v1/documents/upload";
    const res = await apiClient.post(endpoint, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return res.data;
  },

  async deleteDocument(documentId: string): Promise<void> {
    await apiClient.delete(`/v1/documents/${documentId}`);
  },

  // AI Assistant / Ask
  async ask(
    question: string,
    workspaceId: string,
    model?: string,
    topK: number = 5
  ): Promise<AskResponse> {
    const res = await apiClient.post<AskResponse>("/v1/harness/ask", {
      question,
      workspace_id: workspaceId,
      model: model || undefined,
      top_k: topK,
    });
    return res.data;
  },

  // Search Explorer (Hybrid)
  async search(query: string, workspaceId: string, topK: number = 10): Promise<SearchResponse> {
    const res = await apiClient.post<SearchResponse>("/v1/retrieval/search", {
      query,
      workspace_id: workspaceId,
      top_k: topK,
    });
    return res.data;
  },

  // Audit Logs
  async getAuditLogs(limit: number = 50): Promise<AuditLog[]> {
    const res = await apiClient.get<{ traces: AuditLog[] }>("/v1/audit/logs", {
      params: { limit },
    });
    return res.data.traces || [];
  },

  // Users
  async getUsers(): Promise<UserItem[]> {
    const res = await apiClient.get<{ users: UserItem[] }>("/v1/users");
    return res.data.users || [];
  },

  // Evaluations
  async getEvals(): Promise<EvalSummary> {
    const res = await apiClient.get<EvalSummary>("/v1/evals/latest");
    return res.data;
  },
};
