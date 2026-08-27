from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import pyarrow.parquet as pq
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = "https://huggingface.co/datasets/CutehackX/hitek-data-bucket/resolve/main"

@app.get("/")
def root():
    return {"message": "API is live"}

@app.get("/lookup")
def lookup(number: str = Query(..., min_length=10, max_length=15)):
    if not number.isdigit():
        return {"status": "error", "message": "Only digits allowed"}

    last_digit = number[-1]
    main_url = f"{BASE_URL}/final_master_shard_{last_digit}.parquet"
    alt_url = f"{BASE_URL}/alt_master_shard_{last_digit}.parquet"

    def fetch_filter(url, column):
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                return []
            table = pq.read_table(io.BytesIO(resp.content))
            df = table.to_pandas()
            if column not in df.columns:
                return []
            return df[df[column] == number].to_dict(orient="records")
        except Exception as e:
            print(f"Error: {e}")
            return []

    main_records = fetch_filter(main_url, "mobile")
    alt_records = fetch_filter(alt_url, "alt")

    if not main_records and not alt_records:
        return {"status": "not_found", "number": number}

    return {
        "status": "success",
        "number": number,
        "main": main_records,
        "alt": alt_records
    }
