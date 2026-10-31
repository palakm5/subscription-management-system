# Brightloop Subscription Management System

A high-performance subscription, billing, and invoicing management platform built for **Brightloop Software**, adhering strictly to the Architecture Specification.

---

## 1. Overview & Architecture

Brightloop is a single platform covering the complete subscription lifecycle:
- **Catalog Management**: Products with custom variants (attributes + extra prices), subscription plans, tax rules, threshold discounts, and quotation templates.
- **Subscriptions & Quotations**: Finite State Machine (`draft → quotation → confirmed → active → closed` with side-state `paused`), sequential numbering (`SUB-000001`), line item pricing, and renewals.
- **Billing Engine**: Multi-worker safe atomic claims, ACID multi-document MongoDB transactions, post-discount tax bases, unique compound index idempotency guards, period catch-up, and automated lifecycle closures.
- **Invoices & Payments**: Snapshot-based line items, derived overdue status, atomic payment recording with automatic flip to `paid`, overpayment prevention, and vector PDF invoice generation.
- **Customer Self-Service Portal**: Strict row-level tenant isolation (cross-tenant access yields 404).
- **Finance Dashboard & Reports**: High-speed MongoDB aggregation pipelines returning sub-100ms analytics over **10,000+ subscriptions and 30,000+ invoices**.

### Tech Stack
| Layer | Technology |
|---|---|
| **Backend** | Python 3.12+, FastAPI, Pydantic v2, Uvicorn |
| **Database & ODM** | MongoDB 8 (single-node replica set `rs0` for multi-document ACID transactions) + Beanie ODM (Motor/PyMongo) |
| **Monetary Arithmetic** | `app/core/money.py` using Python `Decimal` rounded `ROUND_HALF_UP` to 2 decimal places with BSON `Decimal128` serialization |
| **Auth & Security** | JWT access tokens (15m), HTTP-only cookies, native `bcrypt`, SHA-256 token hashing for password reset |
| **Background Worker** | APScheduler worker process (`app/worker/scheduler.py`, `jobs.py`) |
| **PDF Engine** | ReportLab generating professional vector invoices with financial breakdown |
| **Frontend** | React 19 + TypeScript + Vite + Tailwind CSS with a clean, light corporate theme (slate-50, crisp white cards, blue-600 accents, no dark mode, no AI tags) |

---

## 2. Quickstart & Running Locally

### Prerequisites
- Python 3.12+ (or 3.14)
- Node.js 18+ and npm
- MongoDB 7+ with replica set enabled (`rs0`)

### Step 1: Start MongoDB Replica Set
Multi-document ACID transactions require MongoDB to run with a replica set:
```powershell
mongod --dbpath ".\.mongo_rs" --port 27018 --replSet rs0 --bind_ip 127.0.0.1
```
*(If first time initializing the replica set):*
```powershell
mongosh --port 27018 --eval "rs.initiate({_id: 'rs0', members: [{_id: 0, host: '127.0.0.1:27018'}]})"
```

### Step 2: Set Up & Run Backend API
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .

# Run development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI Swagger documentation is available at `http://127.0.0.1:8000/docs`.

### Step 3: Run Database Seeder (10k+ Subscriptions)
To seed initial administrative accounts, products, and 10,000+ subscriptions + 30,000 invoices:
```powershell
cd backend
python -m app.seed.seed
```

### Step 4: Run Frontend Development Server
```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```
Open your browser at `http://127.0.0.1:5173`.

---

## 3. Automated Test Suite

All 13 test suites execute and pass across the full business rules, lifecycle FSMs, billing idempotency, customer isolation, and performance thresholds:

```powershell
cd backend
.\.venv\Scripts\pytest -v
```

### Test Coverage Highlights:
- `test_money_calculations`: Verifies zero floating-point drift, half-up rounding, and line pricing.
- `test_password_policy`: Enforces password rules (> 8 chars, uppercase, lowercase, special character).
- `test_fsm_transitions`: Validates transition tables and ensures illegal transitions raise HTTP 409.
- `test_auth_signup_and_rbac`: Tests public signup (`customer`), admin-only staff provisioning, and role protection.
- `test_forgot_and_reset_password`: Token hashing, 30m expiry, single-use, email enumeration resistance.
- `test_catalog_crud`: Products, variants (`sales_price + extra_price`), plans, taxes, and discounts.
- `test_subscription_lifecycle_and_numbering`: Sequential numbering (`SUB-000001`), line calculations, template creation, and renewal.
- `test_billing_run_and_idempotency`: Validates that running billing twice against active subscriptions generates **only one invoice** via compound unique indexes.
- `test_catch_up_billing`: Verifies that a subscription 3 periods behind catches up with **3 distinct invoices**.
- `test_invoices_and_payments`: Partial payments, atomic payment recording, auto-flip to `paid`, and overpayment rejection.
- `test_portal_isolation_and_row_scope`: Verifies row-level customer scoping and **404 Not Found** returns on cross-tenant access.
- `test_reports_endpoints`: Validates KPI summary aggregation, monthly revenue group-by, and overdue calculations.
- `test_performance`: Asserts that `GET /reports/summary`, `GET /subscriptions`, and `GET /invoices` respond in **< 2.0 s** over 10,000+ seeded records.

---

## 4. Performance Benchmark Results (< 2s Requirement)

Benchmarked against a seeded dataset containing **10,000 subscriptions** and **29,999 invoices**:

| Endpoint | Target | Actual Response Time | Status |
|---|---|---|---|
| `GET /api/v1/reports/summary` | < 2.0 s | **0.095 s (95 ms)** | PASSED |
| `GET /api/v1/subscriptions?page=1` | < 2.0 s | **0.016 s (16 ms)** | PASSED |
| `GET /api/v1/invoices?page=1` | < 2.0 s | **0.027 s (27 ms)** | PASSED |
| `GET /api/v1/reports/revenue?group_by=month` | < 2.0 s | **0.023 s (23 ms)** | PASSED |
| `GET /api/v1/reports/overdue-invoices?page=1` | < 2.0 s | **0.028 s (28 ms)** | PASSED |

---

## 5. Walkthrough of the Demo Script (Section 15)

Follow these steps to demonstrate every core capability of Brightloop:

### 1. Customer Signup & Staff Creation
- Navigate to `http://127.0.0.1:5173/signup`.
- Test typing a password: live visual checklist validates `> 8 characters (min 9)`, uppercase, lowercase, and special character.
- Complete signup: automatically created with `role = customer`.
- Log out and log in as `admin@brightloop.com` / `AdminSecure1!`.
- Navigate to **Staff Team** (`/staff`) and click **New Staff Member** to provision internal staff accounts.

### 2. Catalog Setup (Product, Variant, Plan, Discount)
- Navigate to **Products & Variants** (`/products`).
- Click **New Product**: create a product (e.g. `Odoo ERP Hosting`, base sales price `$1,000.00`).
- Open **Variants**: add an attribute `brand`, value `Odoo Enterprise`, extra price `+$560.00`. Combined unit price automatically displays as `$1,560.00`.
- Navigate to **Subscription Plans** (`/plans`): create a `Monthly License` plan with `pausable`, `closable`, and `renewable` enabled.
- Navigate to **Discounts** (`/discounts`): create a `10% Promotional Discount` with scope `subscription`.

### 3. Build a Quotation from Template → Confirm → Activate
- Navigate to **Subscriptions** (`/subscriptions`) and click **New Subscription**.
- Select a Customer, choose **From Quotation Template** or custom plan with the variant lines.
- Subscription is created in `draft` status with number `SUB-000001`.
- Click **Manage** to view the detail modal:
  - Click **Generate Quotation** (`draft → quotation`).
  - Click **Confirm Quote** (`quotation → confirmed`).
  - Click **Activate Subscription** (`confirmed → active`). `next_invoice_date` is set to `start_date`.

### 4. Billing Run & Idempotency Verification
- In the top navigation bar or on the Invoices page, click **Run Billing Now**.
- An invoice is generated with:
  - Product line snapshot (`$1,560.00`).
  - 10% discount automatically applied (`-$156.00`).
  - Taxes computed strictly on the post-discount base (`$1,404.00`).
- Click **Run Billing Now** a second time:
  - Outcome: `skipped_duplicates: 1`. **Zero duplicate invoices generated.**

### 5. Record Payments & Auto-Paid Flip
- On the generated invoice, click **Record Payment**.
- Enter a partial payment (e.g., `$500.00`): status remains `confirmed` with balance due reduced.
- Overpayment test: attempt to pay more than the balance due: client and server reject the payment.
- Record the remaining balance: invoice atomically transitions to `paid`.
- Click **Download PDF**: ReportLab generates an official vector PDF invoice with payment receipt.

### 6. Fast KPI Dashboard & Overdue Tracking
- Navigate to **Dashboard** (`/`).
- KPI metric cards (Active Subscriptions, Monthly Revenue, Total Billed, Outstanding Amount, Overdue Invoices) and the revenue chart load immediately in **< 100ms** over all 10,000+ seeded records.
- Click the **Overdue** tab in **Invoices** (`/invoices`) to see derived overdue invoices (`confirmed AND due_date < today AND amount_paid < total`).

### 7. Customer Portal & Row-Level Isolation
- Log out and log in as customer (`customer@brightloop.com` / `CustomerSecure1!`).
- The customer lands directly in the **Customer Portal** (`/portal/subscriptions`).
- Only their own subscriptions and invoices are visible.
- If a customer attempts to query or manipulate another customer's subscription or invoice via the API, the backend returns **HTTP 404 (Not Found)**, completely preventing tenant enumeration.

---

## 6. Architecture & FSM Reference

### Pure State Machine Transition Tables
```python
SUBSCRIPTION_FSM = {
    "draft":     {"quotation", "closed"},
    "quotation": {"confirmed", "draft", "closed"},
    "confirmed": {"active", "closed"},
    "active":    {"paused", "closed"},
    "paused":    {"active", "closed"},
    "closed":    set(), # renewal creates a NEW subscription
}

INVOICE_FSM = {
    "draft":     {"confirmed", "cancelled"},
    "confirmed": {"paid", "cancelled"},
    "paid":      set(),
    "cancelled": set(),
}
```

### Pre-Seeded Demonstration Accounts
| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@brightloop.com` | `AdminSecure1!` |
| **Staff** | `staff@brightloop.com` | `StaffSecure1!` |
| **Customer** | `customer@brightloop.com` | `CustomerSecure1!` |
