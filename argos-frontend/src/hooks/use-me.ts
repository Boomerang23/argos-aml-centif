"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const data = await apiFetch<{
        email: string;
        role: "ADMIN" | "AGENT" | "COMPLIANCE_OFFICER";
        org_id: number;
      }>("/auth/me");
      return {
        isAdmin: data.role === "ADMIN",
        user: data,
      };
    },
  });
}
