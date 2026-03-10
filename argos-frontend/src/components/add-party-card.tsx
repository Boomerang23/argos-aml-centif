"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

export function AddPartyCard({
  caseId,
  onDone,
}: {
  caseId: string;
  onDone: () => void;
}) {
  const [partyType, setPartyType] = useState<"BUYER" | "SELLER">("BUYER");
  const [lastName, setLastName] = useState("");
  const [firstName, setFirstName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [nationality, setNationality] = useState("CI");
  const [address, setAddress] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [idNumber, setIdNumber] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      apiFetch(`/cases/${caseId}/parties`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          party_type: partyType,
          last_name: lastName,
          first_name: firstName,
          birth_date: birthDate || null,
          nationality: nationality || null,
          address: address || null,
          email: email || null,
          phone: phone || null,
          id_number: idNumber || null,
        }),
      }),
    onSuccess: () => {
      setPartyType("BUYER");
      setLastName("");
      setFirstName("");
      setBirthDate("");
      setNationality("CI");
      setAddress("");
      setEmail("");
      setPhone("");
      setIdNumber("");
      onDone();
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ajouter une partie</CardTitle>
      </CardHeader>

      <CardContent className="grid gap-4 md:grid-cols-2">
        <div className="md:col-span-2">
          <Label>Type de partie</Label>
          <div className="mt-2 flex gap-2">
            <Button
              type="button"
              variant={partyType === "BUYER" ? "default" : "outline"}
              onClick={() => setPartyType("BUYER")}
            >
              Acheteur
            </Button>

            <Button
              type="button"
              variant={partyType === "SELLER" ? "default" : "outline"}
              onClick={() => setPartyType("SELLER")}
            >
              Vendeur
            </Button>
          </div>
        </div>

        <div>
          <Label>Nom</Label>
          <Input value={lastName} onChange={(e) => setLastName(e.target.value)} />
        </div>

        <div>
          <Label>Prénom</Label>
          <Input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
        </div>

        <div>
          <Label>Date de naissance</Label>
          <Input type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)} />
        </div>

        <div>
          <Label>Nationalité</Label>
          <Input value={nationality} onChange={(e) => setNationality(e.target.value)} />
        </div>

        <div className="md:col-span-2">
          <Label>Adresse</Label>
          <Input value={address} onChange={(e) => setAddress(e.target.value)} />
        </div>

        <div>
          <Label>Email</Label>
          <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>

        <div>
          <Label>Téléphone</Label>
          <Input value={phone} onChange={(e) => setPhone(e.target.value)} />
        </div>

        <div className="md:col-span-2">
          <Label>Numéro de pièce</Label>
          <Input value={idNumber} onChange={(e) => setIdNumber(e.target.value)} />
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
            disabled={mutation.isPending || !lastName || !firstName}
          >
            {mutation.isPending ? "Ajout..." : "Ajouter la partie"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}