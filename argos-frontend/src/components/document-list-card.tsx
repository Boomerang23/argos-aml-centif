import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type DocumentItem = {
  id: number;
  party_id?: number | null;
  doc_type: string;
  filename: string;
  storage_key: string;
  created_at?: string | null;
};

export function DocumentListCard({ docs }: { docs: DocumentItem[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Documents reçus</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {docs.length === 0 && (
          <div className="text-gray-500">Aucun document reçu.</div>
        )}

        {docs.map((d) => (
          <div key={d.id} className="rounded-lg border p-3">
            <div><span className="text-gray-500">Type :</span> {d.doc_type}</div>
            <div><span className="text-gray-500">Fichier :</span> {d.filename}</div>
            <div><span className="text-gray-500">Party ID :</span> {d.party_id ?? "-"}</div>
            <div>
              <span className="text-gray-500">Reçu le :</span>{" "}
              {d.created_at ? new Date(d.created_at).toLocaleString("fr-FR") : "-"}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}