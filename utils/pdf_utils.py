# utils/pdf_utils.py
import os
import time
import shutil
import requests
import certifi
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse, unquote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# PDF extraction libs
import pdfplumber
from PyPDF2 import PdfReader

# Configuration
DOWNLOAD_DIR = Path("downloaded_pdfs")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_PDF_BYTES = 50 * 1024 * 1024  # 50 MB max download
HEAD_TIMEOUT = 10
GET_TIMEOUT = 20

# Create a session with retries for transient network errors
def create_session(total_retries=3, backoff_factor=1):
    session = requests.Session()
    retry = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    # sensible headers to avoid some basic bot blocks
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return session

session = create_session()

def _sanitize_filename(name: str) -> str:
    # Remove problematic chars and limit length
    keep = "".join(c for c in name if c.isalnum() or c in (" ", ".", "_", "-"))
    keep = keep.strip().replace(" ", "_")
    return keep[:200] or "downloaded_pdf"

def _filename_from_url(url: str, headers) -> str:
    # Try content-disposition first
    cd = headers.get("content-disposition", "")
    if "filename=" in cd:
        # naive parse
        fname = cd.split("filename=")[-1].strip().strip('"')
        return _sanitize_filename(unquote(fname))
    # else fallback to path
    parsed = urlparse(url)
    path = Path(unquote(parsed.path)).name
    if path:
        return _sanitize_filename(path)
    # fallback
    domain = parsed.netloc.replace(":", "_")
    ts = int(time.time())
    return f"{_sanitize_filename(domain)}_{ts}.pdf"

def _is_pdf_content_type(headers) -> bool:
    ct = headers.get("content-type", "").lower()
    return "pdf" in ct

def download_pdf_to_disk(url: str,
                         download_dir: Path = DOWNLOAD_DIR,
                         max_bytes: int = MAX_PDF_BYTES,
                         verify_ssl: bool = True,
                         head_timeout: int = HEAD_TIMEOUT,
                         get_timeout: int = GET_TIMEOUT) -> Path | None:
    """
    Download URL to disk if it's a PDF (or appears to be). Returns filepath or None.
    """
    try:
        # Try HEAD first to check content-type and size (some servers block HEAD; we handle exceptions)
        try:
            head = session.head(url, allow_redirects=True, timeout=head_timeout, verify=certifi.where() if verify_ssl else False)
            headers = head.headers or {}
        except Exception:
            headers = {}

        # If HEAD says not pdf and URL doesn't look like pdf, still try GET if URL contains 'pdf' or 'download'
        looks_like_pdf = url.lower().endswith(".pdf") or "file=" in url.lower() or "pdf" in url.lower() or _is_pdf_content_type(headers)

        if not looks_like_pdf:
            # no obvious pdf signal — skip downloading by default
            return None

        # If content-length too large, skip
        content_length = headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > max_bytes:
                    print(f"Skipping {url} (content-length too large: {content_length} bytes)")
                    return None
            except Exception:
                pass

        # Stream download to disk
        get_resp = session.get(url, stream=True, timeout=get_timeout, allow_redirects=True, verify=certifi.where() if verify_ssl else False)
        get_resp.raise_for_status()

        # Determine filename
        fname = _filename_from_url(url, get_resp.headers)
        filepath = download_dir / fname

        total = 0
        first_chunk = None
        with open(filepath, "wb") as f:
            for chunk in get_resp.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                if first_chunk is None:
                    first_chunk = chunk
                total += len(chunk)
                if total > max_bytes:
                    # abort and clean up
                    f.close()
                    filepath.unlink(missing_ok=True)
                    print(f"Aborting {url}: file exceeded max size {max_bytes} bytes")
                    return None
                f.write(chunk)

        # Quick validity check: either content-type says pdf OR file begins with %PDF
        # Read first few bytes
        try:
            with open(filepath, "rb") as fh:
                head_bytes = fh.read(4)
                if head_bytes.startswith(b"%PDF") or _is_pdf_content_type(get_resp.headers):
                    return filepath
                else:
                    # not a PDF
                    filepath.unlink(missing_ok=True)
                    print(f"Downloaded file for {url} is not a PDF (magic bytes != %PDF).")
                    return None
        except Exception as e:
            filepath.unlink(missing_ok=True)
            print(f"Error validating downloaded file for {url}: {e}")
            return None

    except requests.HTTPError as http_e:
        print(f"HTTP error downloading {url}: {http_e}")
        return None
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None

def extract_text_from_pdf_file(file_path: Path) -> str:
    """
    Extract text (and tables) using pdfplumber primarily; fallback to PyPDF2 if needed.
    Returns a string (may be empty).
    """
    text_pieces = []
    # Try pdfplumber
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                try:
                    page_text = page.extract_text() or ""
                    if page_text:
                        text_pieces.append(page_text)
                    # attempt to extract tables (if any)
                    try:
                        tables = page.extract_tables() or []
                        for table in tables:
                            for row in table:
                                row_text = " | ".join(cell if cell else "" for cell in row)
                                text_pieces.append(row_text)
                    except Exception:
                        # ignore table-specific errors
                        pass
                except Exception:
                    # skip page-level errors
                    continue
        combined = "\n".join(text_pieces).strip()
        if combined:
            return combined
    except Exception as e:
        # pdfplumber failed — we'll try PyPDF2 fallback
        print(f"pdfplumber failed for {file_path}: {e}")

    # PyPDF2 fallback (more tolerant for some malformed PDFs)
    try:
        reader = PdfReader(str(file_path))
        for page in reader.pages:
            try:
                ptext = page.extract_text() or ""
                if ptext:
                    text_pieces.append(ptext)
            except Exception:
                continue
        return "\n".join(text_pieces).strip()
    except Exception as e:
        print(f"PyPDF2 fallback failed for {file_path}: {e}")
        return ""

def fetch_pdf_text(urls,
                   download_dir: Path = DOWNLOAD_DIR,
                   max_bytes: int = MAX_PDF_BYTES,
                   verify_ssl: bool = True,
                   head_timeout: int = HEAD_TIMEOUT,
                   get_timeout: int = GET_TIMEOUT):
    """
    Main function to call: given a list of URLs, attempt to download PDF files and extract text.
    Returns:
        - pdf_texts: list of extracted strings (one per successful PDF)
        - succeeded_files: list of local file paths downloaded successfully
        - failed_urls: list of URLs that couldn't be downloaded or parsed
    """
    pdf_texts = []
    succeeded_files = []
    failed_urls = []

    for url in urls:
        # quick filter: only attempt when likely a PDF (extension or 'pdf' token)
        try_download = url.lower().endswith(".pdf") or "pdf" in url.lower() or "download" in url.lower()
        if not try_download:
            # Optionally: perform a HEAD to check content-type (avoid many HEADs if you have many urls)
            try:
                head = session.head(url, allow_redirects=True, timeout=head_timeout, verify=certifi.where() if verify_ssl else False)
                if not _is_pdf_content_type(head.headers):
                    # skip non-pdf url
                    continue
            except Exception:
                # if HEAD fails, we skip to avoid over-requesting
                continue

        file_path = download_pdf_to_disk(url, download_dir=download_dir, max_bytes=max_bytes, verify_ssl=verify_ssl, head_timeout=head_timeout, get_timeout=get_timeout)
        if not file_path:
            failed_urls.append(url)
            continue

        succeeded_files.append(str(file_path))
        text = extract_text_from_pdf_file(file_path)
        if text:
            pdf_texts.append(text)
        else:
            # keep file for manual inspection but mark as failed to extract
            failed_urls.append(url)

    # Summary log
    print(f"PDF fetch summary: succeeded {len(succeeded_files)}, failed {len(failed_urls)}")
    if failed_urls:
        print("Failed URLs (sample):")
        for u in failed_urls[:10]:
            print(" -", u)

    return pdf_texts, succeeded_files, failed_urls
