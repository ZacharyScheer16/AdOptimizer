import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def run_clustering(df):
    # 1. Automatic Column Mapping
    mapping = {
        'Spend': ['cost', 'amount', 'spent', 'total_charge', 'price'],
        'Clicks': ['clicks', 'link_clicks', 'interactions', 'taps'],
        'Impressions': ['impressions', 'views', 'reach', 'seen']
    }

    for standard_name, synonyms in mapping.items():
        for col in df.columns:
            if col.lower() in synonyms or any(s in col.lower() for s in synonyms):
                df.rename(columns={col: standard_name}, inplace=True)

    # 2. Check if the required columns exist
    required = ['Spend', 'Clicks', 'Impressions']
    if not all(col in df.columns for col in required):
        return {"error": f"Could not find columns for {required}."}

    # 3. Calculation Logic
    df['CTR'] = (df['Clicks'] / df['Impressions']).fillna(0)
    df['CPC'] = (df['Spend'] / df['Clicks']).replace([np.inf, -np.inf], 0).fillna(0)
    
    # 4. Select Features for AI
    features = ['Spend', 'CTR', 'CPC']    
    numeric_data = df[features].fillna(0)

    # 5. Train the Brain
    kmeans = KMeans(n_clusters=3, random_state=42, n_init='auto')
    kmeans.fit(numeric_data)

    # 6. Make Predictions
    df['ad_group'] = kmeans.labels_

    # Calculatiung global AVG to compare against
    avg_cpc = df['CPC'].mean()
    avg_ctr = df['CTR'].mean()

    # --- NEW: ACCURACY & SUMMARY LOGIC ---
    
    # Calculate the clarity of the groups (Score: -1 to 1) [cite: 2025-10-11]
    accuracy_score = silhouette_score(numeric_data, kmeans.labels_)

    # Calculate the average performance for each group [cite: 2025-10-11]
    # This proves the model actually found different 'types' of ads
    group_summary = df.groupby('ad_group')[['Spend', 'CTR', 'CPC']].mean().to_dict(orient="index")

    # Final response including the score and the data
    return {
        "model_accuracy_score": float(accuracy_score),
        "group_averages": group_summary,
        "detailed_results": df.to_dict(orient="records")
    }