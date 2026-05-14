from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import pandas as pd
import io
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

app = FastAPI(title="Customer Segmentation API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process")
async def process_data(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    try:
        # Read CSV data
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        if df.empty:
            raise HTTPException(status_code=400, detail="The CSV file is empty.")

        # Basic Stats
        total_customers = len(df)
        
        # Handle Churn
        churn_rate = 0
        if 'Churn' in df.columns:
            churn_count = df['Churn'].apply(lambda x: 1 if str(x).strip().lower() in ['yes', '1', 'true'] else 0).sum()
            churn_rate = (churn_count / total_customers) * 100

        avg_tenure = df['tenure'].mean() if 'tenure' in df.columns else 0
        avg_monthly_charges = df['MonthlyCharges'].mean() if 'MonthlyCharges' in df.columns else 0

        # AI Segmentation (K-Means Clustering)
        # We'll use tenure and MonthlyCharges for clustering
        segments = {
            'Champions (High Value)': 0,
            'Loyalists': 0,
            'New Customers': 0,
            'At Risk (Churned)': 0
        }

        if 'tenure' in df.columns and 'MonthlyCharges' in df.columns:
            # Prepare data for clustering
            X = df[['tenure', 'MonthlyCharges']].dropna()
            
            if len(X) > 4: # Need enough samples for 4 clusters
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                
                kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
                df['Cluster'] = kmeans.fit_predict(X_scaled)
                
                # Map clusters to meaningful names based on centroids
                centroids = scaler.inverse_transform(kmeans.cluster_centers_)
                # Centroids: [tenure, monthly_charges]
                
                # Sort centroids to identify segments
                # High Tenure, High Charge -> Champions
                # High Tenure, Low Charge -> Loyalists
                # Low Tenure, High Charge -> New Customers
                # Low Tenure, Low Charge -> At Risk (Wait, this is subjective, but let's follow a logic)
                
                # Simple logic for mapping clusters back to labels:
                cluster_map = {}
                sorted_idx = np.lexsort((centroids[:, 1], centroids[:, 0])) # Sort by tenure then charge
                
                # This is a heuristic mapping
                cluster_map[sorted_idx[3]] = 'Champions (High Value)'
                cluster_map[sorted_idx[2]] = 'Loyalists'
                cluster_map[sorted_idx[1]] = 'New Customers'
                cluster_map[sorted_idx[0]] = 'At Risk (Churned)'
                
                df['SegmentLabel'] = df['Cluster'].map(cluster_map)
                segments = df['SegmentLabel'].value_counts().to_dict()
            else:
                # Fallback to rule-based if too few samples
                segments = {
                    'Champions (High Value)': len(df[df['tenure'] > 40]),
                    'Loyalists': len(df[(df['tenure'] <= 40) & (df['tenure'] > 20)]),
                    'New Customers': len(df[df['tenure'] <= 20]),
                    'At Risk (Churned)': churn_count if 'Churn' in df.columns else 0
                }

        # Contract Distribution
        contracts = {}
        if 'Contract' in df.columns:
            contracts = df['Contract'].value_counts().to_dict()

        return {
            "stats": {
                "totalCustomers": total_customers,
                "churnRate": round(churn_rate, 1),
                "avgTenure": round(avg_tenure, 1),
                "avgCharge": round(avg_monthly_charges, 2)
            },
            "segments": segments,
            "contracts": contracts
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files from the root directory
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
