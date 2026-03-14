"use client";

import { useState } from "react";
import { getToken } from "@/lib/auth";
import { getApiBaseUrlOrThrow } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function ExportPdfCard({
  caseId,
}: {
  caseId: number;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleDownload() {
    try {
      setLoading(true);
      setError("");

      const token = getToken();
      const apiBase = getApiBaseUrlOrThrow();

      const res = await fetch(`${apiBase}/reports/cases/${caseId}/pdf`, {
        method: "GET",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Erreur téléchargement PDF");
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = `ARGOS_CASE_${caseId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();

      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err?.message || "Erreur téléchargement PDF");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Export dossier conformité</CardTitle>
      </CardHeader>

      <CardContent className="space-y-3 text-sm">
        <div className="text-gray-600">
          Télécharge le PDF complet du dossier AML incluant :
          transaction, parties, KYC, screening, score, décision conformité et audit trail.
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <Button onClick={handleDownload} disabled={loading}>
          {loading ? "Téléchargement..." : "Télécharger le PDF Bouclier"}
        </Button>
      </CardContent>
    </Card>
  );
}