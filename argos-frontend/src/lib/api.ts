const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function apiFetch(
  path: string,
  options: Omit<RequestInit, "body"> & { body?: unknown } = {}
) {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;

  const headers = new Headers(options.headers || {});
  let body: BodyInit | undefined;

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

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
  });

  const contentType = res.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");

  if (!res.ok) {
    const errorBody = isJson ? await res.json() : await res.text();
    throw new Error(
      typeof errorBody === "string"
        ? errorBody
        : JSON.stringify(errorBody)
    );
  }

  return isJson ? res.json() : res.text();
}