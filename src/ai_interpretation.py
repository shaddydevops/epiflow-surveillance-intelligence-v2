import os,json
from anthropic import Anthropic
from .analytics import weekly_curve,top_places,completeness_summary

SYSTEM="""You are an epidemiological analysis assistant.
Use only supplied aggregated analytical evidence.
Do not invent statistics, denominators, causal explanations, significance, incidence, prevalence or population risk.
Distinguish observed evidence from interpretation.
Highlight data-quality and reporting limitations.
Use cautious public-health language.
Return sections: Executive Summary; Person; Place; Time; Data Quality and Timeliness; What We Cannot Conclude; Questions for Further Investigation; Suggested Public Health Follow-up; Bottom Line.
"""

def build_evidence(df,indicators,audit):
    weekly=weekly_curve(df).tail(16).copy()
    if not weekly.empty:weekly["epi_week"]=weekly["epi_week"].astype(str)
    districts=top_places(df,"district",10) if "district" in df else None
    regions=top_places(df,"region",10) if "region" in df else None
    return {
        "indicators":indicators,
        "weekly_reported_cases":weekly.to_dict("records"),
        "top_districts_by_reported_burden":districts.to_dict("records") if districts is not None else [],
        "top_regions_by_reported_burden":regions.to_dict("records") if regions is not None else [],
        "quality_audit":audit.to_dict("records"),
        "completeness":completeness_summary(df).to_dict("records"),
    }

def interpret_surveillance_results(df,indicators,audit):
    key=os.getenv("ANTHROPIC_API_KEY")
    if not key:return None,"ANTHROPIC_API_KEY is not configured."
    model=os.getenv("ANTHROPIC_MODEL","claude-3-5-sonnet-latest")
    client=Anthropic(api_key=key)
    evidence=build_evidence(df,indicators,audit)
    response=client.messages.create(
        model=model,max_tokens=2600,system=SYSTEM,
        messages=[{"role":"user","content":"Interpret this validated aggregated surveillance evidence:\n\n"+json.dumps(evidence,default=str,indent=2)}],
    )
    text="".join(block.text for block in response.content if hasattr(block,"text"))
    return text,None
