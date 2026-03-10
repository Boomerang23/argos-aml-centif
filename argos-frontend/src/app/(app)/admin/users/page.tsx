"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AdminUserForm } from "@/components/admin-user-form";
import { AdminUsersTable } from "@/components/admin-users-table";

type OrgData = {
  org_id: number;
  name: string;
};

type UserItem = {
  id: number;
  email: string;
  role: "ADMIN" | "AGENT" | "COMPLIANCE_OFFICER";
  is_active: boolean;
  created_at?: string;
};

export default function AdminUsersPage() {
  const {
    data: orgData,
    isLoading: orgLoading,
    error: orgError,
  } = useQuery({
    queryKey: ["admin-org"],
    queryFn: () => apiFetch("/admin/org/me"),
  });

  const {
    data: usersData,
    isLoading: usersLoading,
    error: usersError,
    refetch: refetchUsers,
  } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => apiFetch("/admin/users"),
  });

  if (orgLoading || usersLoading) {
    return <div>Chargement...</div>;
  }

  if (orgError || usersError) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
        {orgError
          ? (orgError as Error).message
          : (usersError as Error).message}
      </div>
    );
  }

  const org = orgData as OrgData;
  const users = ((usersData as UserItem[]) || []);

  return (
    <div className="space-y-4">
      <div>
        <div className="text-xl font-semibold">Administration</div>
        <div className="text-sm text-gray-500">
          Gestion des utilisateurs et de l’organisation.
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Organisation</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          <div>
            <span className="text-gray-500">Nom :</span> {org.name}
          </div>
          <div>
            <span className="text-gray-500">ID :</span> {org.org_id}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <AdminUserForm onDone={() => refetchUsers()} />
        <AdminUsersTable users={users} onDone={() => refetchUsers()} />
      </div>
    </div>
  );
}