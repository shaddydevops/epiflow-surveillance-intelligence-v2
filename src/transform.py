import pandas as pd
import numpy as np

def build_analysis_dataset(df, drop_exact=True, dedupe=False):
    out=df.copy()
    for c in out.select_dtypes(include=["object","string"]).columns:
        out[c]=out[c].astype("string").str.strip()

    if "sex" in out:
        s=out["sex"].astype("string").str.lower()
        out["sex"]=s.replace({"m":"Male","male":"Male","f":"Female","female":"Female"}).str.title()
    if "classification" in out:
        s=out["classification"].astype("string").str.lower()
        out["classification"]=s.replace({"confirmd":"confirmed"}).str.title()
    if "outcome" in out:
        s=out["outcome"].astype("string").str.lower()
        out["outcome"]=s.replace({"dead":"died","death":"died"}).str.title()

    if "age" in out:
        out["age"]=pd.to_numeric(out["age"],errors="coerce")
        out.loc[~out["age"].between(0,120),"age"]=np.nan
        out["age_group"]=pd.cut(
            out["age"],bins=[0,5,15,25,35,45,60,121],right=False,
            labels=["0–4","5–14","15–24","25–34","35–44","45–59","60+"]
        )

    for c in ["date_onset","date_reported"]:
        if c in out:
            out[c]=pd.to_datetime(out[c],errors="coerce")
    if {"date_onset","date_reported"}.issubset(out.columns):
        out["reporting_delay_days"]=(out["date_reported"]-out["date_onset"]).dt.days
        out.loc[out["reporting_delay_days"]<0,"reporting_delay_days"]=np.nan
    if "date_onset" in out:
        out["epi_week"]=out["date_onset"].dt.to_period("W-SUN").apply(
            lambda x: x.start_time if pd.notna(x) else pd.NaT
        )

    if "latitude" in out:
        out["latitude"]=pd.to_numeric(out["latitude"],errors="coerce")
    if "longitude" in out:
        out["longitude"]=pd.to_numeric(out["longitude"],errors="coerce")
    if {"latitude","longitude"}.issubset(out.columns):
        bad=(~out["latitude"].between(-90,90))|(~out["longitude"].between(-180,180))
        out.loc[bad.fillna(False),["latitude","longitude"]]=np.nan

    if drop_exact:
        out=out.drop_duplicates().copy()
    if dedupe and "case_id" in out:
        out=out.drop_duplicates(subset="case_id",keep="first").copy()
    return out
