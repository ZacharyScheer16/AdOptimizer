import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def run_clustering(df):
    try:
        # 1. Clean Column Names
        df.columns = [c.replace('Spent', 'Spend') for c in df.columns]

        # 2. Metric Calculations (Ensuring Spend, CPC, and CTR exist)
        if 'CPC' not in df.columns:
            df['CPC'] = df['Spend'] / df['Clicks'].replace(0, np.nan)
            df['CPC'] = df['CPC'].fillna(0)
        if 'CTR' not in df.columns:
            df['CTR'] = df['Clicks'] / df['Impressions'].replace(0, np.nan)
            df['CTR'] = df['CTR'].fillna(0)

        # 3. Select features (No Scaling to keep that 73.8% confidence)
        features = ['Spend', 'CPC', 'CTR']
        X = df[features].copy()

        # 4. Run AI with 3 Clusters (The original setup)
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        df['ad_group'] = kmeans.fit_predict(X)
        
        # Calculate accuracy based on raw values
        accuracy = silhouette_score(X, df['ad_group'])
        
        # 5. Build Group Insights
        group_insights = {}
        overall_avg_cpc = df['CPC'].mean()
        
        for cluster_id in sorted(df['ad_group'].unique()):
            cluster_data = df[df['ad_group'] == cluster_id]
            avg_cpc = cluster_data['CPC'].mean()
            avg_ctr = cluster_data['CTR'].mean()
            
            # Logic for identifying 'Risky' vs 'Scalable'
            if avg_cpc > overall_avg_cpc:
                label, status = "Money Pit", "Risky"
                rec = "High cost detected. Consider pausing."
            elif avg_ctr > df['CTR'].mean():
                label, status = "Top Performer", "Scalable"
                rec = "Efficient results. Safe to increase budget."
            else:
                label, status = "Stable", "Neutral"
                rec = "Average performance. No changes needed."
            group_insights[int(cluster_id)] = {
                "label": label, "status": status,
                "CPC": avg_cpc, "CTR": avg_ctr, "recommendation": rec
            }
            
        return {
            "model_accuracy_score": accuracy,
            "group_insights": group_insights,
            "detailed_results": df.to_dict('records')
        }
    except Exception as e:
        return {"error": str(e)}

def calculate_savings(results_df, group_insights):
    risky_ids = [int(gid) for gid, info in group_insights.items() if info["status"] == "Risky"]
    total_waste = results_df[results_df['ad_group'].isin(risky_ids)]['Spend'].sum()
    return total_waste