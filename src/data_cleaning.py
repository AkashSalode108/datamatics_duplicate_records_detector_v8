\
import pandas as pd
from .utils import normalize_text, normalize_name, parse_date_safe

REQUIRED_COLS = ["unique_id","first_name","surname","dob","birth_place","postcode","gender","occupation"]

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # ensure required columns exist
    for c in REQUIRED_COLS:
        if c not in df.columns:
            df[c] = None

    out = df.copy()
    out["first_name_clean"] = out["first_name"].apply(normalize_name)
    out["surname_clean"] = out["surname"].apply(normalize_name)
    out["birth_place_clean"] = out["birth_place"].apply(normalize_text)
    out["postcode_clean"] = out["postcode"].astype(str).str.upper().str.replace(" ", "", regex=False)
    out["gender_clean"] = out["gender"].astype(str).str.strip().str.lower().map({
        "m":"m","male":"m","f":"f","female":"f","u":"u","unknown":"u"
    }).fillna("u")
    out["occupation_clean"] = out["occupation"].apply(normalize_text)

    # DOB parts
    dob_parts = out["dob"].apply(parse_date_safe)
    out["dob_year"] = dob_parts.apply(lambda t: t[0])
    out["dob_month"] = dob_parts.apply(lambda t: t[1])
    out["dob_day"] = dob_parts.apply(lambda t: t[2])
    return out
