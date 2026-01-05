import pandas as pd
import numpy as np
from sklearn.cluster import KMeans


def run_clustering(df):
    numeric_data = df.select_dtypes(include=['number']).fillna(0)


    # 2. Define the Brain (With your fixed random state!)
    # n_init='auto' is also good to add to avoid a warning in newer versions
    kmeans = KMeans(n_clusters=3, random_state=42, n_init='auto')

    #3. Train the Brain
    kmeans.fit(numeric_data)

    #4. Make Predictions
    df['ad_group'] = kmeans.labels_

    #5. Return the Data with Predictions
    return df.to_dict(orient="records")