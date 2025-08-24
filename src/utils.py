\
import re
import unicodedata
from typing import Optional
from dateutil import parser

def normalize_text(x: Optional[str]) -> str:
    if x is None:
        return ""
    # Unicode normalize, lower, strip
    x = unicodedata.normalize("NFKD", str(x)).encode("ASCII", "ignore").decode("ASCII")
    x = x.lower().strip()
    # collapse whitespace, remove punctuation except internal hyphens/apostrophes
    x = re.sub(r"[^\w\s'-]", " ", x)
    x = re.sub(r"\s+", " ", x).strip()
    return x

def normalize_name(x: Optional[str]) -> str:
    return normalize_text(x)

def parse_date_safe(x: Optional[str]):
    if not x or (isinstance(x, float) and str(x) == "nan"):
        return None, None, None
    try:
        dt = parser.parse(str(x), dayfirst=False, yearfirst=False, fuzzy=True, default=None)
        # Some partial dates may parse to today's date if default not set; guard:
        y = dt.year if dt.year and 1000 <= dt.year <= 2100 else None
        m = dt.month if dt else None
        d = dt.day if dt else None
        return y, m, d
    except Exception:
        # Attempt to extract a year
        m = re.search(r"(1[5-9]\d{2}|20\d{2})", str(x))
        y = int(m.group(1)) if m else None
        return y, None, None

def safe_equal(a, b):
    return a == b and a is not None and b is not None
