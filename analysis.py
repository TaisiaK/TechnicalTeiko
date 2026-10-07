import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt 
from scipy.stats import mannwhitneyu
from statsmodels.stats.multitest import multipletests
from pathlib import Path

DB_FILE = "loblaw-database.db"
OUTPUT_DR = Path("outputs")

#Part 2: Data Overview
def make_overview(connection):
    connection.execute("""DROP VIEW IF EXISTS relative_frequency;""")
    connection.execute("""
        CREATE VIEW relative_frequency AS
                SELECT 
                    c.sample_id AS sample, t.total_count, c.population, c.count, 
                    100.0 * c.count / t.total_count AS percentage
                FROM cell_counts AS c
                JOIN(
                    SELECT sample_id, SUM(count) AS total_count
                    FROM cell_counts
                    GROUP BY sample_id
                ) AS t USING (sample_id); 
    """)
    query = """
        SELECT *
        FROM relative_frequency
        ORDER BY sample, population
    """
    return pd.read_sql_query(query, connection)

#Part 3: Statistical Analysis
def get_mel_miraclib_data(connection):
    #PBMC samples from melanoma patients receiving miraclib and response
    query = """
        SELECT f.sample, sa.subject_id AS subject, f.population, f.percentage, su.response
        FROM relative_frequency f
        JOIN samples AS sa ON sa.sample_id = f.sample
        JOIN subjects AS su USING(subject_id)
        WHERE su.condition = 'melanoma' AND su.treatment = 'miraclib' AND sa.sample_type = 'PBMC'
        ORDER BY f.population, su.response, f.sample
    """
    return pd.read_sql_query(query, connection)

def make_subject_level_data(data):
    subject_level = (data.groupby(["subject", "population", "response"], as_index=False)
                     ["percentage"].mean().rename(columns={"percentage": "mean_percentage"}))
    return subject_level

def creating_box_plots(data):
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(
        data=data,
        x="population",
        y="mean_percentage",
        hue="response",
        ax=ax
    )
    ax.set_xlabel("Cell Population")
    ax.set_ylabel("Relative Frequency (%)")
    ax.set_title("Cell Population Frequency by Response to Miraclib Treatment")
    fig.tight_layout()
    return fig

def run_statistical_tests(subject_level_data):
    results = []
    for population in sorted(subject_level_data["population"].unique()):
        population_data = subject_level_data[subject_level_data["population"] == population]
        responders = population_data[population_data["response"].str.lower() == "yes"]["mean_percentage"]
        non_responders = population_data[population_data["response"].str.lower() == "no"]["mean_percentage"]
        if len(responders) == 0 or len(non_responders) == 0:
            continue
        statistic, p_value = mannwhitneyu(responders, non_responders, alternative="two-sided")
        results.append({
            "population": population,
            "n_responders": len(responders),
            "n_non_responders": len(non_responders),
            "responder_median": responders.median(),
            "non_responder_median": non_responders.median(),
            "U_statistic": statistic,
            "p_value": p_value,
        })
    results_df = pd.DataFrame(results)
    if not results_df.empty:
        results_df["adjusted_p_value"] = multipletests(results_df["p_value"],method="fdr_bh")[1]
        results_df["significant"] = (results_df["adjusted_p_value"] < 0.05)
    return results_df

#Part 4: Data Subset Analysis
def get_subset_analysis(connection):
    #all melanoma PBMC samples at baseline from patients treated with miraclib
    #sample_id, response, sex
    query = """
        SELECT su.project, su.subject_id AS subject, sa.sample_id AS samples,
            su.response, su.sex
        FROM samples AS sa
        JOIN subjects AS su USING (subject_id)
        WHERE su.condition = 'melanoma' AND su.treatment = 'miraclib' 
        AND sa.sample_type = 'PBMC' AND sa.time_from_treatment_start = 0;
    """
    return pd.read_sql_query(query, connection)

#Google form question
def get_avg_baseline_b_cells(connection):
        query = """
            SELECT 
                AVG(c.count)
            FROM samples AS sa 
            JOIN subjects AS su USING (subject_id)
            JOIN cell_counts AS c USING (sample_id)
            WHERE su.condition = 'melanoma' AND sa.time_from_treatment_start = 0 
            AND c.population = 'b_cell' AND su.sex='M' AND su.response='yes';
        """
        answer = connection.execute(query).fetchone()[0]
        return answer

def main(): 
    OUTPUT_DR.mkdir(exist_ok=True)
    with sqlite3.connect(DB_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON") 
        # Part 2
        overview = make_overview(connection)
        # Part 3
        p3_raw_data = get_mel_miraclib_data(connection)
        p3_subject_data = make_subject_level_data(p3_raw_data)
        p3_stats = run_statistical_tests(p3_subject_data)
        fig = creating_box_plots(p3_subject_data)
        fig.savefig(OUTPUT_DR / "response_boxplots.png", dpi=300)
        plt.close(fig)
        # Part 4
        subset_data = get_subset_analysis(connection)

if __name__ == "__main__":
    main()