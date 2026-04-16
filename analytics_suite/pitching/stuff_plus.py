import pandas as pd 
import numpy as np 
import sys
import os 
import joblib
from google.cloud import bigquery
from pathlib import Path
import scipy

# Resolve Paths
BASE_DIR = Path(__file__).resolve().parent

VAAA_MODEL_PATH = BASE_DIR / "models" / "vaaaa.pkl"
STUFF_MODEL_PATH = BASE_DIR / "models" / "lgbm_stuff_plus.pkl"

# Add parent directory to sys.path to import run_expectancy
SERVER_DIR = BASE_DIR.parent
sys.path.append(str(SERVER_DIR))

from run_expectancy import generate_base_out_state

def generate_stuff():
    print("Initializing BigQuery Client...")
    client = bigquery.Client(project="master-trackman-project")
    
    # Use the unified all_games dataset updated via backend
    query = """
    SELECT * 
    FROM `master-trackman-project.master_trackman_dataset.all_games`
    """
    
    print("Fetching master trackman dataset from BigQuery...")
    master_trackman = client.query(query).to_dataframe()
    
    master_trackman["Date"] = pd.to_datetime(
        master_trackman["Date"],
        errors="coerce",
        infer_datetime_format=True
    )
    
    print("Generating base out state...")
    baserunners = generate_base_out_state(master_trackman)
    
    ### ---------- ####
    ## DATA CLEANING ##
    ### ---------- ####
    
    print("Cleaning data and computing basic features...")
    feature_cols = ['RelSpeed', 'SpinRate', 'pfxz', 'pfxx', 'InducedVertBreak', 'HorzBreak',
        'RelHeight', 'RelSide', 'Extension', 'VertApprAngle', 'HorzApprAngle']

    # Eliminate invalid or NaN pitches
    baserunners = baserunners[~(
        (baserunners['AutoPitchType'].isna()) | 
        (baserunners['AutoPitchType'] == 'Other') | 
        (baserunners['AutoPitchType'] == 'Knuckleball') | 
        (baserunners['AutoPitchType'] == 'Undefined'))]

    # Impute missing pitch metrics (fills with the mean of that pitcher's other)
    baserunners['Extension'] = baserunners['Extension'].fillna(baserunners.groupby(['Pitcher'])['Extension'].transform('mean'))
    baserunners['SpinRate'] = baserunners['SpinRate'].fillna(baserunners.groupby(['Pitcher', 'AutoPitchType'])['SpinRate'].transform('mean'))
    baserunners['InducedVertBreak'] = baserunners['InducedVertBreak'].fillna(baserunners.groupby(['Pitcher', 'AutoPitchType'])['InducedVertBreak'].transform('mean'))
    baserunners['HorzBreak'] = baserunners['HorzBreak'].fillna(baserunners.groupby(['Pitcher', 'AutoPitchType'])['HorzBreak'].transform('mean'))
    baserunners['RelSpeed'] = baserunners['RelSpeed'].fillna(baserunners.groupby(['Pitcher', 'AutoPitchType'])['RelSpeed'].transform('mean'))
    baserunners['VertApprAngle'] = baserunners['VertApprAngle'].fillna(baserunners.groupby(['Pitcher'])['VertApprAngle'].transform('mean'))
    baserunners['HorzApprAngle'] = baserunners['HorzApprAngle'].fillna(baserunners.groupby(['Pitcher'])['HorzApprAngle'].transform('mean'))
    baserunners['RelHeight'] = baserunners['RelHeight'].fillna(baserunners.groupby(['Pitcher'])['RelHeight'].transform('mean'))
    baserunners['RelSide'] = baserunners['RelSide'].fillna(baserunners.groupby(['Pitcher'])['RelSide'].transform('mean'))

    # Eliminates outlier-ish pitches
    means = baserunners.groupby('AutoPitchType')[feature_cols].transform('mean')
    stds  = baserunners.groupby('AutoPitchType')[feature_cols].transform('std')
    mask = ((baserunners[feature_cols] - means).abs() <= 3 * stds).all(axis=1)
    baserunners = baserunners[mask]

    baserunner_cleaned = baserunners.dropna(subset=feature_cols)

    keep_cols = [
        # ID
        'PitchUID', 'GameUID', 'Date', 'Pitcher', 'PitcherTeam', 'PitchNo', 'PitcherThrows', 'Batter', 'BatterTeam', 
        'BatterId', 'BatterSide', 'AutoPitchType', 'TaggedPitchType',
        
        # Stuff (Inputs)
        'RelSpeed', 'SpinRate', 'InducedVertBreak', 'HorzBreak', 
        'RelHeight', 'RelSide', 'Extension', 'VertApprAngle', 'HorzApprAngle',
        'ax0', 'az0', 'x0', 'z0', 'SpinAxis', 'VertRelAngle', 'HorzRelAngle',
        'pfxz', 'pfxx',
        
        # Context
        'Balls', 'Strikes', 'Outs', 'OutsOnPlay', 'RunsScored',
        'first_base', 'second_base', 'third_base', 'PlateLocSide', 'PlateLocHeight',
        
        # Results
        'PitchCall', 'PlayResult', 'KorBB', 'ExitSpeed', 'Angle',
        
        # Run Value (Target)
        'delta_run_exp'
    ]

    # Create the clean view
    # check if 'delta_run_exp' exists, since sometimes that is dynamically assigned
    if 'delta_run_exp' not in baserunners.columns:
        print("Warning: 'delta_run_exp' not generated, filling with 0 for functionality if omitted...")
        baserunners['delta_run_exp'] = 0.0

    missing = [c for c in keep_cols if c not in baserunners.columns]
    keep_cols_safe = [c for c in keep_cols if c in baserunners.columns]
    
    clean_df = baserunners[keep_cols_safe].copy()

    # Filter out non-competitive or undefined pitches
    if 'PitchCall' in clean_df.columns:
        clean_df = clean_df[~clean_df['PitchCall'].isin(['BallIntentional', 'AutomaticBall', 'Undefined'])].copy()

    # Fix typos in PlayResult
    if 'PlayResult' in clean_df.columns:
        clean_df['PlayResult'] = clean_df['PlayResult'].replace({
            'SIngle': 'Single',
            'FIeldersChoice': 'FieldersChoice'
        })
    
    #### ---------------- #####
    # CALCULATE AVG RUN VALUE #
    #### ---------------- #####

    def map_to_10_buckets(row):
        call = row.get('PitchCall', '')
        result = row.get('PlayResult', '')
        
        ### Batted Ball Events (5 Buckets)
        if call == 'InPlay':
            if result == 'Single':
                return 'Single'
            elif result == 'Double':
                return 'Double'
            elif result == 'Triple':
                return 'Triple'
            elif result == 'HomeRun':
                return 'Home Run'
            # Group all "Out" types into one bucket
            elif result in ['Out', 'FieldersChoice', 'Sacrifice', 'Error']:
                return 'Field Out'
            else:
                return 'Ignore'


        ### Pitch Level Events (5 Buckets)
        if call in ['BallCalled', 'BallinDirt']:
            return 'Ball'
        if call == 'StrikeCalled':
            return 'Called Strike'
        if call == 'StrikeSwinging':
            return 'Swinging Strike'
        if call in ['FoulBall', 'FoulBallNotFieldable', 'FoulBallFieldable']:
            return 'Foul'
        if call == 'HitByPitch':
            return 'Hit By Pitch'
            
        return 'Ignore'

    if 'delta_run_exp' in clean_df.columns:
        clean_df['event_type'] = clean_df.apply(map_to_10_buckets, axis=1)

        # Remove any rows that didn't fit into a bucket
        clean_df = clean_df[clean_df['event_type'] != 'Ignore'].copy()
        
        clean_df['xRV_event'] = clean_df.groupby(['event_type', 'Balls', 'Strikes'])['delta_run_exp'].transform('mean')
    else:
        clean_df['xRV_event'] = 0.0 # fallback
        
    ### ---------------- ####
    ## FEATURE ENGINEERING ##
    ### ---------------- ####

    clean_df['expected_spin_axis'] = (
        np.degrees(
            np.arctan2(clean_df['HorzBreak'], clean_df['InducedVertBreak'])
        ) + 180
    ) % 360

    # Normalize expected_spin_axis to [0, 360) range
    diff = clean_df['SpinAxis'] - clean_df['expected_spin_axis']

    clean_df['SpinAxis_diff'] = (diff + 180) % 360 - 180

    # Mirror handedness
    clean_df['handedness_encode'] = (clean_df['PitcherThrows'] == 'Right').astype(int)

    # Boolean mask for left-handed pitchers
    mask_left = clean_df['handedness_encode'] == 0

    # Columns to mirror (sign flip)
    cols_to_flip = ['HorzBreak', 'ax0', 'pfxx', 'RelSide', 'HorzApprAngle', 'HorzRelAngle']
    clean_df_w_mirrored = clean_df.copy()

    # ensure columns exist
    cols_to_flip_safe = [c for c in cols_to_flip if c in clean_df_w_mirrored.columns]
    if len(cols_to_flip_safe) > 0 and len(clean_df_w_mirrored) > 0:
        clean_df_w_mirrored.loc[mask_left, cols_to_flip_safe] *= -1
    
    # -------------------------------
    # FASTBALL BASELINE CALCULATION
    # -------------------------------
    print("Calculating FASTBALL baselines...")
    
    FASTBALL_TYPES = ['FourSeamFastBall', 'Fastball', 'TwoSeamFastBall', 'Sinker', 'Cutter']

    fb_df = clean_df_w_mirrored[
        clean_df_w_mirrored['TaggedPitchType'].isin(FASTBALL_TYPES)
    ].copy()

    # Count pitches by pitcher & FB type
    fb_counts = (
        fb_df.groupby(['Pitcher', 'TaggedPitchType'])
            .size()
            .reset_index(name='pitch_count')
    )

    # Select dominant fastball per pitcher
    dominant_fb = (
        fb_counts.sort_values(['Pitcher', 'pitch_count'], ascending=[True, False])
                .groupby('Pitcher')
                .head(1)
    )

    # Keep only the dominant FB pitches
    fb_dominant = fb_df.merge(
        dominant_fb[['Pitcher', 'TaggedPitchType']],
        on=['Pitcher', 'TaggedPitchType'],
        how='inner'
    )

    # Compute avg metrics from dominant FB
    avg_fb = (
        fb_dominant
        .groupby('Pitcher')
        .agg(
            avg_speed   = ('RelSpeed', 'mean'),
            avg_vert_az = ('az0', 'mean'),
            avg_horz_ax = ('ax0', 'mean'),
            avg_ivb     = ('InducedVertBreak', 'mean'),
            avb_hb      = ('HorzBreak', 'mean'),
            fb_type     = ('TaggedPitchType', 'first'),
            fb_count    = ('PitchNo', 'count')
        )
        .reset_index()
    )

    # Require minimum FB sample size
    avg_fb = avg_fb[avg_fb['fb_count'] >= 3].copy()

    # Merge back (still inner on Pitcher, but far fewer deletions)
    encoded_avg = clean_df_w_mirrored.merge(
        avg_fb.drop(columns='fb_count'),
        on='Pitcher',
        how='inner'
    )
    encoded_avg['speed_diff'] = encoded_avg['RelSpeed'] - encoded_avg['avg_speed']
    encoded_avg['az0_diff'] = encoded_avg['az0'] - encoded_avg['avg_vert_az']
    encoded_avg['ax0_diff'] = encoded_avg['ax0'] - encoded_avg['avg_horz_ax']
    encoded_avg['IVB_diff'] = encoded_avg['InducedVertBreak'] - encoded_avg['avg_ivb']
    encoded_avg['HB_diff'] = encoded_avg['HorzBreak'] - encoded_avg['avb_hb']
    
    ### VAA ABOVE AVERAGE MODEL ###
    print("Loading VAA Above Average model and calculating...")
    features_vaa = ['RelSpeed', 'VertRelAngle', 'HorzRelAngle', 'RelHeight', 'RelSide', 'Extension']

    model_vaa = joblib.load(VAAA_MODEL_PATH)
    encoded_avg['predicted_vaa'] = model_vaa.predict(encoded_avg[features_vaa])
    encoded_avg['vaaaa'] = encoded_avg['VertApprAngle'] - encoded_avg['predicted_vaa']
    
    ## -------- ##
    # MAIN MODEL #
    ## -------- ##
    print("Loading STUFF+ model and evaluating...")
    
    # Define features
    features_stuff = ['RelSpeed', 
                'SpinRate', 
                'Extension', 
                'HorzBreak', 
                'InducedVertBreak',
                'vaaaa',
                'SpinAxis_diff', 
                'speed_diff', 
                'IVB_diff', 
                'HB_diff'
                ]

    # Define target
    target = 'xRV_event'
    df_all = encoded_avg.dropna(subset=features_stuff + [target])
    
    model_stuff = joblib.load(STUFF_MODEL_PATH)
    df_all['predictedxRV'] = model_stuff.predict(df_all[features_stuff]) * -1
    ## Reverse Left Handed Columns to Original Orientation

    # Boolean mask for left-handed pitchers
    mask_left2 = df_all['handedness_encode'] == 0

    # Flip sign only for left-handers
    if len(cols_to_flip_safe) > 0 and len(df_all) > 0:
        df_all.loc[mask_left2, cols_to_flip_safe] *= -1

    # Reverse SpinAxis transform back to original orientation
    if len(df_all) > 0:
        df_all.loc[mask_left2, 'SpinAxis'] = (360 - df_all.loc[mask_left2, 'SpinAxis']) % 360
    
    ## Calculate Overall Stuff+ and Stuff+ by Pitch Type
    ## All stuff values are centered at 100 with a standard deviation of 10

    # Stuff+ with no prefix is overall Stuff+
    df_all['Stuff+'] = 100 + 10 * ((100 * (df_all['predictedxRV'] - df_all['predictedxRV'].mean())) + (10 * df_all['predictedxRV'].std()))

    # DataFrame to hold stuff+ values
    print("Process complete. Returning DataFrame.")
    stuff_df = df_all.copy()

    return stuff_df

if __name__ == "__main__":
    df_stuff = generate_stuff()
    print("Generated Stuff+ dataset of size:", df_stuff.shape)
