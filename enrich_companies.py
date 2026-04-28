import pandas as pd
import requests
import os
from dotenv import load_dotenv
import time
from pathlib import Path
from tqdm import tqdm

# -----------------------
# LOAD ENV
# -----------------------
load_dotenv()
API_KEY = os.getenv("COMPANIES_HOUSE_API_KEY")

if not API_KEY:
    raise ValueError("Missing COMPANIES_HOUSE_API_KEY in .env file")

# -----------------------
# FILE PATHS (FIXED)
# -----------------------
BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "enriched.csv"
OUTPUT_FILE = BASE_DIR / "enriched_output.csv"

# -----------------------
# LOAD DATA
# -----------------------
df = pd.read_csv(INPUT_FILE)

if "company_number" not in df.columns:
    raise ValueError("CSV must contain 'company_number' column")

# -----------------------
# API FUNCTION
# -----------------------
def get_company_data(company_number):
    url = f"https://api.company-information.service.gov.uk/company/{company_number}"

    try:
        r = requests.get(url, auth=(API_KEY, ""), timeout=10)

        if r.status_code != 200:
            return {
                "status": None,
                "type": None,
                "incorporated": None,
                "jurisdiction": None,
                "sic_codes": None,
                "error": f"HTTP {r.status_code}"
            }

        data = r.json()

        return {
            "status": data.get("company_status"),
            "type": data.get("type"),
            "incorporated": data.get("date_of_creation"),
            "jurisdiction": data.get("jurisdiction"),
            "sic_codes": ",".join(data.get("sic_codes", [])) if data.get("sic_codes") else None,
            "error": None
        }

    except Exception as e:
        return {
            "status": None,
            "type": None,
            "incorporated": None,
            "jurisdiction": None,
            "sic_codes": None,
            "error": str(e)
        }

# -----------------------
# ENRICH LOOP (WITH PROGRESS)
# -----------------------
results = []

print(f"\nStarting enrichment for {len(df)} companies...\n")

for i, row in tqdm(df.iterrows(), total=len(df)):

    company_number = row["company_number"]

    print(f"[{i+1}/{len(df)}] Processing {company_number}")

    data = get_company_data(company_number)

    enriched_row = {**row.to_dict(), **data}
    results.append(enriched_row)

    if (i + 1) % 10 == 0:
        print(f"✔ Progress: {i+1}/{len(df)}")

    time.sleep(0.3)

# -----------------------
# SAVE OUTPUT
# -----------------------
output_df = pd.DataFrame(results)
output_df.to_csv(OUTPUT_FILE, index=False)

print("\n========================")
print("ENRICHMENT COMPLETE")
print(f"Saved to: {OUTPUT_FILE}")
print("========================\n")