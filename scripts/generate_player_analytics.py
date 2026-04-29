import json
import os
import sys
from pathlib import Path
from google.cloud import bigquery
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analytics_suite.team_codes import get_team_name

# Set your project id
PROJECT_ID = "master-trackman-project"

def get_bq_client():
    try:
        return bigquery.Client(project=PROJECT_ID)
    except Exception as e:
        print(f"Error initializing BigQuery client: {e}")
        return None

def fetch_hitter_data(client):
    # This query retrieves pitch-level data from 2025 and 2026.
    # Note: If `xwOBA` or `SLG_Value` do not exist in your tables, you may need to 
    # either calculate them within the query using CASE statements based on PlayResult, 
    # or rely on frontend estimation.
    query = """
    WITH raw_data AS (
        SELECT
            Batter,
            BatterTeam,
            PitcherTeam,
            GameDate,
            PitcherThrows,
            TaggedPitchType as PitchType,
            Balls,
            Strikes,
            PlateLocHeight,
            PlateLocSide,
            PlayResult,
            KorBB,
            ExitSpeed,
            Angle
        FROM `master-trackman-project.master_trackman_dataset.2025_data`
        UNION ALL
        SELECT
            Batter,
            BatterTeam,
            PitcherTeam,
            GameDate,
            PitcherThrows,
            TaggedPitchType as PitchType,
            Balls,
            Strikes,
            PlateLocHeight,
            PlateLocSide,
            PlayResult,
            KorBB,
            ExitSpeed,
            Angle
        FROM `master-trackman-project.master_trackman_dataset.2026_data`
    )
    SELECT * FROM raw_data
    WHERE Batter IS NOT NULL
    ORDER BY Batter, GameDate
    """
    
    print("Executing BigQuery...")
    try:
        query_job = client.query(query)
        results = query_job.result()
        return results
    except Exception as e:
        print(f"Error running query. Please verify column names (like ExitSpeed or PlayResult) exist. Error: {e}")
        return []

def process_and_save_data(rows):
    # Group data by Batter
    batters = defaultdict(list)
    
    for row in rows:
        batter_name = str(row.Batter).strip()
        if not batter_name:
            continue
            
        gamedate = str(row.GameDate) if row.GameDate else None
        
        # We create a dictionary per pitch for the frontend
        pitch_data = {
            "GameDate": gamedate,
            "Opponent": get_team_name(row.PitcherTeam) if row.PitcherTeam else None,
            "PitcherHand": row.PitcherThrows,
            "PitchType": row.PitchType,
            "Balls": row.Balls,
            "Strikes": row.Strikes,
            "PlateLocHeight": row.PlateLocHeight,
            "PlateLocSide": row.PlateLocSide,
            "PlayResult": row.PlayResult,
            "KorBB": row.KorBB,
            "ExitSpeed": row.ExitSpeed,
            "Angle": row.Angle,
        }
        batters[batter_name].append(pitch_data)
        
    print(f"Found {len(batters)} batters. Saving JSON files...")
    
    # Save a JSON file for each batter
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "hitters")
    os.makedirs(output_dir, exist_ok=True)
    
    count = 0
    for batter_name, pitches in batters.items():
        # Sanitize filename
        safe_name = "".join([c for c in batter_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        filepath = os.path.join(output_dir, f"{safe_name}.json")
        
        with open(filepath, 'w') as f:
            json.dump({
                "batter": batter_name,
                "pitches": pitches
            }, f)
        count += 1
        
    print(f"Successfully wrote {count} JSON files to {output_dir}")

def main():
    client = get_bq_client()
    if not client:
        print("Could not connect to GCP. Make sure GOOGLE_APPLICATION_CREDENTIALS is set.")
        return
        
    rows = fetch_hitter_data(client)
    if rows:
        process_and_save_data(rows)

if __name__ == "__main__":
    main()
