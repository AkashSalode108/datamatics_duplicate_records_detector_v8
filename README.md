# Historical Person Duplicate Detector

An end-to-end solution to identify probable duplicate person records in messy historical datasets.
It includes:
- A Python library (`src/`) with a clean pipeline (cleaning → blocking → scoring → clustering).
- A Streamlit app (`app.py`) for an interactive UI.
- Unit tests (`tests/`) and sample data.

## Features
- Robust text normalization (Unicode, punctuation, whitespace).
- Fuzzy matching with RapidFuzz (Jaro-Winkler, token set ratio).
- Phonetic encoding with Double Metaphone (via `jellyfish`) to catch typos.
- Flexible blocking strategies to scale to large datasets.
- Rule-based, weighted ensemble scoring (editable in `config/settings.yaml` or via UI).
- Connected components clustering to group duplicates beyond pairwise matches.
- Downloadable results (pairs and clusters).

## Project Structure
```
duplicate_detector/
├── app.py
├── requirements.txt
├── README.md
├── config/
│   └── settings.yaml
├── src/
│   ├── __init__.py
│   ├── utils.py
│   ├── data_cleaning.py
│   ├── blocking.py
│   ├── similarity.py
│   ├── dedupe.py
│   └── evaluation.py
└── tests/
    ├── sample_data.csv
    ├── test_similarity.py
    └── test_pipeline.py
```

## Installation
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the Streamlit app
```bash
streamlit run app.py
```
Then open the provided local URL in your browser.

## How it works
1. **Cleaning**: Normalizes strings, standardizes dates, gender, and codes.
2. **Blocking**: Narrows candidate pairs using one of several strategies.
3. **Similarity**: Computes feature-wise similarity using fuzzy and phonetic methods.
4. **Scoring**: Weighted ensemble → overall pair score.
5. **Clustering**: Builds a graph of duplicate pairs and extracts connected components.
6. **Outputs**: Pairwise predictions and cluster assignments.

## Tests
Run:
```bash
pytest -q
```

## Assumptions
- Input CSV has column names from the prompt (`unique_id`, `first_name`, `surname`, `dob`, `birth_place`, `postcode`, `gender`, `occupation`). Extra columns are ignored.
- Dates may be partial; year-level matches still contribute.
- Postcode granularity varies; exact match or prefix match boosts score.

## Notes
- You can tune thresholds/weights in the UI or `config/settings.yaml` depending on dataset characteristics.
- For very large datasets, consider precomputing blocks and running the scorer in batches.
