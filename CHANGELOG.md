# Changelog

All notable changes to this project are documented in this file.
This project follows [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-17

First versioned release: the application now starts and completes both document flows.

### Added
- `modules/admin.py` - admin company management (create, edit, activate/deactivate, password reset,
  WhatsApp invite, delete) with an activity log. The module was previously empty, which aborted startup.
- `templates/` package - French and Arabic PDF generators for the business plan and the bank
  application, sharing ReportLab helpers (Unicode fonts, Arabic shaping, styles, tables, footer,
  page numbers).
- `i18n/shell.py` - bilingual labels for navigation, company card, bank form and administration.
- Sidebar language selector (`AR/FR`, `AR/EN`); `tr` now comes from `i18n.get_translations`
  instead of an inline dictionary.
- `VERSION` file and this changelog.

### Changed
- PDFs are generated in memory (`BytesIO`) and stored once as base64 in MongoDB. The
  `generated_pdfs/` directory and the duplicate copy on disk are gone.
- `render_plan_affaires` / `render_dossier_banque` take `(tr, current_company)` and record
  `company_id` / `company_name` with every submission.
- `_pdf_to_base64` accepts raw bytes, a buffer or a legacy file path.
- `requirements.txt`: bounded ranges, `pymongo[srv]`, `arabic-reshaper`, `python-bidi`;
  removed the unused `Pillow`.
- Unreachable duplicate branches removed from `app.py`.

### Fixed
- `ImportError` on startup (`render_admin_companies` did not exist).
- `TypeError` from passing four arguments to three-parameter render functions.
- `KeyError` for translation keys missing from the inline dictionary.
- `save_plan` / `save_banque` crashed without `company_id` / `company_name`.
- Submission failed when the `generated_pdfs/` directory was absent.
