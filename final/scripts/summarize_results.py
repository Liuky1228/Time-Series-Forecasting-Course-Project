"""Audit saved R predictions and produce common inputs for report and slides."""
import csv
import json
import math
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "output" / "tables"
INCUMBENT = "SARIMA_011_110"


def read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def quarter_index(label):
    if not re.fullmatch(r"[0-9]{4}Q[1-4]", label):
        raise ValueError(label)
    return int(label[:4]) * 4 + int(label[5]) - 1


def quarter_label(index):
    year, q = divmod(index, 4)
    return f"{year}Q{q + 1}"


def score(rows):
    errors = [float(r["point"]) - float(r["actual"]) for r in rows]
    scales = [float(r["mase_scale"]) for r in rows]
    assert errors and all(math.isfinite(e) for e in errors)
    assert all(math.isfinite(s) and s > 0 for s in scales)
    return {"n": len(rows), "MAE": st.mean(map(abs, errors)),
            "RMSE": math.sqrt(st.mean(e**2 for e in errors)),
            "MASE": st.mean(abs(e)/s for e, s in zip(errors, scales))}


def verify_rows(rows):
    levels = {quarter_index(r["quarter"]): float(r["value_bn"])
              for r in read(ROOT/"data/processed/retail_quarterly.csv")}
    keys, by = set(), defaultdict(list)
    for row in rows:
        model, origin, h = row["model"], quarter_index(row["origin"]), int(row["h"])
        assert h in (1, 2)
        for bound1, bound2 in (("lo95", "lo80"), ("lo80", "hi80"), ("hi80", "hi95")):
            if row.get(bound1) and row.get(bound2):
                assert float(row[bound1]) <= float(row[bound2]), row
        key = model, origin, h
        assert key not in keys, key
        keys.add(key)
        target = origin + h
        assert row["target"] == quarter_label(target)
        assert math.isclose(float(row["actual"]), levels[target], abs_tol=1e-7)
        scale = st.mean(abs(levels[j]-levels[j-4])
                        for j in range(quarter_index("1995Q1"), origin+1))
        assert math.isclose(float(row["mase_scale"]), scale, abs_tol=1e-7)
        by[model,h].append(row)
    origins = set(range(quarter_index("2012Q1"),quarter_index("2025Q4")+1))
    for case, group in by.items():
        assert {quarter_index(r["origin"]) for r in group} == origins, case
    return by


def main():
    assert (ROOT/"output/analysis_status.txt").read_text(encoding="utf-8").strip()=="COMPLETE", \
        "R workflow has not reached COMPLETE"
    rows = read(TABLES/"tab_rolling_errors.csv")
    by = verify_rows(rows)
    assert len(by)==34 and len(rows)==17*56*2
    supplemental = read(TABLES/"tab_supplemental_predictions.csv")
    supplemental_by = verify_rows(supplemental)
    assert len(supplemental_by)==4 and len(supplemental)==2*56*2
    keyed = {(r["model"],r["origin"],r["h"]):r for r in rows}
    choices = {r["origin"]:r for r in read(TABLES/"tab_walk_forward_choices.csv")}
    assert len(choices)==56
    candidates=(INCUMBENT,"SARIMA_011_011","SARIMA_011_101")
    for origin,c in choices.items():
        past=[[r for r in by[m,2] if quarter_index(r["target"])<=quarter_index(origin)]
              for m in candidates]
        assert int(c["n_realized"])==len(past[0])
        chosen=INCUMBENT if len(past[0])<8 else min(
            enumerate(past),key=lambda pair:score(pair[1])["MASE"])[0]
        assert c["model"]==(candidates[chosen] if isinstance(chosen,int) else chosen)
    for r in supplemental:
        o,h=r["origin"],r["h"]
        if r["model"]=="Blend50_Incumbent_SNaive":
            expect=(float(keyed[INCUMBENT,o,h]["point"])+float(keyed["SNaive",o,h]["point"]))/2
        else:
            expect=float(keyed[choices[o]["model"],o,h]["point"])
        assert math.isclose(float(r["point"]),expect,abs_tol=1e-7)
    modes = {
        "all": lambda r: True, "Q1": lambda r: r["target"].endswith("Q1"),
        "pre2020": lambda r: r["target"] < "2020Q1",
        "since2020": lambda r: r["target"] >= "2020Q1",
        "recent_without_shocks": lambda r: r["target"] >= "2020Q1"
        and r["target"] not in ("2020Q1","2020Q2","2022Q2"),
    }
    metrics = {model: {name: score([r for r in group if fn(r)])
                       for name, fn in modes.items()}
               for (model,h), group in (by|supplemental_by).items() if h==2}
    h1 = {model: score(group) for (model,h),group in by.items() if h==1}
    for raw in read(TABLES/"tab_rolling_accuracy.csv"):
        actual = score(by[raw["model"],int(raw["h"])])
        for k,v in actual.items():
            assert math.isclose(v,float(raw[k]),abs_tol=1e-7),(raw["model"],k)
    # Supplementary selectors/blends may be emitted in a separate keyed table.
    supp_path = TABLES/"tab_optimization_accuracy.csv"
    if supp_path.exists():
        for r in read(supp_path):
            if r["h"] != "2":
                continue
            mode = {"All targets":"all","Q1 targets":"Q1","2012-2019":"pre2020",
                    "2020-2026Q2":"since2020"}.get(r["period"])
            if mode:
                entry = {k:float(r[k]) for k in ("MAE","RMSE","MASE")}
                entry["n"] = int(r["n"])
                old = metrics.setdefault(r["model"], {})
                if mode in old:
                    assert all(math.isclose(old[mode][k],v,abs_tol=1e-7)
                               for k,v in entry.items()),(r["model"],mode)
                old[mode]=entry

    intervals=[]
    for r in read(TABLES/"tab_interval_accuracy.csv"):
        m,h,nominal=r["model"],int(r["h"]),float(r["level"])
        if nominal>1:nominal/=100
        group = (by|supplemental_by).get((m,h), [])
        if r["period"]=="All targets" and group:
            suffix=str(int(round(nominal*100)))
            observed = [(float(x["actual"]),float(x["lo"+suffix]),float(x["hi"+suffix]))
                        for x in group]
            assert len(observed)==int(r["n"])
            assert math.isclose(st.mean(l <= y <= u for y,l,u in observed),float(r["coverage"]),abs_tol=1e-8)
            assert math.isclose(st.mean(u-l for y,l,u in observed),float(r["width"]),abs_tol=1e-7)
            winkler=st.mean(u-l+2/(1-nominal)*max(l-y,y-u,0) for y,l,u in observed)
            assert math.isclose(winkler,float(r["Winkler"]),abs_tol=1e-6)
        intervals.append({"model":m,"h":h,"nominal":nominal,"n":int(r["n"]),
            "coverage":float(r["coverage"]),"width":float(r["width"]),
            "score":float(r["Winkler"]),"period":r["period"]})

    def forecasts(file):
        return [{k:r[k] if k in ("quarter","model") else float(r[k])
                 for k in ("quarter","model","point","lo80","hi80","lo95","hi95")}
                for r in read(TABLES/file)]

    original = forecasts("tab_final_forecast.csv")
    rerun = forecasts("tab_final_forecast_rerun.csv")
    assert [r["quarter"] for r in original] == ["2026Q3","2026Q4"]
    assert all(r["model"] == INCUMBENT for r in original+rerun)
    public = read(ROOT/"reference/nbs_q3_releases.csv")
    actual = float(public[1]["cumulative_retail_100m_cny"])-float(public[0]["cumulative_retail_100m_cny"])
    q3=original[0]
    dm_rows = read(TABLES/"tab_dm_tests.csv")
    dm = {f"h{h}": next(float(r["p_value"]) for r in dm_rows
                         if r["h"]==str(h) and r["Comparison"]==INCUMBENT+" vs SNaive")
          for h in (1,2)}
    result={"metrics":metrics,"h1":h1,"intervals":intervals,
            "forecasts":original,"rerun_forecasts":rerun,"dm":dm,
            "diagnostics":read(TABLES/"tab_diagnostics.csv")[0],
            "q3_actual":{"actual":actual,"forecast":q3["point"],
                "error_pct":100*(q3["point"]/actual-1),
                "inside80":q3["lo80"]<=actual<=q3["hi80"],
                "sources":[r["url"] for r in public]},
            "independently_checked_rows":len(rows),
            "independently_checked_supplemental_rows":len(supplemental)}
    (ROOT/"output/optimization_summary.json").write_text(json.dumps(result,indent=2,allow_nan=False,sort_keys=True),encoding="utf-8")
    print(f"PASS: {len(rows)} fitted prediction rows, {len(supplemental)} supplementary rows, chronological choices and interval arithmetic")


if __name__=="__main__":
    main()
