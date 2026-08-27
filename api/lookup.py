from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import duckdb

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

con = duckdb.connect()
con.execute("INSTALL httpfs;")
con.execute("LOAD httpfs;")

@app.get("/")
def root():
    return {"message": "API is live"}

@app.get("/lookup")
def lookup(number: str = Query(..., min_length=10, max_length=15)):
    if not number.isdigit():
        return {"status": "error", "message": "Only digits allowed"}

    last_digit = number[-1]
    primary_url = f"https://huggingface.co/datasets/CutehackX/hitek-data-bucket/resolve/main/final_master_shard_{last_digit}.parquet"
    alt_url = f"https://huggingface.co/datasets/CutehackX/hitek-data-bucket/resolve/main/alt_master_shard_{last_digit}.parquet"

    try:
        query = f"""
            SELECT *, 'Main' AS _record_type FROM read_parquet('{primary_url}') WHERE mobile = '{number}'
            UNION ALL
            SELECT *, 'Alt' AS _record_type FROM read_parquet('{alt_url}') WHERE alt = '{number}'
        """
        raw = con.execute(query).df().to_dict(orient="records")
        
        main_records = []
        alt_records = []
        for row in raw:
            rtype = row.pop('_record_type')
            if rtype == 'Main':
                main_records.append(row)
            else:
                alt_records.append(row)
        
        if not main_records and not alt_records:
            return {"status": "not_found", "number": number}
        
        return {
            "status": "success",
            "number": number,
            "main": main_records,
            "alt": alt_records
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
