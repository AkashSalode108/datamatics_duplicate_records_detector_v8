\
import pandas as pd

def evaluate_with_truth(pairs_df: pd.DataFrame, truth_pairs: pd.DataFrame) -> dict:
    """
    Evaluate precision/recall/F1 given a ground-truth dataframe of duplicate pairs.
    truth_pairs: columns ["id1","id2"] (order-insensitive)
    """
    def canon(a,b): 
        return tuple(sorted((str(a), str(b))))
    truth = set(truth_pairs.apply(lambda r: canon(r["id1"], r["id2"]), axis=1))
    preds = set(pairs_df[pairs_df["is_duplicate"]==1].apply(lambda r: canon(r["id1"], r["id2"]), axis=1))
    tp = len(truth & preds)
    fp = len(preds - truth)
    fn = len(truth - preds)
    prec = tp / (tp + fp) if tp + fp > 0 else 0.0
    rec = tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = 2*prec*rec/(prec+rec) if prec+rec>0 else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(prec,3), "recall": round(rec,3), "f1": round(f1,3)}
