import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
from analysis import (
    make_overview,
    get_mel_miraclib_data,
    make_subject_level_data,
    run_statistical_tests,
    get_subset_analysis,
    get_avg_baseline_b_cells,
)

DB_FILE = "loblaw-database.db"

# PAGE CONFIGURATION 
st.set_page_config(
    page_title="Loblaw Bio - Miraclib Analysis",
    layout="wide",
)

# LOAD DATA
@st.cache_data
def load_analysis_data():
    with sqlite3.connect(DB_FILE) as connection:
        overview = make_overview(connection)
        p3_raw = get_mel_miraclib_data(connection)
        p3_subject = make_subject_level_data(p3_raw)
        statistics = run_statistical_tests(p3_subject)
        baseline = get_subset_analysis(connection)
        avg_baseline_b_cell = get_avg_baseline_b_cells(connection)
    return (
        overview,
        p3_raw,
        p3_subject,
        statistics,
        baseline,
        avg_baseline_b_cell,
    )

(overview, p3_raw, p3_subject, statistics, baseline, avg_baseline_b_cell,) = load_analysis_data()


# TITLE
st.title("Clinical Trial Dashboard")

# PART 2
st.header("Part 2 — Cell Population Frequencies")
st.markdown("""
    Relative frequency of each immune cell population within each sample.
    The percentage is calculated using the total cell count for that sample.
    """)

# Filters
col1, col2 = st.columns(2)
with col1:
    selected_sample = st.selectbox("Sample",["All"] + sorted(overview["sample"].unique()))
with col2:
    selected_population = st.selectbox("Population", ["All"] + sorted(overview["population"].unique()))
overview_filtered = overview.copy()

if selected_sample != "All":
    overview_filtered = overview_filtered[overview_filtered["sample"] == selected_sample]

if selected_population != "All":
    overview_filtered = overview_filtered[overview_filtered["population"] == selected_population]


st.dataframe(overview_filtered, use_container_width=True, hide_index=True,)

# PART 3
st.header("Part 3 — Miraclib Response Analysis")

st.markdown("""
    Comparison of immune cell population relative frequencies between
    miraclib responders and non-responders in melanoma PBMC samples.
    Because each subject contributes three longitudinal PBMC samples (days 0, 7, and 14), 
    treating samples as independent would result in pseudoreplication. 
    Therefore each subject's three measurements were averaged for each immune-cell population 
    before comparing responders and non-responders. 
    """)

# Interactive population selector
selected_population_p3 = st.selectbox("Select cell population",
    ["All"] + sorted(p3_subject["population"].unique()),
    key="p3_population",
)

plot_data = p3_subject.copy()
if selected_population_p3 != "All":
    plot_data = plot_data[plot_data["population"] == selected_population_p3]

# BOX PLOT
fig = px.box(
    plot_data,
    x="population",
    y="mean_percentage",
    color="response",
    points="all",
    hover_data=["subject"],
    category_orders={"response": ["yes", "no"]},
    labels={
        "population": "Cell Population",
        "mean_percentage": "Relative Frequency (%)",
        "response": "Response",
    },
    title="Relative Cell Population Frequency by Treatment Response",
)

fig.update_layout(legend_title_text="Response",)

st.plotly_chart(fig, use_container_width=True,)

# STATISTICAL RESULTS
st.subheader("Statistical Tests")
stats_filtered = statistics.copy()
if selected_population_p3 != "All":
    stats_filtered = stats_filtered[stats_filtered["population"] == selected_population_p3]

st.dataframe(stats_filtered, use_container_width=True, hide_index=True,)

# SIGNIFICANT RESULTS
st.subheader("Significant Differences")
significant = stats_filtered[stats_filtered["significant"] == True]
if significant.empty:
    st.info(
        "No statistically significant differences were detected "
        "after multiple-testing correction."
    )
else:
    st.dataframe(significant, use_container_width=True, hide_index=True,)

# PART 4
st.header("Part 4 — Baseline Subset Analysis")
st.markdown("""
    Melanoma PBMC samples collected at baseline
    (time_from_treatment_start = 0) from patients treated with miraclib.
    """
)

# BASELINE SAMPLE TABLE
st.subheader("Baseline Samples")
st.dataframe(baseline, use_container_width=True, hide_index=True,)

# SAMPLES PER PROJECT
st.subheader("Samples per Project")
samples_per_project = (baseline.groupby("project").size().reset_index(name="sample_count"))
st.dataframe(
    samples_per_project, use_container_width=True, hide_index=True,)

# RESPONDERS / NON-RESPONDERS
st.subheader("Subjects by Treatment Response")
response_counts = (baseline.drop_duplicates("subject").groupby("response").size().reset_index(name="subject_count"))
st.dataframe(response_counts, use_container_width=True, hide_index=True,)

# MALE / FEMALE
st.subheader("Subjects by Sex")
sex_counts = (baseline.drop_duplicates("subject").groupby("sex").size().reset_index(name="subject_count"))
st.dataframe(sex_counts, use_container_width=True, hide_index=True,)