"use client";

import React from "react";

interface AuthGuardProps {
  children:      React.ReactNode;
  /** Kept for backwards compatibility — no longer enforced */
  requireAdmin?: boolean;
}

/**
 * Auth removed (2026-07-06): GlioTrack is now public-read.
 * This component previously redirected unauthenticated users to /login.
 * It now simply renders children unconditionally so all existing import
 * sites continue to compile without modification.
 */
export default function AuthGuard({ children }: AuthGuardProps) {
  return <>{children}</>;
}
