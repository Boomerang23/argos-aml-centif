"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

export default function NewCasePage() {
  const router = useRouter();

  const [reference, setReference] = useState("");
  const [amountFcfa, setAmountFcfa] = useState("");
  const [paymentMode, setPaymentMode] = useState("");
  const [fundsOrigin, setFundsOrigin] = useState("");
  const [countryResidence, setCountryResidence] = useState("CI");
  const [profession, setProfession] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await apiFetch("/cases", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          reference,
          amount_fcfa: amountFcfa ? Number(amountFcfa) : null,
          payment_mode: paymentMode || null,
          funds_origin: fundsOrigin || null,
          country_residence: countryResidence || null,
          profession: profession || null,
        }),
      });

      router.push(`/cases/${res.id}?from=create`);
    } catch (err: any) {
      setError(err?.message || "Erreur création dossier");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <div className="text-xl font-semibold">Nouveau dossier AML</div>
        <div className="text-sm text-gray-500">
          Étape 1 sur 4 — Informations transactionnelles
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Transaction</CardTitle>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2">
              <Label>Référence</Label>
              <Input
                placeholder="CASE-IMMO-0002"
                value={reference}
                onChange={(e) => setReference(e.target.value)}
                required
              />
            </div>

            <div>
              <Label>Montant (FCFA)</Label>
              <Input
                type="number"
                placeholder="65000000"
                value={amountFcfa}
                onChange={(e) => setAmountFcfa(e.target.value)}
              />
            </div>

            <div>
              <Label>Mode de paiement</Label>
              <Input
                placeholder="CASH / BANK / MIXED"
                value={paymentMode}
                onChange={(e) => setPaymentMode(e.target.value)}
              />
            </div>

            <div className="md:col-span-2">
              <Label>Origine des fonds</Label>
              <Input
                placeholder="Ex: vente terrain"
                value={fundsOrigin}
                onChange={(e) => setFundsOrigin(e.target.value)}
              />
            </div>

            <div>
              <Label>Pays de résidence</Label>
              <Input
                placeholder="CI"
                value={countryResidence}
                onChange={(e) => setCountryResidence(e.target.value)}
              />
            </div>

            <div>
              <Label>Profession</Label>
              <Input
                placeholder="Entrepreneur"
                value={profession}
                onChange={(e) => setProfession(e.target.value)}
              />
            </div>

            {error && (
              <div className="md:col-span-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="md:col-span-2 flex justify-end">
              <Button type="submit" disabled={loading}>
                {loading ? "Création..." : "Créer le dossier"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}