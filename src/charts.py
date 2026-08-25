import plotly.express as px
from .analytics import epi_curve, weekly_curve, top_places

def epidemic_curve_figure(df):
    d=epi_curve(df)
    return None if d.empty else px.bar(d,x="date_onset",y="cases",title="Epidemic curve by symptom-onset date")

def weekly_curve_figure(df):
    d=weekly_curve(df)
    return None if d.empty else px.line(d,x="epi_week",y="cases",markers=True,title="Weekly symptom-onset trend")

def place_figure(df,field="district"):
    d=top_places(df,field)
    return None if d.empty else px.bar(d.sort_values("cases"),x="cases",y=field,orientation="h",title=f"Leading {field}s by reported case burden")

def age_figure(df):
    if "age_group" not in df:return None
    d=df["age_group"].value_counts().sort_index().rename("cases").to_frame().reset_index()
    d.columns=["age_group","cases"]
    return px.bar(d,x="age_group",y="cases",title="Reported cases by age group")

def sex_figure(df):
    if "sex" not in df:return None
    d=df["sex"].value_counts(dropna=False).rename("cases").to_frame().reset_index()
    d.columns=["sex","cases"]
    return px.bar(d,x="sex",y="cases",title="Reported cases by sex")

def outcome_figure(df):
    if "outcome" not in df:return None
    d=df["outcome"].value_counts(dropna=False).rename("cases").to_frame().reset_index()
    d.columns=["outcome","cases"]
    return px.bar(d,x="outcome",y="cases",title="Recorded outcomes")
