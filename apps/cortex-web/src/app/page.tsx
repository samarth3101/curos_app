import { redirect } from "next/navigation";

/**
 * Root page — redirects to the dashboard.
 * Unauthenticated users will be redirected to /login by middleware (future).
 */
export default function RootPage() {
  redirect("/dashboard");
}
