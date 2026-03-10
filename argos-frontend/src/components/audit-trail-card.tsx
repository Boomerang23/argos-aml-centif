import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type AuditItem = {
  id: number;
  action: string;
  details: string;
  prev_hash?: string | null;
  hash: string;
  created_at?: string | null;
};

export function AuditTrailCard({ rows }: { rows: AuditItem[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Audit trail</CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {rows.length === 0 && (
          <div className="text-sm text-gray-500">Aucun événement audit.</div>
        )}

        {rows.map((row) => (
          <div key={row.id} className="rounded-lg border p-4 text-sm">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="font-medium">{row.action}</div>
              <div className="text-xs text-gray-500">
                {row.created_at
                  ? new Date(row.created_at).toLocaleString("fr-FR")
                  : "-"}
              </div>
            </div>

            <div className="mt-2 text-gray-700">{row.details || "-"}</div>

            <div className="mt-3 space-y-1 text-xs text-gray-500">
              <div>
                <span className="font-medium">prev_hash :</span>{" "}
                {row.prev_hash || "-"}
              </div>
              <div className="break-all">
                <span className="font-medium">hash :</span> {row.hash}
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}