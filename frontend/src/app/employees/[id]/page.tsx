"use client";

import { useEffect, useState, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, Employee, SalaryRecord } from "@/lib/api";
import { useToast } from "@/components/Toast";
import ConfirmDialog from "@/components/ConfirmDialog";
import Spinner from "@/components/Spinner";

function formatCurrency(amount: string | null, currency: string): string {
  if (!amount) return "\u2014";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency || "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(parseFloat(amount));
}

export default function EmployeeDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const { toast } = useToast();

  const [employee, setEmployee] = useState<Employee | null>(null);
  const [history, setHistory] = useState<SalaryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Confirm dialog
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState<"deactivate" | "reactivate">("deactivate");

  // Salary update form
  const [showSalaryForm, setShowSalaryForm] = useState(false);
  const [salaryForm, setSalaryForm] = useState({
    base_salary: "",
    currency: "USD",
    effective_date: new Date().toISOString().split("T")[0],
  });
  const [salaryErrors, setSalaryErrors] = useState<Record<string, string>>({});
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
  const [editErrors, setEditErrors] = useState<Record<string, string>>({});

  // Original values for dirty checking
  const [originalEditForm, setOriginalEditForm] = useState({
    full_name: "",
    email: "",
    department: "",
    job_title: "",
    country: "",
  });

  const hasEditChanges = useMemo(() => {
    return Object.keys(editForm).some(
      (key) => editForm[key as keyof typeof editForm] !== originalEditForm[key as keyof typeof originalEditForm]
    );
  }, [editForm, originalEditForm]);

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

      const formValues = {
        full_name: emp.full_name,
        email: emp.email,
        department: emp.department,
        job_title: emp.job_title,
        country: emp.country,
      };
      setEditForm(formValues);
      setOriginalEditForm(formValues);

      if (emp.current_salary) {
        setSalaryForm({
          base_salary: emp.current_salary.base_salary,
          currency: emp.current_salary.currency,
          effective_date: new Date().toISOString().split("T")[0],
        });
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function validateSalaryForm(): boolean {
    const errors: Record<string, string> = {};
    if (!salaryForm.base_salary || parseFloat(salaryForm.base_salary) <= 0) {
      errors.base_salary = "Salary must be a positive number";
    }
    if (!salaryForm.effective_date) {
      errors.effective_date = "Effective date is required";
    }
    setSalaryErrors(errors);
    return Object.keys(errors).length === 0;
  }

  function validateEditForm(): boolean {
    const errors: Record<string, string> = {};
    if (!editForm.full_name.trim()) errors.full_name = "Name is required";
    if (!editForm.email.trim()) errors.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(editForm.email)) errors.email = "Invalid email format";
    if (!editForm.department.trim()) errors.department = "Department is required";
    if (!editForm.job_title.trim()) errors.job_title = "Job title is required";
    if (!editForm.country.trim()) errors.country = "Country is required";
    setEditErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSalaryUpdate(e: React.FormEvent) {
    e.preventDefault();
    if (!validateSalaryForm()) return;
    setSubmitting(true);
    try {
      await api.updateSalary(id, salaryForm);
      setShowSalaryForm(false);
      setSalaryErrors({});
      toast("Salary updated successfully", "success");
      await loadEmployee();
    } catch (err: any) {
      toast(err.message || "Failed to update salary", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUpdate(e: React.FormEvent) {
    e.preventDefault();
    if (!hasEditChanges) {
      setEditing(false);
      return;
    }
    if (!validateEditForm()) return;
    setSubmitting(true);
    try {
      await api.updateEmployee(id, editForm);
      setEditing(false);
      setEditErrors({});
      toast("Employee updated successfully", "success");
      await loadEmployee();
    } catch (err: any) {
      toast(err.message || "Failed to update employee", "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleStatusChange() {
    setConfirmOpen(false);
    setSubmitting(true);
    try {
      if (confirmAction === "deactivate") {
        await api.deleteEmployee(id);
        toast("Employee deactivated", "success");
      } else {
        await api.reactivateEmployee(id);
        toast("Employee reactivated", "success");
      }
      await loadEmployee();
    } catch (err: any) {
      toast(err.message || "Failed to update status", "error");
    } finally {
      setSubmitting(false);
    }
  }

  function handleCancelEdit() {
    setEditing(false);
    setEditForm({ ...originalEditForm });
    setEditErrors({});
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
      <ConfirmDialog
        open={confirmOpen}
        title={confirmAction === "deactivate" ? "Deactivate Employee" : "Reactivate Employee"}
        message={
          confirmAction === "deactivate"
            ? `Are you sure you want to deactivate ${employee.full_name}? They will be excluded from analytics.`
            : `Are you sure you want to reactivate ${employee.full_name}? They will be included in analytics again.`
        }
        confirmLabel={confirmAction === "deactivate" ? "Deactivate" : "Reactivate"}
        variant={confirmAction === "deactivate" ? "danger" : "primary"}
        onConfirm={handleStatusChange}
        onCancel={() => setConfirmOpen(false)}
      />

      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-[var(--color-text-muted)] mb-6">
        <Link href="/employees" className="hover:text-[var(--color-text)] transition-colors">Employees</Link>
        <span>/</span>
        <span className="text-[var(--color-text)]">{employee.full_name}</span>
      </div>

      {/* Employee Info */}
      <div className="glass rounded-xl p-6 mb-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">{employee.full_name}</h1>
            <p className="text-[var(--color-text-muted)] text-sm mt-1">{employee.employee_id} &middot; {employee.email}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => editing ? handleCancelEdit() : setEditing(true)}
              className="px-3 py-1.5 text-xs border border-[var(--color-border)] rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors"
            >
              {editing ? "Cancel" : "Edit"}
            </button>
            {employee.status === "active" ? (
              <button
                onClick={() => { setConfirmAction("deactivate"); setConfirmOpen(true); }}
                className="px-3 py-1.5 text-xs border border-[var(--color-danger)]/30 text-[var(--color-danger)] rounded-lg hover:bg-[var(--color-danger)]/10 transition-colors"
              >
                Deactivate
              </button>
            ) : (
              <button
                onClick={() => { setConfirmAction("reactivate"); setConfirmOpen(true); }}
                className="px-3 py-1.5 text-xs border border-[var(--color-success)]/30 text-[var(--color-success)] rounded-lg hover:bg-[var(--color-success)]/10 transition-colors"
              >
                Reactivate
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
                  type={field === "email" ? "email" : "text"}
                  value={editForm[field]}
                  onChange={(e) => {
                    setEditForm({ ...editForm, [field]: e.target.value });
                    if (editErrors[field]) setEditErrors({ ...editErrors, [field]: "" });
                  }}
                  className={`w-full px-3 py-2 bg-[var(--color-bg)] border rounded-lg text-sm focus:outline-none focus:border-[var(--color-primary)] ${editErrors[field] ? "border-[var(--color-danger)]" : "border-[var(--color-border)]"}`}
                />
                {editErrors[field] && <p className="text-xs text-[var(--color-danger)] mt-1">{editErrors[field]}</p>}
              </div>
            ))}
            <div className="col-span-2 flex gap-2">
              <button
                type="submit"
                disabled={submitting || !hasEditChanges}
                className="px-4 py-2 bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2"
              >
                {submitting && <Spinner size={14} />}
                {submitting ? "Saving..." : hasEditChanges ? "Save Changes" : "No Changes"}
              </button>
              <button
                type="button"
                onClick={handleCancelEdit}
                className="px-4 py-2 border border-[var(--color-border)] rounded-lg text-sm hover:bg-[var(--color-surface-hover)] transition-colors"
              >
                Cancel
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
              ["Current Salary", employee.current_salary ? `${formatCurrency(employee.current_salary.base_salary, employee.current_salary.currency)} (${formatCurrency(employee.current_salary.salary_usd, "USD")} USD)` : "\u2014"],
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
                  onChange={(e) => {
                    setSalaryForm({ ...salaryForm, base_salary: e.target.value });
                    if (salaryErrors.base_salary) setSalaryErrors({ ...salaryErrors, base_salary: "" });
                  }}
                  className={`w-full px-3 py-2 bg-[var(--color-surface)] border rounded-lg text-sm focus:outline-none focus:border-[var(--color-primary)] ${salaryErrors.base_salary ? "border-[var(--color-danger)]" : "border-[var(--color-border)]"}`}
                  placeholder="85000"
                />
                {salaryErrors.base_salary && <p className="text-xs text-[var(--color-danger)] mt-1">{salaryErrors.base_salary}</p>}
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
                  onClick={(e) => (e.target as HTMLInputElement).showPicker?.()}
                  onChange={(e) => {
                    setSalaryForm({ ...salaryForm, effective_date: e.target.value });
                    if (salaryErrors.effective_date) setSalaryErrors({ ...salaryErrors, effective_date: "" });
                  }}
                  className={`w-full px-3 py-2 bg-[var(--color-surface)] border rounded-lg text-sm focus:outline-none focus:border-[var(--color-primary)] cursor-pointer ${salaryErrors.effective_date ? "border-[var(--color-danger)]" : "border-[var(--color-border)]"}`}
                />
                {salaryErrors.effective_date && <p className="text-xs text-[var(--color-danger)] mt-1">{salaryErrors.effective_date}</p>}
              </div>
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="mt-3 px-4 py-2 bg-[var(--color-success)] hover:bg-[var(--color-success)]/80 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 inline-flex items-center gap-2"
            >
              {submitting && <Spinner size={14} />}
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
                    {record.salary_usd ? formatCurrency(record.salary_usd, "USD") : "\u2014"}
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
