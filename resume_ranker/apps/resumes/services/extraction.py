from pypdf import PdfReader
import docx

def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()

def extract_text_from_docx(path: str) -> str:
    d = docx.Document(path)
    return "\n".join([p.text for p in d.paragraphs]).strip()

def extract_text(resume) -> str:
    path = resume.file.path
    name = (resume.original_filename or "").lower()
    if name.endswith(".pdf"):
        return extract_text_from_pdf(path)
    if name.endswith(".docx"):
        return extract_text_from_docx(path)
    raise ValueError("Unsupported file type. Only PDF/DOCX supported.")
