\
import streamlit as st
import pandas as pd
import yaml
from io import BytesIO

from src.dedupe import DuplicateDetector, DetectorConfig
from src.data_cleaning import clean_dataframe

st.set_page_config(page_title="Duplicate Records Detector", layout="wide")

st.title("🕰️ Duplicate Records Detector")
st.write("Upload a CSV of person records and find probable duplicates.")

with st.sidebar:
    st.header("⚙️ Settings")
    uploaded_cfg = st.file_uploader("Optional: custom YAML config", type=["yaml","yml"])
    if uploaded_cfg is not None:
        cfg = yaml.safe_load(uploaded_cfg)
        cfg_obj = DetectorConfig(
            pair_score_threshold = cfg.get("thresholds", {}).get("pair_score", 0.78),
            weights = cfg.get("weights", {}),
            blocking_strategy = cfg.get("blocking", {}).get("strategy","first_surname_metaphone_year"),
            postcode_prefix_len = cfg.get("blocking", {}).get("postcode_prefix_len", 3),
        )
    else:
        cfg_obj = DetectorConfig.from_yaml("config/settings.yaml")

    # Allow live tuning
    st.subheader("Thresholds & Weights")
    cfg_obj.pair_score_threshold = st.slider("Pair score threshold", 0.5, 0.99, cfg_obj.pair_score_threshold, 0.01)
    w_name = st.slider("Weight: name", 0.0, 1.0, float(cfg_obj.weights.get("name",0.45)), 0.01)
    w_dob = st.slider("Weight: dob", 0.0, 1.0, float(cfg_obj.weights.get("dob",0.2)), 0.01)
    w_birth = st.slider("Weight: birthplace", 0.0, 1.0, float(cfg_obj.weights.get("birthplace",0.1)), 0.01)
    w_post = st.slider("Weight: postcode", 0.0, 1.0, float(cfg_obj.weights.get("postcode",0.1)), 0.01)
    w_gender = st.slider("Weight: gender", 0.0, 1.0, float(cfg_obj.weights.get("gender",0.05)), 0.01)
    w_occ = st.slider("Weight: occupation", 0.0, 1.0, float(cfg_obj.weights.get("occupation",0.1)), 0.01)
    cfg_obj.weights = {"name":w_name,"dob":w_dob,"birthplace":w_birth,"postcode":w_post,"gender":w_gender,"occupation":w_occ}

    st.subheader("Blocking")
    cfg_obj.blocking_strategy = st.selectbox("Strategy", ["surname_metaphone_year", "postcode_prefix_year", "first_initial_year", "first_surname_metaphone_year"], index=["surname_metaphone_year", "postcode_prefix_year", "first_initial_year", "first_surname_metaphone_year"].index(cfg_obj.blocking_strategy))
    cfg_obj.postcode_prefix_len = st.number_input("Postcode prefix length", min_value=1, max_value=10, value=int(cfg_obj.postcode_prefix_len))

uploaded = st.file_uploader("Upload CSV", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)
    st.write("### Preview", df.head())
    det = DuplicateDetector(cfg_obj)

    if st.button("Run detection"):
        with st.spinner("Processing..."):
            pairs, clusters = det.run(df)

        st.success(f"Done! Found {clusters['cluster_id'].nunique()} clusters across {len(df)} records.")
        st.subheader("Predicted duplicate pairs")
        st.dataframe(pairs, use_container_width=True)
        st.subheader("Clusters")
        st.dataframe(clusters, use_container_width=True)

        # Downloads
        def to_csv_bytes(df):
            buf = BytesIO()
            df.to_csv(buf, index=False)
            buf.seek(0)
            return buf

        st.download_button("Download pairs CSV", data=to_csv_bytes(pairs), file_name="predicted_pairs.csv", mime="text/csv")
        st.download_button("Download clusters CSV", data=to_csv_bytes(clusters), file_name="clusters.csv", mime="text/csv")

    with st.expander("Cleaned data (debug)"):
        st.dataframe(clean_dataframe(df).head(20), use_container_width=True)

else:
    st.info("Please upload a CSV to begin.")
