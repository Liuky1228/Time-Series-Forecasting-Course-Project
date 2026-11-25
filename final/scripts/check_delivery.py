"""Check report format, model-output integration, equations and final PDF boundaries."""
import json
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]


def main():
    d=Document(ROOT/"FinalReport_gp12.docx")
    for s in ("Normal","Title","Heading 1","Caption"):
        style=d.styles[s]
        assert style.font.name=="Times New Roman" and style.font.size.pt==12,s
        assert style.paragraph_format.space_after.pt==6 and style.paragraph_format.line_spacing==1.15,s
    assert all(r.font.size.pt==12 and r.font.name=="Times New Roman"
               for t in d.tables for row in t.rows for c in row.cells for p in c.paragraphs
               for r in p.runs if r.text.strip())
    with ZipFile(ROOT/"FinalReport_gp12.docx") as z:
        math_count=z.read("word/document.xml").count(b"<m:oMath>")
        assert math_count==3
    report=[p.extract_text() or "" for p in PdfReader(ROOT/"FinalReport_gp12.pdf").pages]
    slides=PdfReader(ROOT/"Presentation_gp12.pdf").pages
    end=next(i for i,x in enumerate(report) if "References" in [s.strip() for s in x.splitlines()])
    append=next(i for i,x in enumerate(report) if "Appendix Supplementary comparisons" in x)
    assert 7<=end<=10 and end<append<len(report)
    assert 7<=len(slides)<=8
    joined=" ".join(report)
    expected=["AI Use and Reflection","121,279","0.015","0.097","2026Q3","2026Q4"]
    assert all(x in joined for x in expected)
    normalize=lambda s:" ".join(s.split())
    abstract=normalize(report[0]).split("Abstract",1)[1].split("1 Forecasting",1)[0]
    assert all(s in abstract for s in ("did not consistently improve","5,548","5,655","9,056","8,908"))
    slide_text=normalize(" ".join(p.extract_text() or "" for p in slides))
    notes=normalize((ROOT/"docs/defense_notes.md").read_text(encoding="utf-8"))
    assert all("PACF" not in s for s in (joined,slide_text,notes))
    assert "observable at each origin" not in slide_text
    caveat="historical release dates and data vintages were not reconstructed"
    assert caveat in normalize(joined).lower() and caveat in slide_text.lower()
    assert "未重建历史发布日期或数据版本" in notes
    assert all("0.160" in s for s in (joined,slide_text,notes))
    assert "1.03e-11" in joined and "1.03e-11" in slide_text
    assert "should verify and amend" not in normalize(joined)
    assert all(len(s.strip())>30 for s in report)
    result={"status":"passed","main_pages":end,"reference_pages":append-end,
            "appendix_pages":len(report)-append,"report_pages":len(report),
            "presentation_slides":len(slides),"editable_OOXML_equations":math_count,
            "body_and_table_styles_TNR_12":True,"word_pdf_text_spot_checks":expected,
            "report_slides_notes_revision_checks":True}
    out=ROOT/"output/verification"
    out.mkdir(parents=True,exist_ok=True)
    (out/"delivery_checks.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result))


if __name__=="__main__":
    main()
