import folium
from folium.plugins import MarkerCluster

def internal_case_map(df):
    spatial=df.dropna(subset=["latitude","longitude"]).copy()
    if spatial.empty:return None
    center=[float(spatial["latitude"].median()),float(spatial["longitude"].median())]
    m=folium.Map(location=center,zoom_start=6,tiles="CartoDB positron")
    cluster=MarkerCluster().add_to(m)
    for _,r in spatial.iterrows():
        fields=[]
        for label,key in [("Case","case_id"),("Region","region"),("District","district"),("Classification","classification")]:
            if key in spatial.columns:
                fields.append(f"<b>{label}:</b> {r.get(key,'')}")
        folium.CircleMarker([r["latitude"],r["longitude"]],radius=4,popup="<br>".join(fields),fill=True,fill_opacity=.65).add_to(cluster)
    return m

def briefing_aggregate_map(df,field="district"):
    if not {field,"latitude","longitude"}.issubset(df.columns):
        return None,None
    spatial=df.dropna(subset=[field,"latitude","longitude"]).copy()
    if spatial.empty:return None,None
    if "case_id" in spatial:
        summary=spatial.groupby(field,dropna=False).agg(
            reported_cases=("case_id","count"),latitude=("latitude","mean"),longitude=("longitude","mean")
        ).reset_index()
    else:
        summary=spatial.groupby(field,dropna=False).agg(
            reported_cases=(field,"size"),latitude=("latitude","mean"),longitude=("longitude","mean")
        ).reset_index()
    center=[float(summary["latitude"].median()),float(summary["longitude"].median())]
    m=folium.Map(location=center,zoom_start=6,tiles="CartoDB positron")
    for _,r in summary.iterrows():
        folium.CircleMarker(
            [r["latitude"],r["longitude"]],
            radius=max(5,min(22,4+float(r["reported_cases"])**0.6*2.5)),
            popup=f"<b>{field.title()}:</b> {r[field]}<br>Reported cases: {int(r['reported_cases'])}",
            tooltip=f"{r[field]}: {int(r['reported_cases'])} reported",
            fill=True,fill_opacity=.55
        ).add_to(m)
    return m,summary
