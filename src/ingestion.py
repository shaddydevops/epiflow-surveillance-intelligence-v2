from pathlib import Path
import pandas as pd

def load_tabular(source):
    name = getattr(source, "name", str(source))
    ext = Path(name).suffix.lower()
    if ext == ".csv":
        return pd.read_csv(source)
    if ext in {".xlsx", ".xls"}:
        return pd.read_excel(source)
    if ext == ".parquet":
        return pd.read_parquet(source)
    raise ValueError(f"Unsupported file type: {ext}")

def normalize_column_names(df):
    out = df.copy()
    out.columns = (
        out.columns.astype(str).str.strip().str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True).str.strip("_")
    )
    return out
