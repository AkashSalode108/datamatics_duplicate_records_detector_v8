\
from dataclasses import dataclass
from typing import Dict, Tuple, List
import yaml
import pandas as pd
import numpy as np
import itertools
import networkx as nx

from .data_cleaning import clean_dataframe
from .blocking import apply_blocking
from .similarity import name_similarity, dob_similarity, text_similarity, postcode_similarity, gender_similarity

@dataclass
class DetectorConfig:
    pair_score_threshold: float = 0.78
    weights: Dict[str, float] = None
    blocking_strategy: str = "surname_metaphone_year"
    postcode_prefix_len: int = 3

    @staticmethod
    def from_yaml(path: str) -> "DetectorConfig":
        with open(path, "r") as f:
            cfg = yaml.safe_load(f)
        return DetectorConfig(
            pair_score_threshold = cfg.get("thresholds", {}).get("pair_score", 0.78),
            weights = cfg.get("weights", {
                "name": 0.45, "dob": 0.2, "birthplace": 0.1, "postcode": 0.1, "gender": 0.05, "occupation": 0.1
            }),
            blocking_strategy = cfg.get("blocking", {}).get("strategy", "surname_metaphone_year"),
            postcode_prefix_len = cfg.get("blocking", {}).get("postcode_prefix_len", 3),
        )

class DuplicateDetector:
    def __init__(self, config: DetectorConfig):
        self.cfg = config

    def score_pair(self, r1: pd.Series, r2: pd.Series) -> Tuple[float, Dict[str,float]]:
        feats = {}
        feats["name"] = name_similarity(r1["first_name_clean"], r1["surname_clean"],
                                        r2["first_name_clean"], r2["surname_clean"])
        feats["dob"] = dob_similarity(r1["dob_year"], r1["dob_month"], r1["dob_day"],
                                      r2["dob_year"], r2["dob_month"], r2["dob_day"])
        feats["birthplace"] = text_similarity(r1["birth_place_clean"], r2["birth_place_clean"])
        feats["postcode"] = postcode_similarity(r1["postcode_clean"], r2["postcode_clean"])
        feats["gender"] = gender_similarity(r1["gender_clean"], r2["gender_clean"])
        feats["occupation"] = text_similarity(r1["occupation_clean"], r2["occupation_clean"])

        score = 0.0
        for k, w in self.cfg.weights.items():
            score += w * feats.get(k, 0.0)
        return score, feats

    def candidate_pairs(self, df: pd.DataFrame) -> List[Tuple[int, int]]:
        blocks = apply_blocking(df, self.cfg.blocking_strategy, self.cfg.postcode_prefix_len)
        df = df.copy()
        df["_block_key"] = blocks
        pairs = []
        for _, g in df.groupby("_block_key"):
            idxs = list(g.index)
            if len(idxs) > 1:
                pairs.extend(list(itertools.combinations(idxs, 2)))
        return pairs

    def predict_pairs(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        df = clean_dataframe(df_raw)
        pairs = self.candidate_pairs(df)
        rows = []
        for i, j in pairs:
            s, feats = self.score_pair(df.loc[i], df.loc[j])
            pred = int(s >= self.cfg.pair_score_threshold)
            rows.append({
                "id1": df.loc[i, "unique_id"], "id2": df.loc[j, "unique_id"],
                "score": s, **{f"feat_{k}": v for k, v in feats.items()}, "is_duplicate": pred
            })
        out = pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)
        return out

    def cluster(self, df_raw: pd.DataFrame, pairs_df: pd.DataFrame) -> pd.DataFrame:
        G = nx.Graph()
        # add nodes
        ids = df_raw["unique_id"].astype(str).tolist()
        G.add_nodes_from(ids)
        # add edges for predicted duplicate pairs
        for _, r in pairs_df[pairs_df["is_duplicate"] == 1].iterrows():
            G.add_edge(str(r["id1"]), str(r["id2"]), weight=float(r["score"]))
        clusters = []
        for cid, comp in enumerate(nx.connected_components(G), start=1):
            members = sorted(list(comp))
            for m in members:
                clusters.append({"unique_id": m, "cluster_id": cid, "cluster_size": len(members)})
        return pd.DataFrame(clusters).sort_values(["cluster_size","cluster_id"], ascending=[False,True])

    def run(self, df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        pairs = self.predict_pairs(df_raw)
        clusters = self.cluster(df_raw, pairs)
        return pairs, clusters
