"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type Party = {
  id: number;
  party_type: "BUYER" | "SELLER";
  last_name: string;
  first_name: string;
};

export function OnboardingLinkCard({
  caseId,
  parties,
}: {
  caseId: string;
  parties: Party[];
}) {
  const [selectedPartyId, setSelectedPartyId] = useState<string>("");
  const [generatedUrl, setGeneratedUrl] = useState("");
  const [copyOk, setCopyOk] = useState(false);

  const mutation = useMutation({
    mutationFn: () =>
      apiFetch(`/onboarding/cases/${caseId}/parties/${selectedPartyId}/link`, {
        method: "POST",
      }),
    onSuccess: (data: any) => {
      setGeneratedUrl(data.url || "");
      setCopyOk(false);
    },
  });

  async function handleCopy() {
    if (!generatedUrl) return;
    await navigator.clipboard.writeText(generatedUrl);
    setCopyOk(true);
    setTimeout(() => setCopyOk(false), 1500);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Lien onboarding sécurisé</CardTitle>
      </CardHeader>

      <CardContent className="space-y-4 text-sm">
        {parties.length === 0 ? (
          <div className="text-gray-500">
            Ajoute d’abord une partie au dossier pour générer un lien KYC.
          </div>
        ) : (
          <>
            <div>
              <div className="mb-2 text-gray-500">Choisir la partie</div>

              <div className="flex flex-wrap gap-2">
                {parties.map((p) => {
                  const label =
                    p.party_type === "BUYER"
                      ? `Acheteur — ${p.last_name} ${p.first_name}`
                      : `Vendeur — ${p.last_name} ${p.first_name}`;

                  return (
                    <Button
                      key={p.id}
                      type="button"
                      variant={selectedPartyId === String(p.id) ? "default" : "outline"}
                      onClick={() => setSelectedPartyId(String(p.id))}
                    >
                      {label}
                    </Button>
                  );
                })}
              </div>
            </div>

            {mutation.error && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-red-700">
                {(mutation.error as Error).message}
              </div>
            )}

            <Button
              type="button"
              onClick={() => mutation.mutate()}
              disabled={!selectedPartyId || mutation.isPending}
            >
              {mutation.isPending ? "Génération..." : "Générer le lien"}
            </Button>

            {generatedUrl && (
              <div className="space-y-2 rounded-lg border p-3">
                <div className="text-gray-500">Lien généré</div>
                <div className="break-all text-sm">{generatedUrl}</div>

                <div className="flex gap-2">
                  <Button type="button" variant="secondary" onClick={handleCopy}>
                    {copyOk ? "Copié" : "Copier le lien"}
                  </Button>

                  <Button asChild variant="outline">
                    <a href={generatedUrl} target="_blank" rel="noreferrer">
                      Ouvrir
                    </a>
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}