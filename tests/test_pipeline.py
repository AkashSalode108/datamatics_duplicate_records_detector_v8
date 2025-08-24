# tests/test_pipeline_full.py
import pandas as pd
from src.dedupe import DuplicateDetector, DetectorConfig

def test_end_to_end_full_dataset():
    # Load the full historical dataset
    df = pd.read_csv("tests/historical.csv")

    # Load config from settings.yaml
    cfg = DetectorConfig.from_yaml("config/settings.yaml")
    det = DuplicateDetector(cfg)

    # Run detection
    pairs, clusters = det.run(df)

    # Basic sanity checks
    assert not pairs.empty, "Pairs dataframe should not be empty"
    assert "is_duplicate" in pairs.columns, "Pairs must have 'is_duplicate' column"
    assert not clusters.empty, "Clusters dataframe should not be empty"
    assert "cluster_id" in clusters.columns, "Clusters must have 'cluster_id' column"

    # If ground truth labels exist in dataset
    if "duplicate_group" in df.columns:
        truth_pairs = set()
        for _, group in df.groupby("duplicate_group"):
            ids = group["id"].astype(str).tolist()
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    truth_pairs.add(tuple(sorted((ids[i], ids[j]))))

        predicted_pairs = set(
            tuple(sorted((str(r.id1), str(r.id2))))
            for _, r in pairs[pairs.is_duplicate == 1].iterrows()
        )

        missing = truth_pairs - predicted_pairs
        extra = predicted_pairs - truth_pairs

        # Check recall (found most true dups)
        recall = 1 - len(missing) / max(1, len(truth_pairs))
        assert recall > 0.8, f"Low recall: {recall:.2f}, missing {len(missing)} pairs"

        # Optional: also check precision (few false positives)
        if truth_pairs:
            precision = 1 - len(extra) / max(1, len(predicted_pairs))
            assert precision > 0.5, f"Low precision: {precision:.2f}, extra {len(extra)} pairs"
    else:
        # If no labels exist → just check non-trivial number of dups
        dup_count = pairs[pairs.is_duplicate == 1].shape[0]
        assert dup_count > 10, f"Too few duplicates found: {dup_count}"
