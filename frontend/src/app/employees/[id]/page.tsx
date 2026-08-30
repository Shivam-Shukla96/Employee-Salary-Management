"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, Employee, SalaryRecord } from "@/lib/api";

function formatCurrency(amount: string | null, currency: string): string {
  if (!amount) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency || "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(parseFloat(amount));
}

export default function EmployeeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [employee, setEmployee] = useState<Employee | null>(null);
  const [history, setHistory] = useState<SalaryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Salary update form
  const [showSalaryForm, setShowSalaryForm] = useState(false);
  const [salaryForm, setSalaryForm] = useState({
    base_salary: "",
    currency: "USD",
    effective_date: new Date().toISOString().split("T")[0],
  });
  const [submitting, setSubmitting] = useState(false);

  // Edit form
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    full_name: "",
    email: "",
    department: "",
    job_title: "",
    country: "",
  });

  useEffect(() => {
    loadEmployee();
  }, [id]);

  async function loadEmployee() {
    try {
      setLoading(true);
      const [emp, salaryData] = await Promise.all([
        api.getEmployee(id),
        api.getSalaryHistory(id),
      ]);
      setEmployee(emp);
      setHistory(salaryData.records);
      setEditForm({
        full_name: emp.full_name,
        email: emp.email,
        department: emp.department,
        job_title: emp.job_title,
        country: emp.country,
      });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSalaryUpdate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.updateSalary(id, salaryForm);
      setShowSalaryForm(false);
      setSalaryForm({ base_salary: "", currency: "USD", effective_date: new Date().toISOString().split("T")[0] });
      await loadEmployee();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUpdate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.updateEmployee(id, editForm);
      setEditing(false);
      await loadEmployee();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeactivate() {
    if (!confirm("Are you sure you want to deactivate this employee?")) return;
    try {
      await api.deleteEmployee(id);
      await loadEmployee();
    } catch (err: any) {
      setError(err.message);
    }
  }

  if (loading) {
    return (
      <div className="animate-fade-in space-y-6">
        <div className="h-8 w-48 bg-[var(--color-border)] rounded animate-pulse-subtle" />
        <div className="glass rounded-xl p-6 space-y-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-5 bg-[var(--color-border)] rounded animate-pulse-subtle" style={{ width: `${60 + Math.random() * 30}%` }} />
          ))}
        </div>
      </div>
    );
  }

  if (error && !employee) {
    return (
      <div className="p-6 bg-[var(--color-danger)]/10 border border-[var(--color-danger)]/20 rounded-xl text-[var(--color-danger)]">
        {error}
      </div>
    );
  }

  if (!employee) return null;

  return (
    <div className="animate-fade-in max-w-4xl">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-[var(--color-text-muted)] mb-6">
        <Link href="/employees" className="hover:text-[var(--color-text)] transition-colors">Employees</Link>
        <span>/</span>
        <span className="text-[var(--color-text)]">{employee.full_name}</span>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-[var(--color-danger)]/10 border border-[var(--color-danger)]/20 rounded-lg text-[var(--color-danger)] text-sm">
          {error}
        </div>
      )}

      {/* Employee Info */}
      <div className="glass rounded-xl p-6 mb-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">{employee.full_name}</h1>
            <p className="text-[var(--color-text-muted)] text-sm mt-1">{employee.employee_id} &middot; {employee.email}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setEditing(!editing)}
              className="px-3 py-1.5 text-xs border border-[var(--color-border)] rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors"
            >
              {editing ? "Cancel" : "Edit"}
            </button>
            {employee.status === "active" && (
              <button
                onClick={handleDeactivate}
                className="px-3 py-1.5 text-xs border border-[var(--color-danger)]/30 text-[var(--color-danger)] rounded-lg hover:bg-[var(--color-danger)]/10 transition-colors"
              >
                Deactivate
              </button>
            )}
          </div>
        </div>

        {editing ? (
          <form onSubmit={handleUpdate} className="grid grid-cols-2 gap-4">
            {(["full_name", "email", "department", "job_title", "country"] as const).map((field) => (
              <div key={field}>
                <label className="block text-xs text-[var(--color-text-muted)] mb-1 capitalize">{field.replace("_", " ")}</label>
                <input
                  type="text"
                  value={editForm[field]}
                  onChange={(e) => setEditForm({ ...editForm, [field]: e.target.value })}
                  className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm focus:outline-none focus:border-[var(--color-primary)]"
                />
              </div>
            ))}
            <div className="col-span-2">
              <button type="submit" disabled={submitting} className="px-4 py-2 bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
                {submitting ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </form>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-y-4 gap-x-8">
            {[
              ["Department", employee.department],
              ["Job Title", employee.job_title],
              ["Country", employee.country],
              ["Status", employee.status],
              ["Joining Date", employee.joining_date],
              ["Current Salary", employee.current_salary ? `${formatCurrency(employee.current_salary.base_salary, employee.current_salary.currency)} (${formatCurrency(employee.current_salary.salary_usd, "USD")} USD)` : "—"],
            ].map(([label, value]) => (
              <div key={label}>
                <p className="text-xs text-[var(--color-text-muted)]">{label}</p>
                <p className="text-sm font-medium mt-0.5">{value}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Salary History */}
      <div className="glass rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Salary History</h2>
          <button
            onClick={() => setShowSalaryForm(!showSalaryForm)}
            className="px-3 py-1.5 text-xs bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white rounded-lg transition-colors"
          >
            {showSalaryForm ? "Cancel" : "+ Update Salary"}
          </button>
        </div>

        {showSalaryForm && (
          <form onSubmit={handleSalaryUpdate} className="mb-6 p-4 bg-[var(--color-bg)] rounded-lg border border-[var(--color-border)]">
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-[var(--color-text-muted)] mb-1">Base Salary</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={salaryForm.base_salary}
                  onChange={(e) => setSalaryForm({ ...salaryForm, base_salary: e.target.value })}
                  className="w-full px-3 py-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg text-sm focus:outline-none focus:border-[var(--color-primary)]"
                  placeholder="85000"
                />
              </div>
              <div>
                <label className="block text-xs text-[var(--color-text-muted)] mb-1">Currency</label>
                <select
                  value={salaryForm.currency}
                  onChange={(e) => setSalaryForm({ ...salaryForm, currency: e.target.value })}
                  className="w-full px-3 py-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg text-sm focus:outline-none focus:border-[var(--color-primary)]"
                >
                  {["USD", "GBP", "INR", "EUR", "JPY", "BRL", "CAD", "AUD"].map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-[var(--color-text-muted)] mb-1">Effective Date</label>
                <input
                  type="date"
                  required
                  value={salaryForm.effective_date}
                  onChange={(e) => setSalaryForm({ ...salaryForm, effective_date: e.target.value })}
                  className="w-full px-3 py-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg text-sm focus:outline-none focus:border-[var(--color-primary)]"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="mt-3 px-4 py-2 bg-[var(--color-success)] hover:bg-[var(--color-success)]/80 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {submitting ? "Saving..." : "Save Salary Update"}
            </button>
          </form>
        )}

        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--color-border)]">
              <th className="text-left px-4 py-2 text-[var(--color-text-muted)] font-medium">Effective Date</th>
              <th className="text-right px-4 py-2 text-[var(--color-text-muted)] font-medium">Base Salary</th>
              <th className="text-center px-4 py-2 text-[var(--color-text-muted)] font-medium">Currency</th>
              <th className="text-right px-4 py-2 text-[var(--color-text-muted)] font-medium">USD Equivalent</th>
            </tr>
          </thead>
          <tbody>
            {history.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-[var(--color-text-muted)]">No salary records.</td>
              </tr>
            ) : (
              [...history].reverse().map((record, i) => (
                <tr key={record.id} className={`border-b border-[var(--color-border)] ${i === 0 ? "bg-[var(--color-primary)]/5" : ""}`}>
                  <td className="px-4 py-2.5">{record.effective_date}</td>
                  <td className="px-4 py-2.5 text-right font-mono">{formatCurrency(record.base_salary, record.currency)}</td>
                  <td className="px-4 py-2.5 text-center">{record.currency}</td>
                  <td className="px-4 py-2.5 text-right font-mono text-[var(--color-text-muted)]">
                    {record.salary_usd ? formatCurrency(record.salary_usd, "USD") : "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
