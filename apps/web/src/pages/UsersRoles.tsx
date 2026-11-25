import React, { useEffect, useState } from "react";
import { Users, Shield, CheckCircle2, UserCheck, KeyRound } from "lucide-react";
import { api, type UserItem } from "../services/api";
import { useApp } from "../context/AppContext";

export const UsersRoles: React.FC = () => {
  const { currentUser, login } = useApp();
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    api.getUsers()
      .then((data) => setUsers(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const switchUser = async (username: string) => {
    try {
      await login(username, "password123");
      alert(`Switched active session to user: ${username}`);
    } catch (err: any) {
      alert("Failed to switch user");
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Users & Roles Management</h1>
        <p className="text-sm text-slate-500 mt-1">
          Multi-tenant directory with cryptographic HS256 JWT tokens and granular workspace RBAC policies.
        </p>
      </div>

      {/* Users Table */}
      <div className="rounded-xl border border-slate-200/80 bg-white p-6 shadow-2xs">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-indigo-600" />
            <h2 className="text-base font-semibold text-slate-900">Directory Accounts</h2>
          </div>
          <span className="text-xs text-slate-400">Total Users: {users.length}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <tr>
                <th className="pb-3">User</th>
                <th className="pb-3">Role & Permissions</th>
                <th className="pb-3">Authorized Workspaces</th>
                <th className="pb-3">Status</th>
                <th className="pb-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {users.map((u) => {
                const isCurrent = currentUser?.user_id === u.user_id;
                return (
                  <tr key={u.user_id} className="hover:bg-slate-50/50 transition">
                    <td className="py-4 font-semibold text-slate-900 flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-50 text-indigo-700 font-bold text-xs uppercase">
                        {u.user_id[0]}
                      </div>
                      <div>
                        <div className="capitalize">{u.user_id}</div>
                        <div className="text-[10px] text-slate-400 font-normal">{u.user_id}@company.internal</div>
                      </div>
                    </td>
                    <td className="py-4">
                      <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                        u.role === "admin"
                          ? "bg-purple-50 text-purple-700 border border-purple-200/60"
                          : u.role === "editor"
                          ? "bg-blue-50 text-blue-700 border border-blue-200/60"
                          : "bg-slate-100 text-slate-700"
                      }`}>
                        <Shield className="h-3 w-3" />
                        {u.role}
                      </span>
                    </td>
                    <td className="py-4">
                      <div className="flex flex-wrap gap-1.5">
                        {u.workspaces.map((ws) => (
                          <span
                            key={ws}
                            className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600"
                          >
                            {ws}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-4">
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-600">
                        <CheckCircle2 className="h-3 w-3" />
                        Active
                      </span>
                    </td>
                    <td className="py-4 text-right">
                      {isCurrent ? (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600">
                          <UserCheck className="h-3.5 w-3.5" />
                          Current User
                        </span>
                      ) : (
                        <button
                          onClick={() => switchUser(u.user_id)}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 transition cursor-pointer"
                        >
                          <KeyRound className="h-3 w-3" />
                          Simulate User
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
