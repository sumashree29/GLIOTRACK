import { redirect } from "next/navigation";

// Root "/" redirects directly to the dashboard — no login required.
// Auth has been removed from all read endpoints (commit 7fa6cf7).
export default function RootPage() {
  redirect("/dashboard");
}
