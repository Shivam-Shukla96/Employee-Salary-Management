"use client";

import Link from "next/link";

export default function Home() {
  return (
    <div className="animate-fade-in">
      <h1 className="text-2xl font-bold mb-2">Welcome to ACME Salary Manager</h1>
      <p className="text-[var(--color-text-muted)] mb-8">
        Manage employees, track salary changes, and view workforce analytics.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          href="/employees"
          className="glass rounded-xl p-6 hover:border-[var(--color-primary)]/30 transition-all duration-200 group"
        >
          <div className="w-10 h-10 rounded-lg bg-[var(--color-primary)]/10 flex items-center justify-center mb-4 group-hover:bg-[var(--color-primary)]/20 transition-colors">
            <svg className="w-5 h-5 text-[var(--color-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold mb-1">Employees</h2>
          <p className="text-sm text-[var(--color-text-muted)]">
            View, search, and manage employee records
          </p>
        </Link>

        <Link
          href="/analytics"
          className="glass rounded-xl p-6 hover:border-[var(--color-primary)]/30 transition-all duration-200 group"
        >
          <div className="w-10 h-10 rounded-lg bg-[var(--color-accent)]/10 flex items-center justify-center mb-4 group-hover:bg-[var(--color-accent)]/20 transition-colors">
            <svg className="w-5 h-5 text-[var(--color-accent)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold mb-1">Analytics</h2>
          <p className="text-sm text-[var(--color-text-muted)]">
            Salary insights by department and country
          </p>
        </Link>

        <Link
          href="/employees/new"
          className="glass rounded-xl p-6 hover:border-[var(--color-success)]/30 transition-all duration-200 group"
        >
          <div className="w-10 h-10 rounded-lg bg-[var(--color-success)]/10 flex items-center justify-center mb-4 group-hover:bg-[var(--color-success)]/20 transition-colors">
            <svg className="w-5 h-5 text-[var(--color-success)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold mb-1">Add Employee</h2>
          <p className="text-sm text-[var(--color-text-muted)]">
            Create a new employee record with salary
          </p>
        </Link>
      </div>
    </div>
  );
}
