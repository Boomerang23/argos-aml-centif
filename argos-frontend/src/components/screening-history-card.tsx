import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type ScreeningItem = {
  id: number;
  query: string;
  provider: string;
  risk_flag: boolean;
  created_at?: string | null;
};

export function ScreeningHistoryCard({
  rows,
}: {
  rows: ScreeningItem[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Historique screening</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {rows.length === 0 && (
          <div className="text-gray-500">Aucun screening effectué.</div>
        )}

        {rows.map((row) => (
          <div key={row.id} className="rounded-lg border p-3">
            <div>
              <span className="text-gray-500">Query :</span> {row.query}
            </div>
            <div>
              <span className="text-gray-500">Provider :</span> {row.provider}
            </div>
            <div>
              <span className="text-gray-500">Résultat :</span>{" "}
              <span className={row.risk_flag ? "font-medium text-red-600" : "font-medium text-emerald-600"}>
                {row.risk_flag ? "Match / Risk flag" : "No match"}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Date :</span>{" "}
              {row.created_at ? new Date(row.created_at).toLocaleString("fr-FR") : "-"}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}