# Brightloop Subscription Management System: Architecture

## 1. System Overview
Brightloop is a high-throughput, enterprise-ready subscription lifecycle management platform covering:
- Product and variant catalog with dynamic pricing
- Flexible subscription plans with auto-close, closable, pausable, and renewable controls
- State-machine-driven subscriptions (`draft → quotation → confirmed → active → closed` with `paused`)
- Idempotent recurring billing engine guaranteeing zero duplicate and zero skipped invoices
- Admin-defined percentage and fixed taxes and automated discounts
- Invoice lifecycle with derived overdue calculation and atomic payment recording
- Role-based authorization (`admin`, `staff`, `customer`) with strict row-level customer isolation
- Self-service Customer Portal and Executive Finance Dashboard with KPI aggregation pipelines
- High-performance Mongo indexes ensuring `< 2s` response times on datasets of 10,000+ subscriptions

## 2. Monolithic Layered Architecture
```
React 19 + TypeScript + Tailwind (Light Corporate UI)
                     │ REST/JSON + JWT
                     ▼
FastAPI Application (Modular Monolith)
  ├── Routers: API presentation & parameter parsing (No business logic)
  ├── Services: Business rules, state transitions, transactions, arithmetic
  ├── State: Finite State Machines (SUBSCRIPTION, INVOICE)
  ├── Repositories / Beanie ODM: Data queries and MongoDB persistence
  └── Core: Security, Money, Database connection, Error handlers
                     │
                     ▼
MongoDB Replica Set (Multi-document ACID transactions & atomic claims)
                     ▲
                     │
APScheduler Worker (Periodic billing run, auto-close, and reminder triggers)
```

## 3. Data Integrity & Financial Precision
- All monetary fields (`sales_price`, `cost_price`, `extra_price`, `unit_price`, `subtotal`, `tax_total`, `discount_total`, `total`, `amount_paid`) are stored and manipulated using Python's `Decimal` type with `ROUND_HALF_UP` to 2 decimal places.
- Floating-point representations for money are strictly avoided.
- Compound unique index `{subscription_id: 1, period_start: 1, period_end: 1}` on `invoices` acts as an uncompromisable database-level idempotency lock.
