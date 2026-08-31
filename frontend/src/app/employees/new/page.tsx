"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useToast } from "@/components/Toast";
import Spinner from "@/components/Spinner";

const COUNTRIES_WITH_CURRENCY: Record<string, string> = {
  US: "USD",
  UK: "GBP",
  India: "INR",
  Germany: "EUR",
  Japan: "JPY",
  Brazil: "BRL",
  Canada: "CAD",
  Australia: "AUD",
};

const DEPARTMENTS = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations", "Support", "Product"];

export default function NewEmployeePage() {
  const router = useRouter();
  const { toast } = useToast();
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [form, setForm] = useState({
    full_name: "",
    email: "",
    department: "Engineering",
    job_title: "",
    country: "US",
    joining_date: new Date().toISOString().split("T")[0],
    base_salary: "",
    currency: "USD",
  });

  function handleCountryChange(country: string) {
    setForm({
      ...form,
      country,
      currency: COUNTRIES_WITH_CURRENCY[country] || "USD",
    });
  }

  function updateField(field: string, value: string) {
    setForm({ ...form, [field]: value });
    if (errors[field]) setErrors({ ...errors, [field]: "" });
  }

  function validate(): boolean {
    const errs: Record<string, string> = {};
    if (!form.full_name.trim()) errs.full_name = "Full name is required";
    if (!form.email.trim()) errs.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errs.email = "Invalid email format";
    if (!form.job_title.trim()) errs.job_title = "Job title is required";
    if (!form.joining_date) errs.joining_date = "Joining date is required";
    if (!form.base_salary || parseFloat(form.base_salary) <= 0) errs.base_salary = "Salary must be a positive number";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    try {
      const employee = await api.createEmployee(form);
      toast("Employee created successfully", "success");
      router.push(`/employees/${employee.id}`);
    } catch (err: any) {
      toast(err.message || "Failed to create employee", "error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="animate-fade-in max-w-2xl">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-[var(--color-text-muted)] mb-6">
        <Link href="/employees" className="hover:text-[var(--color-text)] transition-colors">Employees</Link>
        <span>/</span>
        <span className="text-[var(--color-text)]">New Employee</span>
      </div>

      <h1 className="text-2xl font-bold mb-6">Add New Employee</h1>

      <form onSubmit={handleSubmit} className="glass rounded-xl p-6 space-y-6">
        {/* Personal Info */}
        <div>
          <h2 className="text-sm font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Personal Information</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-[var(--color-text-muted)] mb-1">Full Name *</label>
              <input
                type="text"
                required
                value={form.full_name}
                onChange={(e) => updateField("full_name", e.target.value)}
                className={`w-full px-3 py-2 bg-[var(--color-bg)] border rounded-lg text-sm focus:outline-none focus:border-[var(--color-primary)] transition-colors ${errors.full_name ? "border-[var(--color-danger)]" : "border-[var(--color-border)]"}`}
                placeholder="Alice Johnson"
              />
              {errors.full_name && <p className="text-xs text-[var(--color-danger)] mt-1">{errors.full_name}</p>}
            </div>
            <div>
              <label className="block text-xs text-[var(--color-text-muted)] mb-1">Email *</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => updateField("email", e.target.value)}
                className={`w-full px-3 py-2 bg-[var(--color-bg)] border rounded-lg text-sm focus:outline-none focus:border-[var(--color-primary)] transition-colors ${errors.email ? "border-[var(--color-danger)]" : "border-[var(--color-border)]"}`}
                placeholder="alice@acme.com"
              />
              {errors.email && <p className="text-xs text-[var(--color-danger)] mt-1">{errors.email}</p>}
            </div>
          </div>
        </div>

        {/* Work Info */}
        <div>
          <h2 className="text-sm font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Work Information</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-[var(--color-text-muted)] mb-1">Department *</label>
              <select
                value={form.department}
                onChange={(e) => updateField("department", e.target.value)}
                className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm focus:outline-none focus:border-[var(--color-primary)]"
              >
                {DEPARTMENTS.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-[var(--color-text-muted)] mb-1">Job Title *</label>
              <input
                type="text"
                required
                value={form.job_title}
                onChange={(e) => updateField("job_title", e.target.value)}
                className={`w-full px-3 py-2 bg-[var(--color-bg)] border rounded-lg text-sm focus:outline-none focus:border-[var(--color-primary)] transition-colors ${errors.job_title ? "border-[var(--color-danger)]" : "border-[var(--color-border)]"}`}
                placeholder="Software Engineer"
              />
              {errors.job_title && <p className="text-xs text-[var(--color-danger)] mt-1">{errors.job_title}</p>}
            </div>
            <div>
              <label className="block text-xs text-[var(--color-text-muted)] mb-1">Country *</label>
              <select
                value={form.country}
                onChange={(e) => handleCountryChange(e.target.value)}
                className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm focus:outline-none focus:border-[var(--color-primary)]"
              >
                {Object.keys(COUNTRIES_WITH_CURRENCY).map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-[var(--color-text-muted)] mb-1">Joining Date *</label>
              <input
                type="date"
                required
                value={form.joining_date}
                onClick={(e) => (e.target as HTMLInputElement).showPicker?.()}
                onChange={(e) => updateField("joining_date", e.target.value)}
                className={`w-full px-3 py-2 bg-[var(--color-bg)] border rounded-lg text-sm focus:outline-none focus:border-[var(--color-primary)] transition-colors cursor-pointer ${errors.joining_date ? "border-[var(--color-danger)]" : "border-[var(--color-border)]"}`}
              />
              {errors.joining_date && <p className="text-xs text-[var(--color-danger)] mt-1">{errors.joining_date}</p>}
            </div>
          </div>
        </div>

        {/* Salary */}
        <div>
          <h2 className="text-sm font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Initial Salary</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-[var(--color-text-muted)] mb-1">Base Salary *</label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={form.base_salary}
                onChange={(e) => updateField("base_salary", e.target.value)}
                className={`w-full px-3 py-2 bg-[var(--color-bg)] border rounded-lg text-sm focus:outline-none focus:border-[var(--color-primary)] transition-colors ${errors.base_salary ? "border-[var(--color-danger)]" : "border-[var(--color-border)]"}`}
                placeholder="85000"
              />
              {errors.base_salary && <p className="text-xs text-[var(--color-danger)] mt-1">{errors.base_salary}</p>}
            </div>
            <div>
              <label className="block text-xs text-[var(--color-text-muted)] mb-1">Currency</label>
              <input
                type="text"
                value={form.currency}
                readOnly
                className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text-muted)] cursor-not-allowed"
              />
              <p className="text-xs text-[var(--color-text-muted)] mt-1">Auto-set based on country</p>
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="px-6 py-2.5 bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 inline-flex items-center gap-2"
          >
            {submitting && <Spinner size={14} />}
            {submitting ? "Creating..." : "Create Employee"}
          </button>
          <Link
            href="/employees"
            className="px-6 py-2.5 border border-[var(--color-border)] rounded-lg text-sm font-medium hover:bg-[var(--color-surface-hover)] transition-colors"
          >
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
