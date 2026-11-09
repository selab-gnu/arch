"""처리할 PDF 고르기 — 명령행 인자(파일·폴더)를 PDF 목록으로 바꾸고, PDF가 없으면 샘플을 만듭니다."""

from pathlib import Path

DATA_DIR = Path(__file__).with_name("data")


# 샘플 PDF 생성 (PDF를 지정하지 않았고 data/ 폴더도 없을 때만 사용)
def make_sample_pdf(path: Path) -> Path:
    from fpdf import FPDF

    lines = [
        "INVOICE  #INV-2026-1108",
        "Issue date: 2026-11-08    Due date: 2026-12-08",
        "From: Acme Cloud Services Inc. (billing@acmecloud.example, +1-415-555-0142)",
        "To: Gyeongsang Software Lab",
        "",
        "Items:",
        "  - GPU compute (A100, 120 hours) ........ $3,600.00",
        "  - Object storage (2 TB, 1 month) ....... $46.00",
        "  - Premium support plan ................. $299.00",
        "",
        "Subtotal: $3,945.00   Tax (10%): $394.50   Total due: $4,339.50",
        "Pay online at https://pay.acmecloud.example/inv-2026-1108",
        "Late payments incur a 1.5% monthly fee.",
    ]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in lines:
        pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))
    return path


def collect_pdfs(args: list[str]) -> list[Path]:
    """명령행 인자(파일 또는 폴더)를 PDF 경로 목록으로 바꿉니다. 인자가 없으면 data/invoice_en.pdf."""
    if not args:
        default = DATA_DIR / "invoice_en.pdf"
        if default.exists():
            return [default]
        path = make_sample_pdf(Path(__file__).with_name("sample_invoice.pdf"))
        print(f"data/ 폴더가 없어 샘플 PDF를 만들었습니다: {path}")
        return [path]
    pdfs: list[Path] = []
    for arg in args:
        p = Path(arg).expanduser()
        pdfs.extend(sorted(p.glob("*.pdf")) if p.is_dir() else [p])
    return pdfs
