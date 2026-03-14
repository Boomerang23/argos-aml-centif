"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { logout } from "@/lib/auth";
import { useMe } from "@/hooks/use-me";
import { Button } from "@/components/ui/button";

function NavItem({
  href,
  label,
}: {
  href: string;
  label: string;
}) {
  const pathname = usePathname();
  const active = pathname === href;

  return (
    <Link
      href={href}
      className={`block rounded-lg px-3 py-2 text-sm transition ${
        active ? "bg-black text-white" : "text-gray-700 hover:bg-gray-100"
      }`}
    >
      {label}
    </Link>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  const { data: meData, isPending, isError } = useMe();
  const isAdmin = !!meData?.isAdmin;

  useEffect(() => {
    if (isPending) return;
    if (isError || !meData) {
      router.replace("/login");
      return;
    }
    setReady(true);
  }, [isPending, isError, meData, router]);

  if (!ready) {
    return (
      <div className="flex h-screen items-center justify-center text-sm text-gray-500">
        Chargement...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto flex max-w-6xl">
        <aside className="hidden w-64 flex-col border-r bg-white p-4 md:flex">
          <div className="mb-6">
            <div className="text-lg font-semibold">ARGOS AML</div>
            <div className="text-xs text-gray-500">Immobilier CI</div>
          </div>

          <nav className="space-y-1">
            <NavItem href="/dashboard" label="Dashboard" />
            <NavItem href="/cases" label="Dossiers" />
            {isAdmin && <NavItem href="/admin/users" label="Admin" />}
            <NavItem href="/profile" label="Profil" />
          </nav>

          <div className="mt-auto pt-6">
            <Button
              variant="outline"
              className="w-full"
              onClick={() => logout()}
            >
              Se déconnecter
            </Button>
          </div>
        </aside>

        <main className="flex-1 p-4 md:p-8">
          <div className="mb-6 flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Plateforme conformité AML
            </div>

            <div className="md:hidden">
              <Button variant="outline" onClick={() => logout()}>
                Logout
              </Button>
            </div>
          </div>

          {children}
        </main>
      </div>
    </div>
  );
}