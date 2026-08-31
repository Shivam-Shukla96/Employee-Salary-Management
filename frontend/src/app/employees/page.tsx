"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { api, EmployeeListResponse } from "@/lib/api";
import { useDebounce } from "@/hooks/useDebounce";

const STATUS_COLORS: Record<string, string> = {
  active: "bg-[var(--color-success)]/10 text-[var(--color-success)]",
  inactive: "bg-[var(--color-danger)]/10 text-[var(--color-danger)]",
};

function formatCurrency(amount: string | null, currency: string): string {
  if (!amount) return "\u2014";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency || "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(parseFloat(amount));
}

interface SortHeaderProps {
  label: string;
  field: string;
  currentSort: string;
  currentOrder: string;
  onSort: (field: string) => void;
}

function SortHeader({ label, field, currentSort, currentOrder, onSort }: SortHeaderProps) {
  const isActive = currentSort === field;
  return (
    <th
      className="text-left px-4 py-3 text-[var(--color-text-muted)] font-medium cursor-pointer hover:text-[var(--color-text)] transition-colors select-none"
      onClick={() => onSort(field)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {isActive && (
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
            {currentOrder === "asc" ? (
              <path d="M7 14l5-5 5 5z" />
            ) : (
              <path d="M7 10l5 5 5-5z" />
            )}
          </svg>
        )}
      </span>
    </th>
  );
}

function EmployeesList() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [data, setData] = useState<EmployeeListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Local search input (for debouncing)
  const [searchInput, setSearchInput] = useState(searchParams.get("search") || "");
  const debouncedSearch = useDebounce(searchInput, 400);

  // Read other filters from URL
  const country = searchParams.get("country") || "";
  const department = searchParams.get("department") || "";
  const status = searchParams.get("status") || "";
  const page = parseInt(searchParams.get("page") || "1", 10);
  const sortBy = searchParams.get("sort_by") || "";
  const sortOrder = searchParams.get("sort_order") || "asc";
  const pageSize = 20;

  // Sync debounced search to URL
  useEffect(() => {
    const currentUrlSearch = searchParams.get("search") || "";
    if (debouncedSearch !== currentUrlSearch) {
      updateFilters({ search: debouncedSearch });
    }
  }, [debouncedSearch]);

  function updateFilters(updates: Record<string, string | number>) {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(updates).forEach(([k, v]) => {
      if (v === "" || v === undefined || v === null) {
        params.delete(k);
      } else {
        params.set(k, String(v));
      }
    });
    // Reset to page 1 when non-page filters change
    if (!("page" in updates)) {
      params.delete("page");
    }
    router.replace(`/employees?${params.toString()}`, { scroll: false });
  }

  function handleSort(field: string) {
    const newOrder = sortBy === field && sortOrder === "asc" ? "desc" : "asc";
    updateFilters({ sort_by: field, sort_order: newOrder });
  }

  const fetchEmployees = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { page, page_size: pageSize };
      if (debouncedSearch) params.search = debouncedSearch;
      if (country) params.country = country;
      if (department) params.department = department;
      if (status) params.status = status;
      if (sortBy) {
        params.sort_by = sortBy;
        params.sort_order = sortOrder;
      }

      const result = await api.listEmployees(params);
      setData(result);
    } catch (err: any) {
      setError(err.message || "Failed to load employees");
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearch, country, department, status, sortBy, sortOrder]);

  useEffect(() => {
    fetchEmployees();
  }, [fetchEmployees]);

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Employees</h1>
          <p className="text-[var(--color-text-muted)] text-sm mt-1">
            {data ? `${data.total} employees found` : "Loading..."}
          </p>
        </div>
        <div>
          <Link
            href="/employees/new"
            className="px-4 py-2.5 bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white rounded-lg text-sm font-medium transition-colors inline-block"
          >
            + Add Employee
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="glass rounded-xl p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input
            type="text"
            placeholder="Search by name, ID, or email..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary)] transition-colors"
          />
          <select
            value={department}
            onChange={(e) => updateFilters({ department: e.target.value })}
            className="px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)] transition-colors"
          >
            <option value="">All Departments</option>
            {["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations", "Support", "Product"].map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
          <select
            value={country}
            onChange={(e) => updateFilters({ country: e.target.value })}
            className="px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)] transition-colors"
          >
            <option value="">All Countries</option>
            {["US", "UK", "India", "Germany", "Japan", "Brazil", "Canada", "Australia"].map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select
            value={status}
            onChange={(e) => updateFilters({ status: e.target.value })}
            className="px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)] transition-colors"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-[var(--color-danger)]/10 border border-[var(--color-danger)]/20 rounded-lg text-[var(--color-danger)] text-sm">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <SortHeader label="ID" field="employee_id" currentSort={sortBy} currentOrder={sortOrder} onSort={handleSort} />
                <SortHeader label="Name" field="full_name" currentSort={sortBy} currentOrder={sortOrder} onSort={handleSort} />
                <SortHeader label="Department" field="department" currentSort={sortBy} currentOrder={sortOrder} onSort={handleSort} />
                <SortHeader label="Country" field="country" currentSort={sortBy} currentOrder={sortOrder} onSort={handleSort} />
                <SortHeader label="Job Title" field="job_title" currentSort={sortBy} currentOrder={sortOrder} onSort={handleSort} />
                <th className="text-right px-4 py-3 text-[var(--color-text-muted)] font-medium">Salary</th>
                <SortHeader label="Status" field="status" currentSort={sortBy} currentOrder={sortOrder} onSort={handleSort} />
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 15 }).map((_, i) => (
                  <tr key={i} className="border-b border-[var(--color-border)]">
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-[var(--color-border)] rounded animate-pulse-subtle" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-[var(--color-text-muted)]">
                    No employees found matching your criteria.
                  </td>
                </tr>
              ) : (
                data?.items.map((emp) => (
                  <tr
                    key={emp.id}
                    className="border-b border-[var(--color-border)] hover:bg-[var(--color-surface-hover)] transition-colors cursor-pointer"
                  >
                    <td className="px-4 py-3">
                      <Link href={`/employees/${emp.id}`} className="text-[var(--color-primary)] hover:underline font-mono text-xs">
                        {emp.employee_id}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <Link href={`/employees/${emp.id}`} className="hover:text-[var(--color-primary)] transition-colors">
                        <div className="font-medium">{emp.full_name}</div>
                        <div className="text-xs text-[var(--color-text-muted)]">{emp.email}</div>
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{emp.department}</td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{emp.country}</td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{emp.job_title}</td>
                    <td className="px-4 py-3 text-right font-mono">
                      {emp.current_salary
                        ? formatCurrency(emp.current_salary.base_salary, emp.current_salary.currency)
                        : "\u2014"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[emp.status] || ""}`}>
                        {emp.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--color-border)]">
            <p className="text-xs text-[var(--color-text-muted)]">
              Page {data.page} of {data.total_pages} ({data.total} total)
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => updateFilters({ page: Math.max(1, page - 1) })}
                disabled={page <= 1}
                className="px-3 py-1.5 text-xs border border-[var(--color-border)] rounded-lg hover:bg-[var(--color-surface-hover)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>
              <button
                onClick={() => updateFilters({ page: Math.min(data.total_pages, page + 1) })}
                disabled={page >= data.total_pages}
                className="px-3 py-1.5 text-xs border border-[var(--color-border)] rounded-lg hover:bg-[var(--color-surface-hover)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function EmployeesPage() {
  return (
    <Suspense fallback={
      <div className="animate-fade-in space-y-6">
        <div className="h-8 w-48 bg-[var(--color-border)] rounded animate-pulse-subtle" />
        <div className="glass rounded-xl p-4 h-16 animate-pulse-subtle" />
        <div className="glass rounded-xl min-h-[600px] animate-pulse-subtle" />
      </div>
    }>
      <EmployeesList />
    </Suspense>
  );
}
