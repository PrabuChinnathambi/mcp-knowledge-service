import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  MessageSquare,
  FolderKanban,
  FileText,
  Search,
  Users,
  Award,
  ScrollText,
  Settings,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  LogOut,
  UserCheck,
} from "lucide-react";
import { useApp } from "../../context/AppContext";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navItems = [
  { path: "/", label: "Overview", icon: LayoutDashboard },
  { path: "/chat", label: "AI Assistant", icon: MessageSquare },
  { path: "/knowledge", label: "Knowledge Bases", icon: FolderKanban },
  { path: "/documents", label: "Documents", icon: FileText },
  { path: "/search", label: "Search Explorer", icon: Search },
  { path: "/users", label: "Users & Roles", icon: Users },
  { path: "/evals", label: "Evaluations", icon: Award },
  { path: "/audit", label: "Audit Logs", icon: ScrollText },
  { path: "/settings", label: "Settings", icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const { currentUser, logout } = useApp();

  return (
    <aside
      className={`relative flex flex-col border-r border-slate-200 bg-white transition-all duration-300 ease-in-out z-20 ${
        collapsed ? "w-18" : "w-64"
      }`}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between border-b border-slate-100 px-4">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-sm shadow-indigo-200">
            <Sparkles className="h-5 w-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col truncate">
              <span className="text-sm font-semibold text-slate-900 tracking-tight">MCP Knowledge</span>
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Enterprise RAG</span>
            </div>
          )}
        </div>

        <button
          onClick={onToggle}
          className="flex h-7 w-7 items-center justify-center rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition"
          title={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                  isActive
                    ? "bg-indigo-50 text-indigo-700 shadow-xs"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`
              }
              title={collapsed ? item.label : undefined}
            >
              <Icon className="h-4.5 w-4.5 shrink-0 transition" />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* User Footer */}
      <div className="border-t border-slate-100 p-3">
        <div
          className={`flex items-center justify-between rounded-lg bg-slate-50 p-2 ${
            collapsed ? "flex-col gap-2" : ""
          }`}
        >
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-indigo-700 font-semibold text-xs">
              {currentUser?.user_id?.[0]?.toUpperCase() || "A"}
            </div>
            {!collapsed && (
              <div className="flex flex-col truncate">
                <span className="text-xs font-semibold text-slate-800 capitalize truncate">
                  {currentUser?.user_id || "Alice"}
                </span>
                <span className="text-[10px] text-slate-500 capitalize flex items-center gap-1">
                  <UserCheck className="h-3 w-3 text-emerald-500 inline" />
                  {currentUser?.role || "Admin"}
                </span>
              </div>
            )}
          </div>

          <button
            onClick={logout}
            className="flex h-7 w-7 items-center justify-center rounded-md text-slate-400 hover:bg-slate-200 hover:text-slate-700 transition"
            title="Log out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
