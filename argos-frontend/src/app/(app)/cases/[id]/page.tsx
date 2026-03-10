"use client";

import { useParams, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

import { PartyCard } from "@/components/party-card";
import { AddPartyCard } from "@/components/add-party-card";
import { KycChecklistCard } from "@/components/kyc-checklist-card";
import { DocumentListCard } from "@/components/document-list-card";
import { ScreeningFormCard } from "@/components/screening-form-card";
import { ScreeningHistoryCard } from "@/components/screening-history-card";
import { ComplianceDecisionCard } from "@/components/compliance-decision-card";
import { AuditTrailCard } from "@/components/audit-trail-card";
import { ExportPdfCard } from "@/components/export-pdf-card";
import { OnboardingLinkCard } from "@/components/onboarding-link-card";
import { CaseWorkflowBanner } from "@/components/case-workflow-banner";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { StatusBadge, Status } from "@/components/status-badge";

type CaseDetail = {
  id: number;
  reference: string;
  status: Status;
  amount_fcfa?: number | null;
  payment_mode?: string | null;
  funds_origin?: string | null;
  country_residence?: string | null;
  profession?: string | null;
  risk_score: number;
  risk_details?: string | null;
  compliance_decision?: "VALIDATED" | "ESCALATED" | "REJECTED" | null;
  compliance_comment?: string | null;
  date_validation?: string | null;
  created_at: string;
  updated_at: string;
};

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

type ChecklistParty = {
  party_id: number;
  party_type: string;
  name: string;
  present_docs: string[];
  missing_docs: string[];
};

type KycChecklist = {
  case_id: number;
  parties: ChecklistParty[];
  missing: string[];
  is_complete: boolean;
};

type DocumentItem = {
  id: number;
  party_id?: number | null;
  doc_type: string;
  filename: string;
  storage_key: string;
  created_at?: string | null;
};

type ScreeningItem = {
  id: number;
  query: string;
  provider: string;
  risk_flag: boolean;
  created_at?: string | null;
  result_json?: string;
};

type AuditItem = {
  id: number;
  action: string;
  details: string;
  prev_hash?: string | null;
  hash: string;
  created_at?: string | null;
};

function formatMoney(n?: number | null) {
  if (n === null || n === undefined) return "-";
  return new Intl.NumberFormat("fr-FR").format(n) + " FCFA";
}

export default function CaseDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const caseId = params?.id as string;
  const fromCreate = searchParams.get("from") === "create";

  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["case", caseId],
    queryFn: () => apiFetch(`/cases/${caseId}`),
    enabled: !!caseId,
  });

  const {
    data: partiesData,
    isLoading: partiesLoading,
    error: partiesError,
    refetch: refetchParties,
  } = useQuery({
    queryKey: ["case-parties", caseId],
    queryFn: () => apiFetch(`/cases/${caseId}/parties`),
    enabled: !!caseId,
  });

  const {
    data: checklistData,
    isLoading: checklistLoading,
    error: checklistError,
    refetch: refetchChecklist,
  } = useQuery({
    queryKey: ["case-kyc-checklist", caseId],
    queryFn: () => apiFetch(`/onboarding/cases/${caseId}/kyc-checklist`),
    enabled: !!caseId,
  });

  const {
    data: documentsData,
    isLoading: documentsLoading,
    error: documentsError,
    refetch: refetchDocuments,
  } = useQuery({
    queryKey: ["case-documents", caseId],
    queryFn: () => apiFetch(`/onboarding/cases/${caseId}/documents`),
    enabled: !!caseId,
  });

  const {
    data: screeningsData,
    isLoading: screeningsLoading,
    error: screeningsError,
    refetch: refetchScreenings,
  } = useQuery({
    queryKey: ["case-screenings", caseId],
    queryFn: () => apiFetch(`/screening/cases/${caseId}`),
    enabled: !!caseId,
  });

  const {
    data: auditData,
    isLoading: auditLoading,
    error: auditError,
    refetch: refetchAudit,
  } = useQuery({
    queryKey: ["case-audit", caseId],
    queryFn: () => apiFetch(`/cases/${caseId}/audit`),
    enabled: !!caseId,
  });

  const c = data as CaseDetail | undefined;
  const parties = (partiesData || []) as Party[];
  const checklist = checklistData as KycChecklist | undefined;
  const documents = (documentsData || []) as DocumentItem[];
  const screenings = (screeningsData || []) as ScreeningItem[];
  const audits = (auditData || []) as AuditItem[];

  const hasParties = parties.length > 0;
  const kycComplete = !!checklist?.is_complete;
  const hasScreening = screenings.length > 0;

  if (isLoading) {
    return <div>Chargement...</div>;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
        {(error as Error).message}
      </div>
    );
  }

  if (!c) {
    return <div>Dossier introuvable</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-xl font-semibold">{c.reference}</div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-gray-600">
            <StatusBadge status={c.status} />
            <span>Score: {c.risk_score}</span>
            <span>•</span>
            <span>Maj: {new Date(c.updated_at).toLocaleString("fr-FR")}</span>
          </div>
        </div>

        <Button
          variant="secondary"
          onClick={() => {
            refetch();
            refetchParties();
            refetchChecklist();
            refetchDocuments();
            refetchScreenings();
            refetchAudit();
          }}
        >
          Rafraîchir
        </Button>
      </div>

      {fromCreate && (
        <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800">
          Dossier créé avec succès. Étape suivante : ajoute les parties, puis génère le lien KYC.
        </div>
      )}

      <CaseWorkflowBanner
        hasParties={hasParties}
        kycComplete={kycComplete}
        hasScreening={hasScreening}
      />

      <Card>
        <CardHeader>
          <CardTitle>Résumé transaction</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 text-sm md:grid-cols-2">
          <div>
            <span className="text-gray-500">Montant :</span>{" "}
            {formatMoney(c.amount_fcfa)}
          </div>
          <div>
            <span className="text-gray-500">Mode paiement :</span>{" "}
            {c.payment_mode || "-"}
          </div>
          <div>
            <span className="text-gray-500">Origine des fonds :</span>{" "}
            {c.funds_origin || "-"}
          </div>
          <div>
            <span className="text-gray-500">Pays résidence :</span>{" "}
            {c.country_residence || "-"}
          </div>
          <div>
            <span className="text-gray-500">Profession :</span>{" "}
            {c.profession || "-"}
          </div>
          <div>
            <span className="text-gray-500">Créé :</span>{" "}
            {new Date(c.created_at).toLocaleString("fr-FR")}
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="parties" className="w-full">
        <TabsList className="flex flex-wrap">
          <TabsTrigger value="parties">Parties</TabsTrigger>
          <TabsTrigger value="kyc">KYC</TabsTrigger>
          <TabsTrigger value="screening">Screening</TabsTrigger>
          <TabsTrigger value="conformite">Conformité</TabsTrigger>
          <TabsTrigger value="audit">Audit</TabsTrigger>
          <TabsTrigger value="export">Export PDF</TabsTrigger>
        </TabsList>

        <TabsContent value="parties">
          <div className="grid gap-4">
            <AddPartyCard
              caseId={caseId}
              onDone={() => {
                refetchParties();
                refetchChecklist();
                refetch();
                refetchAudit();
              }}
            />

            <div className="grid gap-4 md:grid-cols-2">
              {partiesLoading && <div>Chargement...</div>}

              {partiesError && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {(partiesError as Error).message}
                </div>
              )}

              {!partiesLoading && !partiesError && parties.length === 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Parties</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm text-gray-500">
                    Aucune partie enregistrée.
                  </CardContent>
                </Card>
              )}

              {!partiesLoading &&
                !partiesError &&
                parties.map((p) => <PartyCard key={p.id} p={p} />)}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="kyc">
          <div className="grid gap-4">
            <OnboardingLinkCard
              caseId={caseId}
              parties={parties.map((p) => ({
                id: p.id,
                party_type: p.party_type,
                last_name: p.last_name,
                first_name: p.first_name,
              }))}
            />

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                {checklistLoading && <div>Chargement checklist...</div>}

                {checklistError && (
                  <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    {(checklistError as Error).message}
                  </div>
                )}

                {!checklistLoading && !checklistError && checklist && (
                  <KycChecklistCard data={checklist} />
                )}
              </div>

              <div>
                {documentsLoading && <div>Chargement documents...</div>}

                {documentsError && (
                  <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    {(documentsError as Error).message}
                  </div>
                )}

                {!documentsLoading && !documentsError && (
                  <DocumentListCard docs={documents} />
                )}
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="screening">
          <div className="grid gap-4 md:grid-cols-2">
            <ScreeningFormCard
              caseId={caseId}
              onDone={() => {
                refetch();
                refetchScreenings();
                refetchAudit();
              }}
            />

            <div>
              {screeningsLoading && <div>Chargement screenings...</div>}

              {screeningsError && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                  {(screeningsError as Error).message}
                </div>
              )}

              {!screeningsLoading && !screeningsError && (
                <ScreeningHistoryCard rows={screenings} />
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="conformite">
          <div className="grid gap-4 md:grid-cols-2">
            <ComplianceDecisionCard
              caseId={caseId}
              onDone={() => {
                refetch();
                refetchAudit();
              }}
            />

            <Card>
              <CardHeader>
                <CardTitle>Décision actuelle</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div>
                  <span className="text-gray-500">Décision :</span>{" "}
                  {c.compliance_decision || "-"}
                </div>
                <div>
                  <span className="text-gray-500">Commentaire :</span>{" "}
                  {c.compliance_comment || "-"}
                </div>
                <div>
                  <span className="text-gray-500">Date :</span>{" "}
                  {c.date_validation
                    ? new Date(c.date_validation).toLocaleString("fr-FR")
                    : "-"}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="audit">
          <div>
            {auditLoading && <div>Chargement audit...</div>}

            {auditError && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {(auditError as Error).message}
              </div>
            )}

            {!auditLoading && !auditError && (
              <AuditTrailCard rows={audits} />
            )}
          </div>
        </TabsContent>

        <TabsContent value="export">
          <ExportPdfCard caseId={c.id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}