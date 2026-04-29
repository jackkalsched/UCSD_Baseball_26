import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import joblib
import sys
from pathlib import Path
import pandas as pd
from google.cloud import bigquery
import json
from analytics_suite.team_codes import normalize_teams

def update_all_data():
    """
    Fetches the latest dataset from BigQuery and saves it to a static JSON and CSV
    file so that it can be loaded by the front-end web pages.
    """
    print("Initializing BigQuery Client...")
    # NOTE: Ensure you are authenticated with Google Cloud (e.g. via GOOGLE_APPLICATION_CREDENTIALS)
    client = bigquery.Client(project="master-trackman-project")

    query = """
    SELECT *
    FROM `master-trackman-project.master_trackman_dataset.all_games`
    """

    print("Executing query to fetch latest data...")
    df = client.query(query).to_dataframe()
    print(f"Data fetched successfully! Received {len(df)} rows.")

    # Map TrackMan team codes → school names
    for col in ["BatterTeam", "PitcherTeam", "HomeTeam", "AwayTeam"]:
        if col in df.columns:
            df[col] = normalize_teams(df[col])

    # Determine the directory to save the data
    # Saving inside static/data/ so index.html and other pages can fetch it
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "static" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    json_path = data_dir / "all_games.json"
    csv_path = data_dir / "all_games.csv"

    print(f"Saving data to {json_path}...")
    # Convert dates to ISO format so JSON can be parsed easily in JS
    df.to_json(json_path, orient="records", date_format="iso")

    print(f"Saving data to {csv_path}...")
    df.to_csv(csv_path, index=False)

    print("Update complete! The website data has been successfully updated.")

if __name__ == "__main__":
    update_all_data()
