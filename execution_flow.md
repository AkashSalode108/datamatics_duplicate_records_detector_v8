🔄 Full Execution Flow
1. app.py (Streamlit Frontend Entry)

This is the user-facing API/UI entrypoint.

st.set_page_config(page_title="Historical Person Duplicate Detector", layout="wide")
st.title("🕰️ Historical Person Duplicate Detector")


Configures the Streamlit web app.

Sets title.

with st.sidebar:
    uploaded_cfg = st.file_uploader("Optional: custom YAML config", type=["yaml","yml"])


Sidebar allows uploading of a YAML config (for weights & thresholds).

cfg_obj = DetectorConfig.from_yaml("config/settings.yaml")


Loads default configuration (weights for name/dob similarity, threshold for duplicates).

cfg_obj.pair_score_threshold = st.slider("Pair score threshold", 0.5, 0.99, cfg_obj.pair_score_threshold, 0.01)


User adjusts threshold interactively → determines how strict duplicate detection is.

uploaded = st.file_uploader("Upload CSV", type=["csv"])


Uploads the historical dataset CSV.

if uploaded:
    df = pd.read_csv(uploaded)
    det = DuplicateDetector(cfg_obj)
    pairs, clusters = det.run(df)
    st.dataframe(pairs)
    st.dataframe(clusters)


Loads dataset → initializes DuplicateDetector with config.

Runs pipeline → gets duplicate pairs + clusters.

Displays tables in UI.

2. DuplicateDetector (src/dedupe.py)

This is the core orchestrator.

class DuplicateDetector:
    def run(self, df_raw):
        pairs = self.predict_pairs(df_raw)
        clusters = self.cluster(df_raw, pairs)
        return pairs, clusters

Step 2.1: predict_pairs
df = clean_dataframe(df_raw)
pairs = self.candidate_pairs(df)


Cleaning: normalize names, parse dates, map gender, standardize text.

Blocking: group records into smaller comparison sets.

for i, j in pairs:
    s, feats = self.score_pair(df.loc[i], df.loc[j])
    pred = int(s >= self.cfg.pair_score_threshold)
    rows.append({...})


For each candidate pair:

score_pair → calculate similarity across features (name, dob, postcode, birthplace, gender, occupation).

Weighted score computed from config.

Compare with threshold → mark as duplicate (1) or not (0).

Collect into results table.

Step 2.2: cluster
G = nx.Graph()
G.add_nodes_from(ids)
for _, r in pairs_df[pairs_df["is_duplicate"] == 1].iterrows():
    G.add_edge(r["id1"], r["id2"])


Build a graph:

Nodes = person records.

Edges = predicted duplicate pairs.

Connected components = clusters (groups of duplicates).

3. Cleaning (src/data_cleaning.py)

Standardizes messy data before similarity comparison.

out["first_name_clean"] = out["first_name"].apply(normalize_name)


normalize_name → lowercase, strip punctuation, collapse spaces.

dob_parts = out["dob"].apply(parse_date_safe)
out["dob_year"] = dob_parts.apply(lambda t: t[0])


parse_date_safe → handles 14/03/1875, 1875-03-14, etc.

Extracts year, month, day safely.

out["gender_clean"] = out["gender"].map({"m":"m","male":"m","f":"f","female":"f"}).fillna("u")


Standardizes gender into m, f, u.

Other cleaning:

Remove special characters from birth_place, occupation.

Normalize postcode format (strip spaces, uppercase).

4. Blocking (src/blocking.py)

Avoids comparing every record with every record (which is O(N²)).

surname_key = df["surname_clean"].apply(lambda x: metaphone(x))
year_key = df["dob_year"]
return surname_key + "|" + year_key


Uses phonetic encoding (Metaphone) on surname → groups by sound, not spelling.

Combines with year of birth.

Only compare records inside the same block.

Example:

“Smith”, 1875 → block: "SM0|1875"

“Smyth”, 1875 → block: "SM0|1875"
👉 They end up in the same block, so we compare them.

5. Similarity Functions (src/similarity.py)
Name Similarity
jw = JaroWinkler.similarity("john", "jon")/100
ts = fuzz.token_set_ratio("john smith", "jon smyth")/100
phonetic = 1.0 if metaphone(sn1)==metaphone(sn2) else 0.0
return max(jw, ts) + 0.1*phonetic


Jaro-Winkler: measures typo similarity.

Fuzzy Token Set Ratio: handles swapped/missing tokens.

Phonetic match adds small boost.

DOB Similarity
if years equal → 1.0
if year diff = 1 → 0.5
bonus if month/day also match

Postcode Similarity
if exact match → 1.0
else → fraction of common prefix

Birthplace & Occupation

Use fuzzy string matching.

Normalize casing, remove punctuation.

6. Scoring & Decision
score = w1*name_sim + w2*dob_sim + w3*postcode_sim + ...
if score >= threshold → duplicate


Weighted average using config values.

Threshold determines strictness:

High threshold (0.9): only very strong matches.

Low threshold (0.6): more matches, but risk of false positives.

7. Clustering (src/dedupe.py)

After duplicate pairs are found:

Build graph of duplicates.

Apply connected components to group.

Example:

(1,2) duplicate

(2,3) duplicate

→ cluster = {1,2,3}

8. Tests (tests/)

test_similarity.py: check each similarity metric.

test_pipeline.py: run full pipeline on sample dataset, assert known duplicates are caught.

⚡ Example Run

Dataset:

1: John Smith, 14/03/1875, London, M
2: Jon Smyth, 14-03-1875, London, Male
3: Jane Doe, 02/01/1880, York, F
4: Jaine Do, 1880-01-02, York, Female


Flow:

Cleaning → normalize names (“john”, “jon”), parse DOB, standardize gender.

Blocking → (“Smith/Smyth”, 1875), (“Doe/Do”, 1880).

Similarity:

(1,2): Name 0.9, DOB 1.0, Birthplace 1.0 → Score = 0.95 ✅ Duplicate

(3,4): Name 0.88, DOB 1.0, Birthplace 1.0 → Score = 0.93 ✅ Duplicate

Graph → Clusters: [1,2], [3,4].

✅ So the pipeline = Upload → Cleaning → Blocking → Similarity → Scoring → Duplicate Pairs → Clustering → Display.