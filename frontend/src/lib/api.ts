/**
 * API client for the Employee Salary Management backend.
 *
 * Centralizes all fetch calls to the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Employee {
  id: string;
  employee_id: string;
  full_name: string;
  email: string;
  department: string;
  job_title: string;
  country: string;
  status: string;
  joining_date: string;
  created_at: string;
  updated_at: string;
  current_salary: SalaryInfo | null;
}

export interface SalaryInfo {
  base_salary: string;
  currency: string;
  effective_date: string;
  salary_usd: string | null;
}

export interface EmployeeListResponse {
  items: Employee[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SalaryRecord {
  id: string;
  base_salary: string;
  currency: string;
  effective_date: string;
  salary_usd: string | null;
  created_at: string;
}

export interface SalaryHistoryResponse {
  employee_id: string;
  records: SalaryRecord[];
}

export interface DepartmentStat {
  department: string;
  employee_count: number;
  avg_salary_usd: string;
  min_salary_usd: string;
  max_salary_usd: string;
  total_payroll_usd: string;
}

export interface CountryStat {
  country: string;
  currency: string;
  employee_count: number;
  avg_salary_local: string;
  avg_salary_usd: string;
  total_payroll_usd: string;
}

export interface SalarySummary {
  total_employees: number;
  avg_salary_usd: string;
  median_salary_usd: string;
  min_salary_usd: string;
  max_salary_usd: string;
  total_payroll_usd: string;
}

export interface AnalyticsResponse {
  summary: SalarySummary;
  by_department: DepartmentStat[];
  by_country: CountryStat[];
}

export interface EmployeeCreateData {
  full_name: string;
  email: string;
  department: string;
  job_title: string;
  country: string;
  joining_date: string;
  base_salary: string;
  currency: string;
}

export interface EmployeeUpdateData {
  full_name?: string;
  email?: string;
  department?: string;
  job_title?: string;
  country?: string;
  joining_date?: string;
}

export interface SalaryUpdateData {
  base_salary: string;
  currency: string;
  effective_date: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error: ${res.status}`);
  }
  return res.json();
}

// Employees
export const api = {
  // Employee CRUD
  listEmployees(params: Record<string, string | number> = {}): Promise<EmployeeListResponse> {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") query.set(k, String(v));
    });
    return apiFetch(`/api/employees?${query}`);
  },

  getEmployee(id: string): Promise<Employee> {
    return apiFetch(`/api/employees/${id}`);
  },

  createEmployee(data: EmployeeCreateData): Promise<Employee> {
    return apiFetch("/api/employees", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  updateEmployee(id: string, data: EmployeeUpdateData): Promise<Employee> {
    return apiFetch(`/api/employees/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  deleteEmployee(id: string): Promise<Employee> {
    return apiFetch(`/api/employees/${id}`, { method: "DELETE" });
  },

  reactivateEmployee(id: string): Promise<Employee> {
    return apiFetch(`/api/employees/${id}/reactivate`, { method: "POST" });
  },

  exportEmployeesCSV(params: Record<string, string> = {}): string {
    const query = new URLSearchParams(params);
    return `${API_BASE}/api/employees/export?${query}`;
  },

  // Salary
  getCurrentSalary(employeeId: string): Promise<SalaryInfo> {
    return apiFetch(`/api/employees/${employeeId}/salary`);
  },

  updateSalary(employeeId: string, data: SalaryUpdateData): Promise<SalaryRecord> {
    return apiFetch(`/api/employees/${employeeId}/salary`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  getSalaryHistory(employeeId: string): Promise<SalaryHistoryResponse> {
    return apiFetch(`/api/employees/${employeeId}/salary/history`);
  },

  // Analytics
  getAnalytics(): Promise<AnalyticsResponse> {
    return apiFetch("/api/analytics");
  },
};
