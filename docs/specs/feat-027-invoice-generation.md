# FEAT-027: Invoice Generation

## Status: Done

## Summary
Each payment automatically gets a unique invoice number (INV-XXXXXXXX). Students can view payment history and printable invoice detail pages.

## Models
- Payment (`apps/payments/models.py`): `invoice_number` (CharField, unique, auto-generated in save() as `INV-{uuid_hex[:8]}`), `paid_at` (DateTimeField). Also has amount_display property.

## Views
- PaymentHistoryView (`apps/payments/views.py`) -- paginated list (20/page) of student's payments filtered by academy
- InvoiceDetailView (`apps/payments/views.py`) -- renders a printable invoice page for a single payment, restricted to the payment's student

## Celery Tasks
- send_payment_confirmation_email (`apps/payments/tasks.py`) -- sends HTML email with invoice number and link to invoice detail page

## URLs
- `/payments/history/` -- `payment-history`
- `/payments/invoice/<int:pk>/` -- `invoice-detail`

## Templates
- `templates/payments/payment_history.html`
- `templates/payments/invoice.html`

## Tests
- TestInvoices in `tests/integration/test_release3_features.py` -- invoice detail view loads, invoice_number present in response content
