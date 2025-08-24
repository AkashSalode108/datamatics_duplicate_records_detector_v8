\
from rapidfuzz import fuzz, distance
import jellyfish

def name_similarity(fn1, sn1, fn2, sn2):
    # Base string sims
    s1 = f"{fn1} {sn1}".strip()
    s2 = f"{fn2} {sn2}".strip()
    jw = distance.JaroWinkler.similarity(s1, s2) / 100.0
    ts = fuzz.token_set_ratio(s1, s2) / 100.0

    # Phonetic boost if metaphone matches on surname OR first name initial matches
    try:
        mp1 = jellyfish.metaphone(sn1 or "")
        mp2 = jellyfish.metaphone(sn2 or "")
        phonetic = 1.0 if mp1 and mp1 == mp2 else 0.0
    except Exception:
        phonetic = 0.0

    # First initial check
    initials = (fn1[:1] and fn1[:1] == fn2[:1]) and (sn1[:1] and sn1[:1] == sn2[:1])
    init_boost = 0.05 if initials else 0.0

    return max(jw, ts) + 0.1*phonetic + init_boost

def dob_similarity(y1, m1, d1, y2, m2, d2):
    # year exact: 1; year off by 1 (common) 0.5; month/day exact add small bump
    if y1 is None or y2 is None:
        base = 0.0
    else:
        if y1 == y2:
            base = 1.0
        elif abs(y1 - y2) == 1:
            base = 0.5
        else:
            base = 0.0
    # month/day bump
    if m1 and m2 and m1 == m2:
        base += 0.1
    if d1 and d2 and d1 == d2:
        base += 0.1
    return min(base, 1.0)

def text_similarity(a, b):
    if not a or not b:
        return 0.0
    return fuzz.token_set_ratio(str(a), str(b)) / 100.0

def postcode_similarity(a, b):
    if not a or not b:
        return 0.0
    a = str(a); b = str(b)
    if a == b:
        return 1.0
    # prefix match
    common_prefix = 0
    for x, y in zip(a, b):
        if x == y:
            common_prefix += 1
        else:
            break
    return min(common_prefix / max(len(a), len(b)), 0.9)

def gender_similarity(a, b):
    return 1.0 if a and b and a == b and a in ("m","f") else 0.0
