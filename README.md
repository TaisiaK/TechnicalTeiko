# TechnicalTeiko

### Requirements
Required software to run in GitHub Codespaces: Python 3, pip, make

### Setup
Install all required Python dependencies by running:
```bash
make setup
```

This installs the packages listed in requirements.txt.

### Run the Data Pipeline

Run:
```bash
make pipeline
```

This executes the data pipeline from start to finish.

The pipeline:

1. Reads cell-count.csv.

2. Creates the SQLite database.

3. Creates the relational database tables.

4. Loads the input data into SQLite.

5. Runs the analysis and statistical calculations.

6. The generated SQLite database is created in the repository root.

### Run the Dashboard

Start the interactive dashboard with:
```bash
make dashboard
```

The dashboard runs on port 8501.

### GitHub Codespaces

After running make dashboard, open the forwarded port 8501 in GitHub Codespaces to access the dashboard.

### Reproducing the Results

To reproduce the complete analysis in a fresh environment:

```bash
make setup
make pipeline
make dashboard
```

Then open the forwarded port 8501 in GitHub Codespaces.

### Statistical Methods

For each immune cell population, responder and non-responder relative frequencies are compared using a two-sided Mann–Whitney U test.

The Mann–Whitney U test was selected because it is a non-parametric test for comparing two independent groups and does not require the relative-frequency data to follow a normal distribution.

P-values are adjusted using the Benjamini–Hochberg false discovery rate procedure to account for testing multiple cell populations.

A corrected p-value below 0.05 is considered statistically significant.

### Dashboard Link

After launching the dashboard with:
```bash
make dashboard
```

the dashboard is available through the forwarded Codespaces port:

Port: 8501


Dashboard: http://localhost:8501
