# Architecture & Design Decisions Record

This document records architectural decisions, tech stack choices, and conventions satisfying all business rules in the Brightloop Architecture Spec.

## ADR-001: Technology Stack and Execution Environment
- **Backend**: FastAPI with Python 3.12+ (Python 3.14 on host), Pydantic v2, Uvicorn.
- **Database**: MongoDB 8.3 with Beanie ODM over Motor/PyMongo async driver. Configured as a single-node replica set (`rs0`) to enable ACID multi-document transactions required for idempotent billing runs and atomic payment processing.
- **Money Handling**: Decimal128 / Python `Decimal` rounded with `ROUND_HALF_UP` to 2 decimal places. All monetary math centralized in `app/core/money.py`. Floats are strictly prohibited for currency.
- **PDF Generation**: ReportLab engine generating crisp, professional, vector invoice PDFs with complete billing breakdown, payment history, and company header.
- **Frontend**: React + Vite + TypeScript with Tailwind CSS. Follows a clean, modern, accessible light corporate palette (slate-50 background, crisp white cards, blue-600 accents, high contrast, clean human-crafted aesthetic without dark theme or AI badges).

## ADR-002: Authentication & Token Management
- Passwords hashed using native `bcrypt` (`hashpw`/`checkpw`).
- Access tokens expire in 15 minutes; refresh tokens stored in secure HTTP-only cookies.
- Forgot password generates secure random token, stores SHA-256 hash in database with 30-minute expiry; reset link dispatched via email / development logger.
- Password policy strictly enforced on both client and server: more than 8 characters (min 9), at least 1 uppercase, 1 lowercase, 1 special character.
- Public signup always assigns `customer` role. Only admins can create `staff` users.

## ADR-003: Idempotent Billing Engine
- **Atomic Claim**: Mongo `find_one_and_update` on active subscriptions with `next_invoice_date <= today` and leased `lock_until`.
- **Idempotency Guard**: Unique compound index on `invoices`: `(subscription_id, period_start, period_end)` prevents duplicate invoicing even under parallel workers or process crashes.
- **Atomic Transaction**: Billing execution runs within an ACID MongoDB session transaction. If duplicate is detected, `DuplicateKeyError` is handled gracefully without re-billing.
- **Catch-up Loop**: Re-claims and bills sequentially period by period if `next_invoice_date` is several periods behind until `next_invoice_date > today`.
- **Auto-Close & Quote Expiry**: Automated jobs close expired auto-close subscriptions and expire quotations past `quotation_valid_until`.

## ADR-004: Row-Level Customer Isolation
- Customer queries strictly enforce `customer_id == current_user.customer_id` inside the repository/service layer. Cross-tenant access returns HTTP 404 (Not Found) rather than 403 (Forbidden) to prevent account or resource enumeration.

## ADR-005: Pydantic v2 BSON Decimal128 Serialization
- Beanie models reading BSON `Decimal128` from MongoDB failed with Pydantic v2 strict Decimal validation.
- Solution: Defined `Money` and `OptionalMoney` using `Annotated[Decimal, BeforeValidator(validate_money), PlainSerializer(...)]` in `app/core/money.py` ensuring bi-directional BSON `Decimal128` <-> Python `Decimal` serialization without loss of precision.

## ADR-006: Proportional Subscription Discount Allocation on Tax Bases
- Taxes MUST be computed on the post-discount base. When a subscription-level discount applies to the subtotal, it is allocated proportionally across line subtotals before tax calculations, ensuring line-level tax amounts accurately reflect effective taxable values.

## ADR-007: Frontend Light Business Theme
- Applied a tailored light corporate design: white surface cards, slate-50/100 backgrounds, high-contrast slate-900 typography, subtle blue-600 focus states, and standard semantic status badges. Avoids dark/black schemes and avoids any AI-generated style tags/watermarks.
