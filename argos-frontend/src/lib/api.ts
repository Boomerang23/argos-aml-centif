import { logout } from "@/lib/auth";

const API_BASE_URL_KEY = "NEXT_PUBLIC_API_BASE_URL";

function getApiBaseUrl(): string {
  const raw =
    typeof process !== "undefined"
      ? process.env.NEXT_PUBLIC_API_BASE_URL
      : undefined;
  const isDev =
    typeof process !== "undefined" &&
    process.env.NODE_ENV === "development";

  let base = (raw ?? "").trim();
  if (!base && isDev) {
    base = "http://localhost:8000";
  }
  if (!base) {
    throw new Error(
      `${API_BASE_URL_KEY} is not set or empty. Set it in .env.local (e.g. ${API_BASE_URL_KEY}=http://localhost:8000) or as build arg in Docker.`
    );
  }
  if (!base.startsWith("http://") && !base.startsWith("https://")) {
    throw new Error(
      `${API_BASE_URL_KEY} must be a valid URL starting with http:// or https://. Got: ${base}`
    );
  }
  return base.replace(/\/+$/, "");
}

/**
 * Returns the validated API base URL (no trailing slash).
 * Throws if NEXT_PUBLIC_API_BASE_URL is missing, empty, or not http(s).
 * In development, falls back to http://localhost:8000 when unset.
 */
export function getApiBaseUrlOrThrow(): string {
  return getApiBaseUrl();
}

export async function apiFetch(
  path: string,
  options: Omit<RequestInit, "body"> & { body?: unknown } = {}
) {
  const API_BASE = getApiBaseUrl();

  const headers = new Headers(options.headers || {});
  let body: BodyInit | undefined;

  if (options.body !== undefined && options.body !== null) {
    if (
      typeof options.body === "string" ||
      options.body instanceof FormData ||
      options.body instanceof URLSearchParams ||
      options.body instanceof Blob
    ) {
      body = options.body;
    } else {
      headers.set("Content-Type", "application/json");
      body = JSON.stringify(options.body);
    }
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body,
    credentials: "include",
  });

  const contentType = res.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");

  if (!res.ok) {
    if (res.status === 401 && typeof window !== "undefined") {
      logout();
    }
    const errorBody = isJson ? await res.json() : await res.text();
    throw new Error(
      typeof errorBody === "string"
        ? errorBody
        : JSON.stringify(errorBody)
    );
  }

  return isJson ? res.json() : res.text();
}
