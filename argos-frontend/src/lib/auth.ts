/**
 * Auth helpers. JWT is stored in an HTTP-only cookie set by the API;
 * we never read or write the token in the frontend (XSS-safe).
 */

export function logout() {
  // Call API to clear the cookie, then redirect (cookie is sent automatically)
  const base =
    typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_BASE_URL
      ? process.env.NEXT_PUBLIC_API_BASE_URL.replace(/\/+$/, "")
      : "http://localhost:8000";
  fetch(`${base}/auth/logout`, { method: "POST", credentials: "include" }).finally(
    () => {
      window.location.href = "/login";
    }
  );
}

/**
 * Client-side we cannot read the HTTP-only cookie.
 * Use useMe() and check data/error to know if the user is authenticated.
 */
export function isAuthenticated(): boolean {
  return false; // unknown without a round-trip; rely on useMe() instead
}
