# PROD-007: PDF Generation (Invoices + Certificates)

## Status: TODO

## Summary
Add xhtml2pdf to generate downloadable PDF versions of invoices and course completion certificates.

## Implementation
- Add `xhtml2pdf` to requirements
- Create `InvoicePDFView` in payments app — renders invoice HTML template to PDF
- Create `CertificatePDFView` in enrollments app — renders certificate HTML template to PDF
- Add "Download PDF" buttons on the existing invoice detail and certificate pages
- PDF templates reuse existing HTML templates with print-friendly CSS
- Response uses `Content-Disposition: attachment` for browser download

## Files Modified/Created
- `requirements/base.txt` — add `xhtml2pdf`
- `apps/payments/views.py` — add `InvoicePDFView`
- `apps/payments/urls.py` — add `invoice-pdf` URL pattern
- `apps/enrollments/views.py` — add `CertificatePDFView`
- `apps/enrollments/urls.py` — add `certificate-pdf` URL pattern
- `templates/payments/invoice.html` — add PDF download button
- `templates/enrollments/certificate.html` — add PDF download button

## Configuration
- No additional env vars needed
- xhtml2pdf uses ReportLab internally, included as transitive dependency

## Verification
- Navigate to an invoice detail page, click "Download PDF" — should download a valid PDF
- Navigate to a certificate page, click "Download PDF" — should download a valid PDF
- Verify PDF contains all invoice/certificate data and is properly formatted
