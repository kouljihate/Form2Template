"""PDF generators for the business plan (plan d'affaires) and bank application (dossier banque).

Every generator exposes ``generate_pdf_fr(data, pdf_path=None)`` or
``generate_pdf_ar(data, pdf_path=None)`` and returns an in-memory ``BytesIO``
buffer positioned at 0, so callers can store/download the PDF without touching
the filesystem.
"""
