import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import { AppLayout } from "./components/layout/AppLayout";

import { Overview } from "./pages/Overview";
import { Chat } from "./pages/Chat";
import { KnowledgeBases } from "./pages/KnowledgeBases";
import { Documents } from "./pages/Documents";
import { SearchExplorer } from "./pages/SearchExplorer";
import { UsersRoles } from "./pages/UsersRoles";
import { Evaluations } from "./pages/Evaluations";
import { AuditLogs } from "./pages/AuditLogs";
import { Settings } from "./pages/Settings";

export const App: React.FC = () => {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Overview />} />
            <Route path="chat" element={<Chat />} />
            <Route path="knowledge" element={<KnowledgeBases />} />
            <Route path="documents" element={<Documents />} />
            <Route path="search" element={<SearchExplorer />} />
            <Route path="users" element={<UsersRoles />} />
            <Route path="evals" element={<Evaluations />} />
            <Route path="audit" element={<AuditLogs />} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
};

export default App;
