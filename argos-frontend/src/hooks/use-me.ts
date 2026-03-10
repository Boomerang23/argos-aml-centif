"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export function useMe() {
  return useQuery({
    queryKey: ["me-org"],
    queryFn: async () => {
      try {
        const org = await apiFetch("/admin/org/me");
        return { isAdmin: true, org };
      } catch {
        return { isAdmin: false, org: null };
      }
    },
  });
}