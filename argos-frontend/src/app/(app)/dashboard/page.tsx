"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { KpiCard } from "@/components/kpi-card";

type DashboardSummary = {
  scope: string;
  total_cases: number;
  by_status: {
    DRAFT: number;
    ORANGE: number;
    GREEN: number;
    RED: number;
  };
  alerts: {
    red_cases: number;
    draft_incomplete: number;
  };
  compliance_decisions: {
    VALIDATED: number;
    ESCALATED: number;
    REJECTED: number;
  };
};

export default function DashboardPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => apiFetch("/dashboard/summary"),
  });

  const d = data as DashboardSummary | undefined;

  if (isLoading) {
    return <div>Chargement...</div>;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
        {(error as Error).message}
      </div>
    );
  }

  if (!d) {
    return <div>Aucune donnée</div>;
  }

  if (d.total_cases === 0) {
    return (
      <div className="space-y-4">
        <div>
          <div className="text-xl font-semibold">Dashboard AML</div>
          <div className="text-sm text-gray-500">
            Vue synthétique conformité.
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Aucun dossier pour le moment</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-gray-600">
            <div>
              Commence par créer ton premier dossier AML pour voir le dashboard se remplir.
            </div>

            <Button asChild>
              <Link href="/cases/new">Créer un dossier</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-xl font-semibold">Dashboard AML</div>
          <div className="text-sm text-gray-500">
            Vue synthétique conformité de{" "}
            {d.scope === "agent" ? "tes dossiers" : "ton organisation"}.
          </div>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            Rafraîchir
          </Button>
          <Button asChild>
            <Link href="/cases">Voir les dossiers</Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <KpiCard title="Total dossiers" value={d.total_cases} />
        <KpiCard
          title="RED"
          value={d.by_status.RED}
          subtitle="Alertes critiques"
        />
        <KpiCard
          title="ORANGE"
          value={d.by_status.ORANGE}
          subtitle="Vigilance normale"
        />
        <KpiCard
          title="GREEN"
          value={d.by_status.GREEN}
          subtitle="Dossiers conformes"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Workflow dossiers</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center justify-between rounded-lg border p-3">
              <span>DRAFT</span>
              <span className="font-semibold">{d.by_status.DRAFT}</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <span>ORANGE</span>
              <span className="font-semibold">{d.by_status.ORANGE}</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <span>GREEN</span>
              <span className="font-semibold">{d.by_status.GREEN}</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <span>RED</span>
              <span className="font-semibold text-red-600">
                {d.by_status.RED}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Décisions conformité</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center justify-between rounded-lg border p-3">
              <span>VALIDATED</span>
              <span className="font-semibold">
                {d.compliance_decisions.VALIDATED}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <span>ESCALATED</span>
              <span className="font-semibold">
                {d.compliance_decisions.ESCALATED}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <span>REJECTED</span>
              <span className="font-semibold">
                {d.compliance_decisions.REJECTED}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Alertes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="rounded-lg border border-red-200 bg-red-50 p-3">
              <div className="font-medium text-red-700">Dossiers RED</div>
              <div className="mt-1 text-red-600">
                {d.alerts.red_cases} dossier(s) à traiter en priorité
              </div>
            </div>

            <div className="rounded-lg border border-orange-200 bg-orange-50 p-3">
              <div className="font-medium text-orange-700">
                Dossiers incomplets
              </div>
              <div className="mt-1 text-orange-600">
                {d.alerts.draft_incomplete} dossier(s) en attente de complétion
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Actions rapides</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Button asChild variant="outline">
              <Link href="/cases?status=RED">Voir les RED</Link>
            </Button>

            <Button asChild variant="outline">
              <Link href="/cases?status=DRAFT">Voir les incomplets</Link>
            </Button>

            <Button asChild>
              <Link href="/cases/new">Créer un dossier</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}