"""PDF text extraction and chunking, with OCR fallback for scanned PDFs."""
from pypdf import PdfReader


def _text_layer_pages(file):
    """Extract per-page text from the PDF's embedded text layer (fast path)."""
    try:
        file.seek(0)  # make sure we read from the start of the stream
    except (AttributeError, OSError):
        pass
    reader = PdfReader(file)
    return [(page.extract_text() or "") for page in reader.pages]


def _ocr_pages(file, dpi=400):
    """Render each page to a high-resolution image and read it with RapidOCR.

    Used only when the text layer is empty/missing (scanned or image-based PDFs).
    dpi=400 is important: small embedded images (e.g. ticket screenshots) only
    become machine-readable when the page is rasterized at high resolution.
    Returns per-page OCR text.
    """
    try:
        import pymupdf as mupdf
    except ImportError:
        import fitz as mupdf
    from rapidocr_onnxruntime import RapidOCR
    import numpy as np

    ocr = RapidOCR()
    try:
        file.seek(0)  # the text-layer pass already consumed the stream
    except (AttributeError, OSError):
        pass
    data = file.read()
    doc = mupdf.open(stream=data, filetype="pdf")
    pages = []
    for page in doc:
        pix = page.get_pixmap(dpi=dpi)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img = img[:, :, :3]
        result, _ = ocr(img)
        pages.append("\n".join(line[1] for line in result) if result else "")
    doc.close()
    return pages


def chunk_pdf(file, chunk_size=400, overlap=50):
    """Extract text from a PDF file object and split into overlapping word chunks.

    Tries the PDF's text layer first; if it yields (almost) no text, falls back
    to OCR so scanned/image-based PDFs still work.

    Args:
        file: file-like object with .read() (e.g. Streamlit UploadedFile).
        chunk_size: target number of words per chunk.
        overlap: number of overlapping words between consecutive chunks.

    Returns:
        (chunks, ocr_used): list of non-empty text chunks, and whether OCR was needed.
    """
    pages = _text_layer_pages(file)
    ocr_used = False
    if sum(len(p.strip()) for p in pages) < 20:  # effectively no text layer
        try:
            pages = _ocr_pages(file)
            ocr_used = True
        except Exception:
            # OCR unavailable/failed — behave as before (zero chunks -> app shows guidance)
            pages = []

    text = "\n".join(pages)
    words = text.split()
    chunks = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
    return chunks, ocr_used
