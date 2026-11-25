import React, { createContext, useContext, useEffect, useState } from "react";
import { api, type UserSession } from "../services/api";

interface AppContextType {
  currentUser: UserSession | null;
  currentWorkspace: string;
  workspaces: string[];
  backendOnline: boolean;
  setCurrentWorkspace: (ws: string) => void;
  login: (username: string, pass: string) => Promise<void>;
  logout: () => void;
  refreshState: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<UserSession | null>(() => api.getCurrentUser());
  const [currentWorkspace, setCurrentWorkspace] = useState<string>("hr-docs");
  const [workspaces, setWorkspaces] = useState<string[]>(["hr-docs", "api-docs", "engineering"]);
  const [backendOnline, setBackendOnline] = useState<boolean>(true);

  const refreshState = async () => {
    try {
      const stats = await api.getOverviewStats();
      setBackendOnline(true);
      if (stats.metrics.workspaces && stats.metrics.workspaces.length > 0) {
        setWorkspaces(stats.metrics.workspaces);
        if (!stats.metrics.workspaces.includes(currentWorkspace)) {
          setCurrentWorkspace(stats.metrics.workspaces[0]);
        }
      }
    } catch {
      setBackendOnline(false);
    }
  };

  useEffect(() => {
    // If not logged in, auto-login with default dev user "alice" for seamless developer experience
    if (!currentUser) {
      api.login("alice", "password123")
        .then((user) => {
          setCurrentUser(user);
          refreshState();
        })
        .catch(() => {
          // Backend might be offline during initial boot
          refreshState();
        });
    } else {
      refreshState();
    }
  }, []);

  const login = async (username: string, pass: string) => {
    const user = await api.login(username, pass);
    setCurrentUser(user);
    if (user.workspaces.length > 0) {
      setWorkspaces(user.workspaces);
      setCurrentWorkspace(user.workspaces[0]);
    }
    await refreshState();
  };

  const logout = () => {
    api.logout();
    setCurrentUser(null);
  };

  return (
    <AppContext.Provider
      value={{
        currentUser,
        currentWorkspace,
        workspaces,
        backendOnline,
        setCurrentWorkspace,
        login,
        logout,
        refreshState,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
};
