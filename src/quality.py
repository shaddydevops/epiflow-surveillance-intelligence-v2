import pandas as pd

def completeness_table(df):
    return pd.DataFrame({
        "variable": df.columns,
        "missing": [int(df[c].isna().sum()) for c in df.columns],
        "complete": [int(df[c].notna().sum()) for c in df.columns],
        "completeness_percent": [round(df[c].notna().mean()*100, 1) for c in df.columns],
    }).sort_values("completeness_percent")

def quality_audit(df):
    rows=[]
    def add(check,status,affected=0,detail=""):
        rows.append({"check":check,"status":status,"affected":int(affected),"detail":detail})
    add("Dataset has records","PASS" if len(df) else "FAIL",0 if len(df) else 1,f"{len(df):,} records")
    if "case_id" in df:
        dup=int(df["case_id"].duplicated(keep=False).sum())
        add("Repeated case_id","WARN" if dup else "PASS",dup,"Repeated IDs require domain review.")
    if "age" in df:
        age=pd.to_numeric(df["age"],errors="coerce")
        bad=int((~age.between(0,120)&age.notna()).sum())
        add("Age plausibility 0–120","FAIL" if bad else "PASS",bad)
    if "date_onset" in df:
        onset=pd.to_datetime(df["date_onset"],errors="coerce")
        bad=int(df["date_onset"].notna().sum()-onset.notna().sum())
        add("Onset dates parse","WARN" if bad else "PASS",bad)
    if "date_reported" in df:
        rep=pd.to_datetime(df["date_reported"],errors="coerce")
        bad=int(df["date_reported"].notna().sum()-rep.notna().sum())
        add("Reported dates parse","WARN" if bad else "PASS",bad)
    if {"date_onset","date_reported"}.issubset(df.columns):
        onset=pd.to_datetime(df["date_onset"],errors="coerce")
        rep=pd.to_datetime(df["date_reported"],errors="coerce")
        bad=int((rep<onset).fillna(False).sum())
        add("Report date not before onset","FAIL" if bad else "PASS",bad)
    if {"latitude","longitude"}.issubset(df.columns):
        lat=pd.to_numeric(df["latitude"],errors="coerce")
        lon=pd.to_numeric(df["longitude"],errors="coerce")
        bad=int(((~lat.between(-90,90))|(~lon.between(-180,180))).fillna(False).sum())
        add("Coordinate plausibility","FAIL" if bad else "PASS",bad)
    miss=int(df.isna().sum().sum())
    add("Missing cells","WARN" if miss else "PASS",miss)
    return pd.DataFrame(rows)
