"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CasesTable } from "@/components/cases-table";

type Status = "DRAFT" | "ORANGE" | "GREEN" | "RED";

type CaseRow = {
  id: number;
  reference: string;
  status: Status;
  amount_fcfa?: number | null;
  risk_score: number;
  updated_at: string;
};

export default function CasesPage() {
  const searchParams = useSearchParams();
  const initialStatus =
    (searchParams.get("status") as Status | "ALL" | null) || "ALL";

  const [status, setStatus] = useState<Status | "ALL">(initialStatus);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["cases", status],
    queryFn: () => {
      const qs = status === "ALL" ? "" : `?status=${status}`;
      return apiFetch(`/cases${qs}`);
    },
  });

  const rows: CaseRow[] = useMemo(() => {
    return (data || []) as CaseRow[];
  }, [data]);

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xl font-semibold">Dossiers</div>
          <div className="text-sm text-gray-500">
            Liste des dossiers AML de ton organisation.
          </div>
        </div>

        <Button asChild>
          <Link href="/cases/new">Nouveau dossier</Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filtres</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {(["ALL", "DRAFT", "ORANGE", "GREEN", "RED"] as const).map((s) => (
            <Button
              key={s}
              variant={status === s ? "default" : "outline"}
              onClick={() => setStatus(s)}
            >
              {s}
            </Button>
          ))}

          <Button variant="secondary" onClick={() => refetch()}>
            Rafraîchir
          </Button>
        </CardContent>
      </Card>

      {isLoading && <div>Chargement...</div>}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {(error as Error).message}
        </div>
      )}

      {!isLoading && !error && <CasesTable rows={rows} />}
    </div>
  );
}