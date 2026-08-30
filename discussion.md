I also wanted to share a few initial interpretations so I can make sure I’m aligned with your expectations.

1. Salary components
I’m planning to keep the MVP focused on base salary and avoid adding payroll-related components such as allowances, bonuses, or deductions unless they are specifically required. Please let me know if you expect these to be included.

2. Salary history
I’m planning to maintain salary changes as historical records with effective dates rather than simply overwriting the current salary. Please confirm if this matches the expected behavior.

3. Multiple currencies
Since the organization operates across multiple countries, I’m planning to store salaries in their respective currencies and provide country/role/department-level insights without introducing exchange-rate normalization in the MVP. Would that be acceptable, or do you expect cross-country compensation comparisons in a common currency?

4. Roles and permissions
Since the stated persona is an HR Manager, I’m planning to keep the MVP focused on a single HR Manager role rather than building a full RBAC system. Please confirm if any additional roles or permission levels are expected.

5. Compensation insights
I’m planning to include insights such as average/median salary, salary distribution, and comparisons across country, department, and role. Are there any specific compensation-related questions or reports you would particularly expect the application to answer?

6. Employee data
I did not see a predefined employee schema in the assessment. Should I define the relevant employee attributes based on the product requirements, or is there an expected set of fields that should be included?

7. Deployment
Is the deployment environment/platform completely open to the candidate, or is there a preferred hosting platform or database setup?





answers to above queries. 

Here is guidance across your points to help you finalize your architecture and scope:

1. Salary Components: Keeping the MVP strictly focused on base salary is the right call. Complex payroll components like allowances, bonuses, and tax deductions are out of scope.

2. Salary History: Maintaining a historical log with effective dates is a great architectural choice if you decide to implement it, but managing current salary per employee is completely sufficient for this MVP. You have full ownership here.

3. Multiple Currencies: Storing native local currencies for each employee is spot on. However, for org-wide analytics and cross-country comparisons, we strongly recommend providing a normalized view in a single base currency (e.g., USD) using a simple, seeded exchange-rate table. Comparing raw local numbers side-by-side without a common reference currency limits global reporting.

4. Roles & Permissions: Focusing on a single HR Manager persona is completely sufficient. You do not need to build multi-role permissions, manager views, or a full RBAC system.

5. Compensation Insights: Your proposed insights (average/median salary, salary distribution, and comparisons across country, department, and role) are spot on! Predefined visual dashboards, KPI cards, and interactive filters cover everything expected.

6. Employee Data Schema: You have full freedom to define the schema. Standard attributes like Employee ID, Full Name, Department, Job Title, Country, Base Salary, Currency, Status (Active/Inactive), and Joining Date work best.

7. Deployment: Any platform (Render, Railway, Fly.io, Vercel, AWS, etc.) is acceptable. If public hosting poses any friction, submitting a GitHub repository with a Docker Compose setup and a brief demo video is also fully sufficient.

Please capture your final scope decisions, data model assumptions, and intentional trade-offs in your one-page requirements document before diving into code.