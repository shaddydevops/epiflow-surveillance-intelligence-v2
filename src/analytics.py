import pandas as pd

def rapid_indicators(df):
    x={"records":int(len(df))}
    if "case_id" in df:x["unique_case_ids"]=int(df["case_id"].nunique(dropna=True))
    if "age" in df and df["age"].notna().any():x["median_age"]=round(float(df["age"].median()),1)
    if "classification" in df:x["confirmed"]=int(df["classification"].astype("string").str.lower().eq("confirmed").sum())
    if "outcome" in df:x["deaths_recorded"]=int(df["outcome"].astype("string").str.lower().isin(["died","dead","death"]).sum())
    if "reporting_delay_days" in df:
        s=df["reporting_delay_days"].dropna()
        if len(s):
            x["median_reporting_delay_days"]=round(float(s.median()),1)
            x["p90_reporting_delay_days"]=round(float(s.quantile(.90)),1)
    if "region" in df:x["regions"]=int(df["region"].nunique(dropna=True))
    if "district" in df:x["districts"]=int(df["district"].nunique(dropna=True))
    return x

def categorical_profile(df, variable):
    s=df[variable]
    result=s.value_counts(dropna=False).rename("n").to_frame()
    result["percent"]=(result["n"]/len(df)*100).round(1)
    result=result.reset_index()
    result.columns=[variable,"n","percent"]
    return result

def epi_curve(df):
    if "date_onset" not in df:return pd.DataFrame(columns=["date_onset","cases"])
    return df.dropna(subset=["date_onset"]).groupby("date_onset").size().rename("cases").reset_index()

def weekly_curve(df):
    if "epi_week" not in df:return pd.DataFrame(columns=["epi_week","cases"])
    return df.dropna(subset=["epi_week"]).groupby("epi_week").size().rename("cases").reset_index()

def top_places(df, field="district", n=12):
    if field not in df:return pd.DataFrame(columns=[field,"cases"])
    d=df[field].value_counts(dropna=False).head(n).rename("cases").reset_index()
    d.columns=[field,"cases"]
    return d

def completeness_summary(df):
    rows=[]
    for c in ["case_id","age","sex","date_onset","date_reported","classification","outcome","region","district","latitude","longitude"]:
        if c in df:
            rows.append({"metric":f"{c} completeness","percent":round(float(df[c].notna().mean()*100),1)})
    return pd.DataFrame(rows).sort_values("percent") if rows else pd.DataFrame(columns=["metric","percent"])
