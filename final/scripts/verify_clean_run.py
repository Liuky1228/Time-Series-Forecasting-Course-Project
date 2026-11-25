"""Run the full workflow from a fresh folder containing only packaged inputs and code."""
import argparse
import csv
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def compare_table(a,b,key):
    rows1,rows2=read_csv(a),read_csv(b)
    arows={tuple(r[k] for k in key):r for r in rows1}
    brows={tuple(r[k] for k in key):r for r in rows2}
    assert len(rows1)==len(arows)==len(rows2)==len(brows) and arows.keys()==brows.keys(),a
    for ix,r in arows.items():
        other=brows[ix]
        assert r.keys()==other.keys(),(a,ix)
        for k,v in r.items():
            if v==other[k]:
                continue
            try:
                left,right=float(v),float(other[k])
            except ValueError as exc:
                raise AssertionError((a,ix,k,v,other[k])) from exc
            assert math.isclose(left,right,rel_tol=1e-9,abs_tol=1e-7),(a,ix,k,v,other[k])
    return len(arows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rscript",required=True,type=Path)
    parser.add_argument("--word-pdf",action="store_true",help="Also test desktop Word export on Windows")
    parser.add_argument("--pwsh",default="pwsh.exe",help="PowerShell 7 executable for Word export")
    args=parser.parse_args()
    verify=ROOT/"output/verification"
    verify.mkdir(parents=True,exist_ok=True)
    scratch=Path(tempfile.mkdtemp(prefix="sta4003-clean-20261116-"))
    for folder in ("data","reference","R","scripts","tests","docs"):
        if (ROOT/folder).exists():
            shutil.copytree(ROOT/folder,scratch/folder,ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(ROOT/"build_quarterly.py",scratch/"build_quarterly.py")
    for entry in ("make_equations.py","build_final_report.py"):
        if (ROOT/entry).exists():
            shutil.copy2(ROOT/entry,scratch/entry)
    assert not (scratch/"output").exists()
    raw_files={p.relative_to(scratch):p.read_bytes() for p in (scratch/"data/raw").glob("*") if p.is_file()}
    commands=[
        (sys.executable,"-X","utf8","build_quarterly.py"),
        (str(args.rscript),"--vanilla","tests/test_optimization.R"),
        (str(args.rscript),"--vanilla","R/run_all.R"),
        (str(args.rscript),"--vanilla","tests/test_outputs.R"),
        (sys.executable,"-X","utf8","scripts/test_summary.py"),
        (sys.executable,"-X","utf8","scripts/summarize_results.py"),
        (sys.executable,"-X","utf8","make_equations.py"),
        (sys.executable,"-X","utf8","build_final_report.py"),
    ]
    if args.word_pdf:
        commands.extend([
            (args.pwsh,"-NoProfile","-File","scripts/export_report.ps1"),
            (sys.executable,"-X","utf8","scripts/check_delivery.py"),
        ])
    env=dict(os.environ)
    if sys.platform=="win32":
        env["LC_ALL"]=".UTF-8"
    started=time.monotonic()
    print("Clean work directory:",scratch,flush=True)
    log=verify/("clean_run_"+scratch.name.rsplit("-",1)[-1]+".txt")
    with log.open("wb") as f:
        for command in commands:
            result=subprocess.run(command,cwd=scratch,env=env,stdout=f,stderr=subprocess.STDOUT)
            if result.returncode:
                raise RuntimeError(f"{command} exited {result.returncode}; see {log}")
            print("PASS",command[-1],flush=True)
    assert all((scratch/f).read_bytes()==x for f,x in raw_files.items())
    checks={}
    for name,keys in [
        ("tab_rolling_errors.csv",("model","origin","h")),
        ("tab_rolling_accuracy.csv",("model","h")),
        ("tab_interval_accuracy.csv",("model","h","level","period")),
        ("tab_final_forecast_rerun.csv",("quarter","model")),
    ]:
        rel=Path("output/tables")/name
        checks[name]=compare_table(ROOT/rel,scratch/rel,keys)
    for name in ("FinalReport_gp12.docx",):
        assert (scratch/name).stat().st_size>10000
    if (scratch/"Presentation_gp12.pdf").exists():
        assert (scratch/"Presentation_gp12.pdf").stat().st_size>10000
    originals = sorted((ROOT/"output/tables").glob("*.csv"))
    regenerated = sorted((scratch/"output/tables").glob("*.csv"))
    assert [p.name for p in originals]==[p.name for p in regenerated]
    byte_equal_csvs = sum(p.read_bytes()==q.read_bytes() for p,q in zip(originals,regenerated))
    assert (scratch/"output/optimization_summary.json").read_bytes()==(ROOT/"output/optimization_summary.json").read_bytes()
    if args.word_pdf:
        from pypdf import PdfReader
        for name in ("FinalReport_gp12.pdf","Presentation_gp12.pdf"):
            extract=lambda f:[page.extract_text() for page in PdfReader(f).pages]
            assert extract(ROOT/name)==extract(scratch/name),name
    slides_present = (scratch/"Presentation_gp12.pdf").exists()
    result={"status":"passed","seconds":round(time.monotonic()-started,2),
            "no_outputs_or_cache_at_start":True,"raw_inputs_unchanged":True,
            "numeric_table_checks":checks,"summary_equal":True,
            "r_result_csvs":len(originals),"byte_identical_r_csvs":byte_equal_csvs,
            "report_word_regenerated":True,
            "slides_regenerated":slides_present,
            "report_and_slides_pdf_text_agrees":args.word_pdf,"log":log.name}
    (verify/"clean_run.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result),flush=True)


if __name__=="__main__":
    main()
