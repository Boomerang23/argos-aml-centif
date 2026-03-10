import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function KpiCard({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-gray-500">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-semibold">{value}</div>
        {subtitle && (
          <div className="mt-1 text-xs text-gray-500">{subtitle}</div>
        )}
      </CardContent>
    </Card>
  );
}