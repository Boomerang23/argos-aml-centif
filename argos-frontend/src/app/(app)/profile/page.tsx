"use client";

import { getToken, logout } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function ProfilePage() {
  const token = getToken();

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
            <span className="text-gray-500">Token présent :</span>{" "}
            {token ? "Oui" : "Non"}
          </div>

          <Button variant="outline" onClick={() => logout()}>
            Se déconnecter
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}