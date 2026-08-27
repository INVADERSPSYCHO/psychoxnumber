from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import requests
import io
import logging

# Logging setup (Render logs mein dikhega)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = "https://huggingface.co/datasets/CutehackX/hitek-data-bucket/resolve/main"
DEVELOPER = "@PsychopathMC"

@app.get("/")
def root():
    return {"message": "API is live", "developer": DEVELOPER}

@app.get("/debug")
def debug(last_digit: int = Query(..., ge=0, le=9)):
    """Returns first 5 rows of a shard to inspect column names and data"""
    url = f"{BASE_URL}/final_master_shard_{last_digit}.parquet"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return {"error": f"Failed to fetch shard {last_digit}"}
        df = pd.read_parquet(io.BytesIO(resp.content))
        sample = df.head(5).to_dict(orient="records")
        return {
            "shard": last_digit,
            "columns": list(df.columns),
            "sample_data": sample
        }
    except Exception as e:
        logger.error(f"Debug error: {str(e)}")
        return {"error": str(e)}

@app.get("/lookup")
def lookup(number: str = Query(..., min_length=10, max_length=15)):
    if not number.isdigit():
        return {"status": "error", "message": "Only digits allowed", "developer": DEVELOPER}

    last_digit = number[-1]
    main_url = f"{BASE_URL}/final_master_shard_{last_digit}.parquet"
    alt_url = f"{BASE_URL}/alt_master_shard_{last_digit}.parquet"

    def fetch_filter(url, column):
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"Failed to fetch {url}")
                return []
            df = pd.read_parquet(io.BytesIO(resp.content))
            if column not in df.columns:
                logger.warning(f"Column '{column}' not found. Available: {list(df.columns)}")
                return []
            filtered = df[df[column] == number].to_dict(orient="records")
            logger.info(f"Found {len(filtered)} records for {number} in column {column}")
            return filtered
        except Exception as e:
            logger.error(f"Error in fetch_filter: {str(e)}")
            return []

    main_records = fetch_filter(main_url, "mobile")
    alt_records = fetch_filter(alt_url, "alt")

    if not main_records and not alt_records:
        return {"status": "not_found", "number": number, "developer": DEVELOPER}

    return {
        "status": "success",
        "number": number,
        "main": main_records,
        "alt": alt_records,
        "developer": DEVELOPER
    }
