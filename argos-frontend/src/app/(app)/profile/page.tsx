"use client";

import { logout } from "@/lib/auth";
import { useMe } from "@/hooks/use-me";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function ProfilePage() {
  const { data: meData } = useMe();

  return (
    <div className="space-y-4">
      <div>
        <div className="text-xl font-semibold">Profil</div>
        <div className="text-sm text-gray-500">
          Informations de session.
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Session</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div>
            <span className="text-gray-500">Session :</span>{" "}
            {meData?.user ? `Active (${meData.user.email})` : "Chargement…"}
          </div>

          <Button variant="outline" onClick={() => logout()}>
            Se déconnecter
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}