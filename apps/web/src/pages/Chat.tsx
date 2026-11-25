import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Sparkles,
  Bot,
  User,
  Copy,
  Check,
  RotateCcw,
  BookOpen,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  ThumbsUp,
  ThumbsDown,
  Cpu,
} from "lucide-react";
import { api, type Citation } from "../services/api";
import { useApp } from "../context/AppContext";

interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  text: string;
  timestamp: string;
  citations?: Citation[];
  model?: string;
  traceId?: string;
  status?: "answered" | "refused" | "failed";
}

const samplePrompts: Record<string, string[]> = {
  "hr-docs": [
    "What is the company probation period policy?",
    "How many days of annual leave can be carried forward?",
    "What are the remote work equipment allowances?",
  ],
  "engineering": [
    "What are the P1 incident response requirements?",
    "How do we handle production outage post-mortems?",
  ],
  "api-docs": [
    "How do I verify webhook HMAC signatures?",
    "What is the retry policy for failed webhook deliveries?",
  ],
};

export const Chat: React.FC = () => {
  const { currentWorkspace, setCurrentWorkspace, workspaces } = useApp();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedModel, setSelectedModel] = useState<string>("qwen2.5:7b-instruct");
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (questionText?: string) => {
    const textToSend = questionText || input.trim();
    if (!textToSend || loading) return;

    const userMessage: ChatMessage = {
      id: "usr-" + Date.now(),
      sender: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!questionText) setInput("");
    setLoading(true);

    try {
      const response = await api.ask(textToSend, currentWorkspace, selectedModel);

      const aiMessage: ChatMessage = {
        id: "ai-" + Date.now(),
        sender: "ai",
        text: response.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        citations: response.citations,
        model: response.model || selectedModel,
        traceId: response.trace_id,
        status: response.status,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        id: "err-" + Date.now(),
        sender: "ai",
        text:
          err.response?.data?.detail ||
          "Failed to connect to AI Harness. Ensure PostgreSQL and local Ollama are running.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        status: "failed",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const copyAnswer = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleCitations = (messageId: string) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [messageId]: !prev[messageId],
    }));
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="flex h-[calc(100vh-8.5rem)] flex-col rounded-xl border border-slate-200/80 bg-white shadow-2xs overflow-hidden">
      {/* Chat Sub-Header */}
      <div className="flex h-14 items-center justify-between border-b border-slate-100 bg-slate-50/50 px-5">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-xs">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Grounded AI Assistant</h2>
            <p className="text-[11px] text-slate-500">
              Answers are strictly verified against workspace document chunks.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Model Selector */}
          <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs">
            <Cpu className="h-3.5 w-3.5 text-indigo-500" />
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-transparent font-medium text-slate-700 focus:outline-none cursor-pointer"
            >
              <option value="qwen2.5:7b-instruct">qwen2.5:7b-instruct (Default)</option>
              <option value="llama3.2:3b">llama3.2:3b (Fast)</option>
              <option value="deepseek-r1:1.5b">deepseek-r1:1.5b (Reasoning)</option>
            </select>
          </div>

          <button
            onClick={clearChat}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50 transition cursor-pointer"
            title="Clear Conversation"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Clear
          </button>
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center max-w-md mx-auto">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 mb-4 shadow-xs">
              <Bot className="h-7 w-7" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">How can I help you today?</h3>
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
              Ask questions about your internal policies, engineering runbooks, or API docs. Answers include
              verified citations from your workspace documents.
            </p>

            {/* Suggested Starter Prompts */}
            <div className="mt-6 w-full space-y-2">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Suggested questions for {currentWorkspace}:
              </span>
              <div className="flex flex-col gap-2 mt-2">
                {(samplePrompts[currentWorkspace] || samplePrompts["hr-docs"]).map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(prompt)}
                    className="w-full text-left rounded-lg border border-slate-200 bg-slate-50/60 p-2.5 text-xs text-slate-700 hover:border-indigo-300 hover:bg-indigo-50/40 hover:text-indigo-900 transition text-truncate shadow-2xs cursor-pointer"
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3.5 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.sender === "ai" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-xs">
                  <Bot className="h-4.5 w-4.5" />
                </div>
              )}

              <div className={`flex flex-col max-w-2xl ${msg.sender === "user" ? "items-end" : "items-start"}`}>
                <div
                  className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-2xs ${
                    msg.sender === "user"
                      ? "bg-indigo-600 text-white rounded-br-xs"
                      : msg.status === "failed"
                      ? "bg-rose-50 text-rose-900 border border-rose-200/80 rounded-bl-xs"
                      : "bg-slate-50 text-slate-900 border border-slate-200/70 rounded-bl-xs"
                  }`}
                >
                  {msg.status === "failed" && (
                    <div className="flex items-center gap-1.5 font-semibold text-xs text-rose-700 mb-1">
                      <AlertCircle className="h-4 w-4" />
                      Harness Error
                    </div>
                  )}
                  <div className="whitespace-pre-wrap">{msg.text}</div>
                </div>

                {/* AI Message Footer / Citations */}
                {msg.sender === "ai" && (
                  <div className="mt-2 w-full space-y-2">
                    {/* Citations Accordion */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="rounded-lg border border-slate-200/80 bg-white p-2.5 text-xs shadow-2xs">
                        <button
                          onClick={() => toggleCitations(msg.id)}
                          className="flex w-full items-center justify-between font-semibold text-slate-700 hover:text-indigo-600 transition cursor-pointer"
                        >
                          <span className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-slate-500">
                            <BookOpen className="h-3.5 w-3.5 text-indigo-500" />
                            {msg.citations.length} Verified Citation{msg.citations.length > 1 ? "s" : ""}
                          </span>
                          {expandedCitations[msg.id] ? (
                            <ChevronUp className="h-3.5 w-3.5 text-slate-400" />
                          ) : (
                            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
                          )}
                        </button>

                        {expandedCitations[msg.id] && (
                          <div className="mt-2.5 space-y-2 divide-y divide-slate-100 pt-2 border-t border-slate-100">
                            {msg.citations.map((c, i) => (
                              <div key={i} className="pt-2 first:pt-0">
                                <div className="font-semibold text-slate-900">{c.title}</div>
                                <div className="text-[11px] text-indigo-600">Section: {c.section}</div>
                                <div className="text-[10px] text-slate-400 font-mono mt-0.5">{c.source_uri}</div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Meta Controls (Model, Copy, Feedback) */}
                    <div className="flex items-center gap-3 text-[11px] text-slate-400">
                      {msg.model && <span>Model: {msg.model}</span>}
                      <span>•</span>
                      <span>{msg.timestamp}</span>
                      <span>•</span>
                      <button
                        onClick={() => copyAnswer(msg.text, msg.id)}
                        className="flex items-center gap-1 hover:text-slate-700 transition cursor-pointer"
                      >
                        {copiedId === msg.id ? (
                          <>
                            <Check className="h-3 w-3 text-emerald-600" />
                            <span className="text-emerald-600">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3" />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                      <button className="hover:text-slate-600 transition cursor-pointer" title="Helpful">
                        <ThumbsUp className="h-3 w-3" />
                      </button>
                      <button className="hover:text-slate-600 transition cursor-pointer" title="Not helpful">
                        <ThumbsDown className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {msg.sender === "user" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-900 text-white shadow-xs">
                  <User className="h-4.5 w-4.5" />
                </div>
              )}
            </div>
          ))
        )}

        {/* Loading Spinner Indicator */}
        {loading && (
          <div className="flex gap-3.5 items-start">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-xs animate-pulse">
              <Bot className="h-4.5 w-4.5" />
            </div>
            <div className="rounded-2xl rounded-bl-xs bg-slate-50 border border-slate-200/80 px-4 py-3 text-xs text-slate-500 shadow-2xs flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-600" />
              </span>
              Searching vector store and synthesizing response via {selectedModel}...
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Bar */}
      <div className="border-t border-slate-100 bg-white p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-end gap-2.5 rounded-xl border border-slate-200 bg-slate-50/50 p-2 focus-within:border-indigo-500 focus-within:bg-white focus-within:ring-2 focus-within:ring-indigo-100 transition shadow-2xs"
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            placeholder={`Ask a question grounded in ${currentWorkspace}... (Press Enter to send)`}
            className="flex-1 max-h-32 resize-none bg-transparent px-2.5 py-1 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-xs cursor-pointer"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400 px-1">
          <span>Active workspace: <strong className="text-slate-700">{currentWorkspace}</strong></span>
          <span>Strict RAG Guardrails & PII Masking Active</span>
        </div>
      </div>
    </div>
  );
};
