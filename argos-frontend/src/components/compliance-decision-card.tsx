"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export function ComplianceDecisionCard({
  caseId,
  onDone,
}: {
  caseId: string;
  onDone: () => void;
}) {
  const [comment, setComment] = useState("");

  const mutation = useMutation({
    mutationFn: (decision: "VALIDATED" | "ESCALATED" | "REJECTED") =>
      apiFetch(`/cases/${caseId}/compliance-decision`, {
        method: "POST",
        body: {
          decision,
          comment,
        },
      }),
    onSuccess: () => {
      setComment("");
      onDone();
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Décision conformité</CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        <Textarea
          placeholder="Commentaire conformité"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />

        {mutation.error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {(mutation.error as Error).message}
          </div>
        )}

        <div className="flex gap-2">
          <Button
            onClick={() => mutation.mutate("VALIDATED")}
            disabled={mutation.isPending}
          >
            Valider
          </Button>

          <Button
            variant="secondary"
            onClick={() => mutation.mutate("ESCALATED")}
            disabled={mutation.isPending}
          >
            Escalader
          </Button>

          <Button
            variant="destructive"
            onClick={() => mutation.mutate("REJECTED")}
            disabled={mutation.isPending}
          >
            Rejeter
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}