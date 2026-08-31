"use client";

import { useEffect, useState } from "react";
import { api, AnalyticsResponse } from "@/lib/api";

function formatUSD(amount: string): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(parseFloat(amount));
}

function formatCompact(amount: string): string {
  const num = parseFloat(amount);
  if (num >= 1_000_000) return `$${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `$${(num / 1_000).toFixed(0)}K`;
  return `$${num.toFixed(0)}`;
}

function BarChart({ data, labelKey, valueKey, maxValue }: {
  data: Record<string, any>[];
  labelKey: string;
  valueKey: string;
  maxValue: number;
}) {
  return (
    <div className="space-y-2.5">
      {data.map((item, i) => {
        const value = parseFloat(item[valueKey]);
        const pct = maxValue > 0 ? (value / maxValue) * 100 : 0;
        return (
          <div key={i} className="group">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-[var(--color-text)]">{item[labelKey]}</span>
              <span className="font-mono text-[var(--color-text-muted)] text-xs">{formatUSD(item[valueKey])}</span>
            </div>
            <div className="h-2 bg-[var(--color-bg)] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 ease-out"
                style={{
                  width: `${pct}%`,
                  background: `linear-gradient(90deg, var(--color-primary), var(--color-accent))`,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const result = await api.getAnalytics();
        setData(result);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="animate-fade-in space-y-6">
        <div className="h-8 w-48 bg-[var(--color-border)] rounded animate-pulse-subtle" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="glass rounded-xl p-5 h-28 animate-pulse-subtle" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-[var(--color-danger)]/10 border border-[var(--color-danger)]/20 rounded-xl text-[var(--color-danger)]">
        Failed to load analytics: {error}
      </div>
    );
  }

  if (!data) return null;

  const { summary, by_department, by_country, by_role } = data;
  const maxDeptPayroll = Math.max(...by_department.map((d) => parseFloat(d.total_payroll_usd)), 1);
  const maxCountryPayroll = Math.max(...by_country.map((c) => parseFloat(c.total_payroll_usd)), 1);
  const maxDeptAvg = Math.max(...by_department.map((d) => parseFloat(d.avg_salary_usd)), 1);
  const maxCountryAvg = Math.max(...by_country.map((c) => parseFloat(c.avg_salary_usd)), 1);
  const maxRoleAvg = Math.max(...(by_role || []).map((r) => parseFloat(r.avg_salary_usd)), 1);

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-[var(--color-text-muted)] text-sm mt-1">
          Salary insights across the organization (all values normalized to USD)
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {[
          { label: "Total Employees", value: summary.total_employees.toString(), format: "number", color: "var(--color-primary)" },
          { label: "Avg Salary", value: summary.avg_salary_usd, format: "usd", color: "var(--color-accent)" },
          { label: "Median Salary", value: summary.median_salary_usd || "0", format: "usd", color: "#38bdf8" },
          { label: "Total Payroll", value: summary.total_payroll_usd, format: "compact", color: "var(--color-success)" },
          { label: "Salary Range", value: `${formatCompact(summary.min_salary_usd)} – ${formatCompact(summary.max_salary_usd)}`, format: "raw", color: "var(--color-warning)" },
        ].map((kpi) => (
          <div key={kpi.label} className="glass rounded-xl p-5">
            <p className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider mb-2">{kpi.label}</p>
            <p className="text-2xl font-bold" style={{ color: kpi.color }}>
              {kpi.format === "usd"
                ? formatUSD(kpi.value)
                : kpi.format === "compact"
                ? formatCompact(kpi.value)
                : kpi.value}
            </p>
          </div>
        ))}
      </div>

      {/* Salary Range Distribution */}
      <div className="glass rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-1">Salary Range by Department</h2>
        <p className="text-xs text-[var(--color-text-muted)] mb-5">Min–Max spread with average marker</p>
        <div className="space-y-4">
          {[...by_department].sort((a, b) => parseFloat(b.max_salary_usd) - parseFloat(a.max_salary_usd)).map((dept) => {
            const globalMax = Math.max(...by_department.map((d) => parseFloat(d.max_salary_usd)), 1);
            const min = parseFloat(dept.min_salary_usd);
            const max = parseFloat(dept.max_salary_usd);
            const avg = parseFloat(dept.avg_salary_usd);
            const leftPct = (min / globalMax) * 100;
            const widthPct = ((max - min) / globalMax) * 100;
            const avgPct = (avg / globalMax) * 100;

            return (
              <div key={dept.department}>
                <div className="flex items-center justify-between text-sm mb-1.5">
                  <span>{dept.department}</span>
                  <span className="text-xs text-[var(--color-text-muted)] font-mono">
                    {formatCompact(dept.min_salary_usd)} – {formatCompact(dept.max_salary_usd)}
                  </span>
                </div>
                <div className="relative h-3 bg-[var(--color-bg)] rounded-full">
                  {/* Range bar */}
                  <div
                    className="absolute h-full rounded-full opacity-40"
                    style={{
                      left: `${leftPct}%`,
                      width: `${Math.max(widthPct, 0.5)}%`,
                      background: "linear-gradient(90deg, var(--color-primary), var(--color-accent))",
                    }}
                  />
                  {/* Average marker */}
                  <div
                    className="absolute top-0 w-1 h-full bg-[var(--color-warning)] rounded-full"
                    style={{ left: `${avgPct}%` }}
                    title={`Avg: ${formatUSD(dept.avg_salary_usd)}`}
                  />
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex items-center gap-4 mt-4 text-xs text-[var(--color-text-muted)]">
          <div className="flex items-center gap-1.5">
            <div className="w-6 h-2 rounded-full opacity-40" style={{ background: "linear-gradient(90deg, var(--color-primary), var(--color-accent))" }} />
            <span>Min–Max Range</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-1 h-3 bg-[var(--color-warning)] rounded-full" />
            <span>Average</span>
          </div>
        </div>
      </div>

      {/* Department & Country side-by-side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Department Breakdown */}
        <div className="glass rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-1">Average Salary by Department</h2>
          <p className="text-xs text-[var(--color-text-muted)] mb-5">Normalized to USD</p>
          <BarChart
            data={[...by_department].sort((a, b) => parseFloat(b.avg_salary_usd) - parseFloat(a.avg_salary_usd))}
            labelKey="department"
            valueKey="avg_salary_usd"
            maxValue={maxDeptAvg}
          />
        </div>

        {/* Country Breakdown */}
        <div className="glass rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-1">Average Salary by Country</h2>
          <p className="text-xs text-[var(--color-text-muted)] mb-5">Normalized to USD</p>
          <BarChart
            data={[...by_country].sort((a, b) => parseFloat(b.avg_salary_usd) - parseFloat(a.avg_salary_usd))}
            labelKey="country"
            valueKey="avg_salary_usd"
            maxValue={maxCountryAvg}
          />
        </div>
      </div>

      {/* Payroll Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-1">Total Payroll by Department</h2>
          <p className="text-xs text-[var(--color-text-muted)] mb-5">Annual payroll in USD</p>
          <BarChart
            data={[...by_department].sort((a, b) => parseFloat(b.total_payroll_usd) - parseFloat(a.total_payroll_usd))}
            labelKey="department"
            valueKey="total_payroll_usd"
            maxValue={maxDeptPayroll}
          />
        </div>

        <div className="glass rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-1">Total Payroll by Country</h2>
          <p className="text-xs text-[var(--color-text-muted)] mb-5">Annual payroll in USD</p>
          <BarChart
            data={[...by_country].sort((a, b) => parseFloat(b.total_payroll_usd) - parseFloat(a.total_payroll_usd))}
            labelKey="country"
            valueKey="total_payroll_usd"
            maxValue={maxCountryPayroll}
          />
        </div>
      </div>

      {/* Department Detail Table */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-[var(--color-border)]">
          <h2 className="text-lg font-semibold">Department Details</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="text-left px-4 py-3 text-[var(--color-text-muted)] font-medium">Department</th>
                <th className="text-right px-4 py-3 text-[var(--color-text-muted)] font-medium">Employees</th>
                <th className="text-right px-4 py-3 text-[var(--color-text-muted)] font-medium">Avg Salary</th>
                <th className="text-right px-4 py-3 text-[var(--color-text-muted)] font-medium">Min</th>
                <th className="text-right px-4 py-3 text-[var(--color-text-muted)] font-medium">Max</th>
                <th className="text-right px-4 py-3 text-[var(--color-text-muted)] font-medium">Total Payroll</th>
              </tr>
            </thead>
            <tbody>
              {by_department.map((dept) => (
                <tr key={dept.department} className="border-b border-[var(--color-border)] hover:bg-[var(--color-surface-hover)] transition-colors">
                  <td className="px-4 py-3 font-medium">{dept.department}</td>
                  <td className="px-4 py-3 text-right text-[var(--color-text-muted)]">{dept.employee_count}</td>
                  <td className="px-4 py-3 text-right font-mono">{formatUSD(dept.avg_salary_usd)}</td>
                  <td className="px-4 py-3 text-right font-mono text-[var(--color-text-muted)]">{formatUSD(dept.min_salary_usd)}</td>
                  <td className="px-4 py-3 text-right font-mono text-[var(--color-text-muted)]">{formatUSD(dept.max_salary_usd)}</td>
                  <td className="px-4 py-3 text-right font-mono">{formatCompact(dept.total_payroll_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Country Detail Table */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-[var(--color-border)]">
          <h2 className="text-lg font-semibold">Country Details</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="text-left px-4 py-3 text-[var(--color-text-muted)] font-medium">Country</th>
                <th className="text-center px-4 py-3 text-[var(--color-text-muted)] font-medium">Currency</th>
                <th className="text-right px-4 py-3 text-[var(--color-text-muted)] font-medium">Employees</th>
                <th className="text-right px-4 py-3 text-[var(--color-text-muted)] font-medium">Avg (Local)</th>
                <th className="text-right px-4 py-3 text-[var(--color-text-muted)] font-medium">Avg (USD)</th>
                <th className="text-right px-4 py-3 text-[var(--color-text-muted)] font-medium">Total Payroll</th>
              </tr>
            </thead>
            <tbody>
              {by_country.map((c) => (
                <tr key={c.country} className="border-b border-[var(--color-border)] hover:bg-[var(--color-surface-hover)] transition-colors">
                  <td className="px-4 py-3 font-medium">{c.country}</td>
                  <td className="px-4 py-3 text-center text-[var(--color-text-muted)]">{c.currency}</td>
                  <td className="px-4 py-3 text-right text-[var(--color-text-muted)]">{c.employee_count}</td>
                  <td className="px-4 py-3 text-right font-mono text-[var(--color-text-muted)]">
                    {new Intl.NumberFormat("en-US", { style: "currency", currency: c.currency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(parseFloat(c.avg_salary_local))}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">{formatUSD(c.avg_salary_usd)}</td>
                  <td className="px-4 py-3 text-right font-mono">{formatCompact(c.total_payroll_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Role Breakdown */}
      {by_role && by_role.length > 0 && (
        <>
          <div className="glass rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-1">Average Salary by Role</h2>
            <p className="text-xs text-[var(--color-text-muted)] mb-5">Normalized to USD, sorted by compensation</p>
            <BarChart
              data={[...by_role].sort((a, b) => parseFloat(b.avg_salary_usd) - parseFloat(a.avg_salary_usd))}
              labelKey="job_title"
              valueKey="avg_salary_usd"
              maxValue={maxRoleAvg}
            />
          </div>

          {/* Role Detail Table */}
          <div className="glass rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-[var(--color-border)]">
              <h2 className="text-lg font-semibold">Role Details</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--color-border)]">
                    <th className="text-left px-4 py-3 text-[var(--color-text-muted)] font-medium">Job Title</th>
                    <th className="text-right px-4 py-3 text-[var(--color-text-muted)] font-medium">Employees</th>
                    <th className="text-right px-4 py-3 text-[var(--color-text-muted)] font-medium">Avg Salary</th>
                    <th className="text-right px-4 py-3 text-[var(--color-text-muted)] font-medium">Min</th>
                    <th className="text-right px-4 py-3 text-[var(--color-text-muted)] font-medium">Max</th>
                  </tr>
                </thead>
                <tbody>
                  {[...by_role].sort((a, b) => parseFloat(b.avg_salary_usd) - parseFloat(a.avg_salary_usd)).map((role) => (
                    <tr key={role.job_title} className="border-b border-[var(--color-border)] hover:bg-[var(--color-surface-hover)] transition-colors">
                      <td className="px-4 py-3 font-medium">{role.job_title}</td>
                      <td className="px-4 py-3 text-right text-[var(--color-text-muted)]">{role.employee_count}</td>
                      <td className="px-4 py-3 text-right font-mono">{formatUSD(role.avg_salary_usd)}</td>
                      <td className="px-4 py-3 text-right font-mono text-[var(--color-text-muted)]">{formatUSD(role.min_salary_usd)}</td>
                      <td className="px-4 py-3 text-right font-mono text-[var(--color-text-muted)]">{formatUSD(role.max_salary_usd)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
