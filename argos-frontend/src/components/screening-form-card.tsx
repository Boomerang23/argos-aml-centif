"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function ScreeningFormCard({
  caseId,
  onDone,
}: {
  caseId: string;
  onDone: () => void;
}) {
  const [query, setQuery] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      apiFetch(`/screening/cases/${caseId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      }),
    onSuccess: () => {
      setQuery("");
      onDone();
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Lancer un screening</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Input
          placeholder="Nom à vérifier"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />

        {mutation.error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {(mutation.error as Error).message}
          </div>
        )}

        <Button
          onClick={() => mutation.mutate()}
          disabled={!query.trim() || mutation.isPending}
        >
          {mutation.isPending ? "Screening..." : "Lancer screening"}
        </Button>
      </CardContent>
    </Card>
  );
}