"""Create a versioned course ZIP; never overwrite an existing archive by default."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "FinalReport_gp12.pdf", "FinalReport_gp12.docx", "Presentation_gp12.pdf",
    "README.md", "R/run_all.R", "output/optimization_summary.json",
    "output/verification/clean_run.json",
)


def create_zip(destination, candidate=False):
    if ROOT in destination.parents:
        raise ValueError("Store ZIP outside its input directory")
    required = REQUIRED[:-1] if candidate else REQUIRED
    for name in required:
        if not (ROOT/name).is_file():
            raise FileNotFoundError(name)
    if not candidate:
        assert json.loads((ROOT/REQUIRED[-1]).read_text(encoding="utf-8"))["status"]=="passed"
    files = {}
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if not path.is_file() or path.name.startswith(("~$", ".DS_Store")):
            continue
        if any(x in ("__pycache__", ".git", ".Rlibrary", "models") for x in rel.parts):
            continue
        if path.suffix.lower() in (".pyc",".rds",".rdata",".exe",".dll",".zip"):
            continue
        files[rel.as_posix()]=path
    with ZipFile(destination, "x", compression=ZIP_DEFLATED) as archive:
        for name,path in files.items():
            archive.write(path,name)
    with ZipFile(destination) as archive:
        assert archive.testzip() is None and set(archive.namelist())==set(files)
        assert all(archive.read(name)==path.read_bytes() for name,path in files.items())
    print(f"Verified {destination}: {len(files)} files")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination",type=Path)
    parser.add_argument("--candidate",action="store_true",help="Allow packaging before clean-run receipt")
    args=parser.parse_args()
    create_zip(args.destination.resolve(),args.candidate)
