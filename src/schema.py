from .constants import ALIASES

def suggest_mapping(columns):
    cols = list(columns)
    normalized = {str(c).lower(): c for c in cols}
    result = {}
    for canon, aliases in ALIASES.items():
        for alias in aliases:
            if alias.lower() in normalized:
                result[canon] = normalized[alias.lower()]
                break
    return result

def apply_mapping(df, mapping):
    chosen = {src: canon for canon, src in mapping.items() if src}
    out = df.rename(columns=chosen).copy()
    mapped = [c for c in mapping if c in out.columns]
    extras = [c for c in out.columns if c not in mapped]
    return out[mapped + extras]
