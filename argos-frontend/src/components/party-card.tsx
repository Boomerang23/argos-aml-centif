import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type Party = {
  id: number;
  party_type: "BUYER" | "SELLER";
  last_name: string;
  first_name: string;
  birth_date?: string | null;
  nationality?: string | null;
  address?: string | null;
  email?: string | null;
  phone?: string | null;
  id_number?: string | null;
};

export function PartyCard({ p }: { p: Party }) {
  const title = p.party_type === "BUYER" ? "Acheteur" : "Vendeur";

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2 text-sm">
        <div><span className="text-gray-500">Nom:</span> {p.last_name}</div>
        <div><span className="text-gray-500">Prénom:</span> {p.first_name}</div>
        <div><span className="text-gray-500">Naissance:</span> {p.birth_date || "-"}</div>
        <div><span className="text-gray-500">Nationalité:</span> {p.nationality || "-"}</div>
        <div><span className="text-gray-500">Adresse:</span> {p.address || "-"}</div>
        <div><span className="text-gray-500">Email:</span> {p.email || "-"}</div>
        <div><span className="text-gray-500">Téléphone:</span> {p.phone || "-"}</div>
        <div><span className="text-gray-500">ID:</span> {p.id_number || "-"}</div>
      </CardContent>
    </Card>
  );
}