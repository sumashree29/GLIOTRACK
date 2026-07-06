"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Users, Shield, Brain, ChevronRight } from "lucide-react";

interface NavItem {
  href: string; label: string; icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: <LayoutDashboard size={15} /> },
  { href: "/patients",  label: "Patients",  icon: <Users size={15} /> },
  { href: "/admin",     label: "Admin",     icon: <Shield size={15} /> },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className="fixed inset-y-0 left-0 z-30 w-[220px] flex flex-col"
      style={{ backgroundColor: "var(--surface)", borderRight: "1px solid var(--border)" }}
    >
      {/* Logo */}
      <div
        className="flex items-center gap-3 px-5 h-[57px] shrink-0"
        style={{ borderBottom: "1px solid var(--border)" }}
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-lg shrink-0 bg-gradient-to-br from-[#4a90d9] to-[#2563a8] shadow-[0_0_14px_rgba(74,144,217,0.4)]">
          <Brain size={15} className="text-white" />
        </div>
        <div className="min-w-0">
          <p className="text-[13px] font-bold tracking-tight leading-none" style={{ color: "var(--text)" }}>GLIOTRACK</p>
          <p className="text-[10px] mt-0.5 leading-none truncate" style={{ color: "var(--muted)" }}>Brain Tumour Analysis</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-0.5">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className="group flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-150"
              style={{
                backgroundColor: active ? "var(--surface-2)" : "transparent",
                border: `1px solid ${active ? "var(--border)" : "transparent"}`,
                color: active ? "var(--text)" : "var(--muted)",
              }}
            >
              <span style={{ color: active ? "var(--blue)" : "var(--muted)" }}>{item.icon}</span>
              <span className="flex-1 truncate">{item.label}</span>
              {active && <ChevronRight size={11} style={{ color: "var(--muted)" }} />}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}