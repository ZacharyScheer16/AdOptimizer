import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def run_clustering(df):
    # 1. Automatic Column Mapping
    # This allows the tool to work with exports from Facebook, Google, etc.
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
        return {"error": f"Could not find columns for {required}. Please check your CSV."}

    # 3. Calculation Logic (Feature Engineering)
    # Adding CTR and CPC helps the AI see 'efficiency' regardless of total spend
    df['CTR'] = (df['Clicks'] / df['Impressions']).fillna(0)
    df['CPC'] = (df['Spend'] / df['Clicks']).replace([np.inf, -np.inf], 0).fillna(0)
    
    # 4. Select Features for AI
    features = ['Spend', 'CTR', 'CPC']    
    numeric_data = df[features].fillna(0)

    # 5. Train the Brain (K-Means)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init='auto')
    kmeans.fit(numeric_data)

    # 6. Make Predictions
    df['ad_group'] = kmeans.labels_

    # 7. Benchmarking (The Yardstick)
    avg_cpc = df['CPC'].mean()
    avg_ctr = df['CTR'].mean()

    # 8. Group Summary & Recommendation Logic
    group_summary = df.groupby('ad_group')[['Spend', 'CTR', 'CPC']].mean().to_dict(orient="index")

    for group_id, stats in group_summary.items():
        # High Efficiency Group
        if stats['CPC'] < avg_cpc and stats['CTR'] >= avg_ctr:
            stats['label'] = "Top Performers"
            stats['status'] = "Scalable"
            stats['recommendation'] = "Increase budget. These ads are highly efficient."
        
        # High Cost (Low Efficiency) Group
        elif stats['CPC'] > avg_cpc * 1.2:
            stats['label'] = "Money Pits"
            stats['status'] = "Risky"
            stats['recommendation'] = "Pause or redesign. Costs are significantly higher than average."
        
        # Average / Stable Group
        else:
            stats['label'] = "Stable / Learning"
            stats['status'] = "Neutral"
            stats['recommendation'] = "Maintain current spend and monitor for 7 more days."

    # 9. Accuracy Logic
    accuracy_score = silhouette_score(numeric_data, kmeans.labels_)

    # Final response including the intelligence report
    return {
        "model_accuracy_score": float(accuracy_score),
        "group_insights": group_summary,
        "detailed_results": df.to_dict(orient="records")
    }

def calculate_savings(results_df,  group_insights):
    risky_ids = [int(gid) for gid, info in group_insights.items() if info["status"] == "Risky"]

    total_waste = results_df[results_df['ad_group'].isin(risky_ids)]['Spend'].sum()
    return total_waste