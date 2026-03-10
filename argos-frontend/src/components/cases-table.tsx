"use client";

import Link from "next/link";
import { StatusBadge } from "@/components/status-badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type CaseRow = {
  id: number;
  reference: string;
  status: "DRAFT" | "ORANGE" | "GREEN" | "RED";
  amount_fcfa?: number | null;
  risk_score: number;
  updated_at: string;
};

function formatMoney(n?: number | null) {
  if (!n) return "-";
  return new Intl.NumberFormat("fr-FR").format(n) + " FCFA";
}

export function CasesTable({ rows }: { rows: CaseRow[] }) {
  return (
    <div className="rounded-xl border bg-white">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Référence</TableHead>
            <TableHead>Montant</TableHead>
            <TableHead>Statut</TableHead>
            <TableHead>Score</TableHead>
            <TableHead>Dernière maj</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {rows.map((c) => (
            <TableRow key={c.id} className="hover:bg-gray-50">
              <TableCell className="font-medium">
                <Link className="underline-offset-4 hover:underline" href={`/cases/${c.id}`}>
                  {c.reference}
                </Link>
              </TableCell>
              <TableCell>{formatMoney(c.amount_fcfa)}</TableCell>
              <TableCell><StatusBadge status={c.status} /></TableCell>
              <TableCell>{c.risk_score}</TableCell>
              <TableCell>{new Date(c.updated_at).toLocaleString("fr-FR")}</TableCell>
            </TableRow>
          ))}

          {rows.length === 0 && (
            <TableRow>
              <TableCell colSpan={5} className="py-10 text-center text-sm text-gray-500">
                Aucun dossier
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}