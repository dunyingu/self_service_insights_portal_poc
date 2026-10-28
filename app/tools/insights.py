from typing import List, Dict, Any
import pandas as pd

def data_to_insights(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "No rows returned."
    df = pd.DataFrame(rows)
    pieces = []
    for col in df.select_dtypes(include='number').columns:
        pieces.append(f"Avg {col}: {df[col].mean():,.2f}; Sum {col}: {df[col].sum():,.2f}")
    if 'ORDER_DATE' in df.columns:
        pieces.append(f"Date range: {df['ORDER_DATE'].min()} → {df['ORDER_DATE'].max()}")
    return " | ".join(pieces) if pieces else f"Returned {len(df)} rows."
