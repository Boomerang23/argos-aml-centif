type WorkflowProps = {
  hasParties: boolean;
  kycComplete: boolean;
  hasScreening: boolean;
};

function StepItem({
  index,
  title,
  done,
  active,
}: {
  index: number;
  title: string;
  done: boolean;
  active: boolean;
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border bg-white px-4 py-3">
      <div
        className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold ${
          done
            ? "bg-emerald-600 text-white"
            : active
            ? "bg-black text-white"
            : "bg-gray-200 text-gray-700"
        }`}
      >
        {done ? "✓" : index}
      </div>

      <div className="text-sm font-medium">{title}</div>
    </div>
  );
}

export function CaseWorkflowBanner({
  hasParties,
  kycComplete,
  hasScreening,
}: WorkflowProps) {
  return (
    <div className="grid gap-3 md:grid-cols-4">
      <StepItem index={1} title="Transaction" done={true} active={false} />
      <StepItem index={2} title="Parties" done={hasParties} active={!hasParties} />
      <StepItem index={3} title="KYC / Onboarding" done={kycComplete} active={hasParties && !kycComplete} />
      <StepItem index={4} title="Vérifications" done={hasScreening} active={hasParties && kycComplete && !hasScreening} />
    </div>
  );
}