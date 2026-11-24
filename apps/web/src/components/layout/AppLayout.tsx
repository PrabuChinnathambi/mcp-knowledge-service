import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Navbar } from "./Navbar";

export const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState<boolean>(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans text-slate-900 antialiased">
      {/* Collapsible Sidebar */}
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top Navbar */}
        <Navbar />

        {/* Dynamic Route View */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
