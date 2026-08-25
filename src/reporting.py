def build_brief(df,ind):
    parts=[f"The analysis dataset contains {ind.get('records',len(df)):,} records."]
    if ind.get("confirmed") is not None:parts.append(f"{ind['confirmed']:,} records are classified as confirmed.")
    if ind.get("deaths_recorded") is not None:parts.append(f"{ind['deaths_recorded']:,} death outcomes are recorded.")
    if ind.get("median_reporting_delay_days") is not None:parts.append(f"The median observed reporting delay is {ind['median_reporting_delay_days']} days.")
    if ind.get("districts") is not None:parts.append(f"Records span {ind['districts']} districts.")
    parts.append("Reported case counts describe burden in the available data and should not be interpreted as population risk without appropriate denominators.")
    return " ".join(parts)
