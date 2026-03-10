"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

type Role = "ADMIN" | "AGENT" | "COMPLIANCE_OFFICER";

export function AdminUserForm({
  onDone,
}: {
  onDone: () => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("AGENT");

  const mutation = useMutation({
    mutationFn: () =>
      apiFetch("/admin/users", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
          role,
        }),
      }),
    onSuccess: () => {
      setEmail("");
      setPassword("");
      setRole("AGENT");
      onDone();
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Créer un utilisateur</CardTitle>
      </CardHeader>

      <CardContent className="grid gap-4 md:grid-cols-2">
        <div className="md:col-span-2">
          <Label>Email</Label>
          <Input
            type="email"
            placeholder="agent@argos.ci"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div>
          <Label>Mot de passe</Label>
          <Input
            type="password"
            placeholder="Mot de passe"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <div>
          <Label>Rôle</Label>
          <div className="mt-2 flex flex-wrap gap-2">
            {(["ADMIN", "AGENT", "COMPLIANCE_OFFICER"] as Role[]).map((r) => (
              <Button
                key={r}
                type="button"
                variant={role === r ? "default" : "outline"}
                onClick={() => setRole(r)}
              >
                {r}
              </Button>
            ))}
          </div>
        </div>

        {mutation.error && (
          <div className="md:col-span-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {(mutation.error as Error).message}
          </div>
        )}

        <div className="md:col-span-2 flex justify-end">
          <Button
            type="button"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !email || !password}
          >
            {mutation.isPending ? "Création..." : "Créer l'utilisateur"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}