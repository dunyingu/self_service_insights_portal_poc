from typing import List, Dict, Any

def data_to_charts(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {}
    cols = list(rows[0].keys())
    num_cols = [c for c in cols if isinstance(rows[0].get(c), (int, float))]
    date_cols = [c for c in cols if 'DATE' in c.upper()]
    if date_cols and num_cols:
        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "mark": "line",
            "encoding": {"x": {"field": date_cols[0], "type": "temporal"},
                         "y": {"field": num_cols[0], "type": "quantitative"}},
            "data": {"values": rows},
        }
    str_cols = [c for c in cols if isinstance(rows[0].get(c), str)]
    if str_cols and num_cols:
        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "mark": "bar",
            "encoding": {"x": {"field": str_cols[0], "type": "nominal"},
                         "y": {"field": num_cols[0], "type": "quantitative"}},
            "data": {"values": rows},
        }
    return {}
