\
import pandas as pd
import jellyfish

def double_metaphone_safe(s: str):
    if not s:
        return ("","")
    try:
        return jellyfish.metaphone(s), jellyfish.metaphone(s)  # fallback to metaphone for simplicity
    except Exception:
        return ("","")

def surname_metaphone_year_block(df: pd.DataFrame) -> pd.Series:
    # combine metaphone of surname and year of birth
    surname_key = df["surname_clean"].fillna("").apply(lambda x: (double_metaphone_safe(x)[0] or x[:1]))
    year_key = df["dob_year"].fillna(-1).astype(int).astype(str)
    return surname_key.astype(str) + "|" + year_key

def postcode_prefix_year_block(df: pd.DataFrame, prefix_len: int = 3) -> pd.Series:
    pc = df["postcode_clean"].fillna("").str[:prefix_len]
    year_key = df["dob_year"].fillna(-1).astype(int).astype(str)
    return pc + "|" + year_key

def first_initial_year_block(df: pd.DataFrame) -> pd.Series:
    fi = df["first_name_clean"].fillna("").str[:1]
    year_key = df["dob_year"].fillna(-1).astype(int).astype(str)
    return fi + "|" + year_key

def apply_blocking(df: pd.DataFrame, strategy: str, postcode_prefix_len: int = 3) -> pd.Series:
    if strategy == "surname_metaphone_year":
        return surname_metaphone_year_block(df)
    elif strategy == "postcode_prefix_year":
        return postcode_prefix_year_block(df, postcode_prefix_len)
    elif strategy == "first_initial_year":
        return first_initial_year_block(df)
    else:
        return surname_metaphone_year_block(df)
