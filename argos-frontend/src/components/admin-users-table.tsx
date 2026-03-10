"use client";

import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type Role = "ADMIN" | "AGENT" | "COMPLIANCE_OFFICER";

type UserItem = {
  id: number;
  email: string;
  role: Role;
  is_active: boolean;
  created_at?: string;
};

export function AdminUsersTable({
  users,
  onDone,
}: {
  users: UserItem[];
  onDone: () => void;
}) {
  const updateMutation = useMutation({
    mutationFn: ({
      userId,
      payload,
    }: {
      userId: number;
      payload: Record<string, unknown>;
    }) =>
      apiFetch(`/admin/users/${userId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      }),
    onSuccess: () => onDone(),
  });

  function changeRole(userId: number, role: Role) {
    updateMutation.mutate({
      userId,
      payload: { role },
    });
  }

  function toggleActive(userId: number, isActive: boolean) {
    updateMutation.mutate({
      userId,
      payload: { is_active: !isActive },
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Utilisateurs de l’organisation</CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {updateMutation.error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {(updateMutation.error as Error).message}
          </div>
        )}

        {users.length === 0 && (
          <div className="text-sm text-gray-500">Aucun utilisateur.</div>
        )}

        {users.map((u) => (
          <div
            key={u.id}
            className="rounded-xl border bg-white p-4 text-sm"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="font-medium">{u.email}</div>
                <div className="mt-1 text-gray-500">
                  Créé le{" "}
                  {u.created_at
                    ? new Date(u.created_at).toLocaleString("fr-FR")
                    : "-"}
                </div>
              </div>

              <div
                className={`rounded-full px-3 py-1 text-xs font-medium ${
                  u.is_active
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-gray-200 text-gray-700"
                }`}
              >
                {u.is_active ? "Actif" : "Inactif"}
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {(["ADMIN", "AGENT", "COMPLIANCE_OFFICER"] as Role[]).map((role) => (
                <Button
                  key={role}
                  type="button"
                  size="sm"
                  variant={u.role === role ? "default" : "outline"}
                  onClick={() => changeRole(u.id, role)}
                  disabled={updateMutation.isPending}
                >
                  {role}
                </Button>
              ))}

              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => toggleActive(u.id, u.is_active)}
                disabled={updateMutation.isPending}
              >
                {u.is_active ? "Désactiver" : "Activer"}
              </Button>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}