import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type ChecklistParty = {
  party_id: number;
  party_type: string;
  name: string;
  present_docs: string[];
  missing_docs: string[];
};

type Checklist = {
  case_id: number;
  parties: ChecklistParty[];
  missing: string[];
  is_complete: boolean;
};

export function KycChecklistCard({ data }: { data: Checklist }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Checklist KYC</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div>
          <span className="text-gray-500">Statut KYC :</span>{" "}
          <span className={data.is_complete ? "text-emerald-600 font-medium" : "text-orange-600 font-medium"}>
            {data.is_complete ? "Complet" : "Incomplet"}
          </span>
        </div>

        {data.missing.length > 0 && (
          <div>
            <div className="text-gray-500">Points manquants globaux :</div>
            <ul className="list-disc pl-5">
              {data.missing.map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
          </div>
        )}

        {data.parties.map((p) => (
          <div key={p.party_id} className="rounded-lg border p-3">
            <div className="font-medium">
              {p.party_type} — {p.name}
            </div>

            <div className="mt-2">
              <span className="text-gray-500">Documents présents :</span>{" "}
              {p.present_docs.length > 0 ? p.present_docs.join(", ") : "-"}
            </div>

            <div>
              <span className="text-gray-500">Documents manquants :</span>{" "}
              {p.missing_docs.length > 0 ? p.missing_docs.join(", ") : "Aucun"}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}