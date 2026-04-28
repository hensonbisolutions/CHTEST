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
# FILES
# -----------------------
BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "enriched.csv"
OUTPUT_FILE = BASE_DIR / "enriched_financial.csv"

# -----------------------
# LOAD DATA
# -----------------------
df = pd.read_csv(INPUT_FILE)

if "company_number" not in df.columns:
    raise ValueError("CSV must contain 'company_number' column")

# -----------------------
# FINANCIAL FILINGS FETCH
# -----------------------
def get_latest_accounts(company_number):
    url = f"https://api.company-information.service.gov.uk/company/{company_number}/filing-history"

    try:
        r = requests.get(url, auth=(API_KEY, ""), timeout=10)

        if r.status_code != 200:
            return {
                "last_accounts_date": None,
                "accounts_type": None,
                "accounts_description": None,
                "filing_error": f"HTTP {r.status_code}"
            }

        data = r.json().get("items", [])

        # Find latest accounts filing
        for item in data:
            category = item.get("category", "")
            if "accounts" in category:
                return {
                    "last_accounts_date": item.get("date"),
                    "accounts_type": item.get("subcategory"),
                    "accounts_description": item.get("description"),
                    "filing_error": None
                }

        return {
            "last_accounts_date": None,
            "accounts_type": None,
            "accounts_description": None,
            "filing_error": "No accounts found"
        }

    except Exception as e:
        return {
            "last_accounts_date": None,
            "accounts_type": None,
            "accounts_description": None,
            "filing_error": str(e)
        }

# -----------------------
# ENRICH LOOP
# -----------------------
results = []

print(f"\nStarting financial parsing for {len(df)} companies...\n")

for i, row in tqdm(df.iterrows(), total=len(df)):

    company_number = row["company_number"]

    print(f"[{i+1}/{len(df)}] Fetching financials for {company_number}")

    financial_data = get_latest_accounts(company_number)

    enriched_row = {**row.to_dict(), **financial_data}
    results.append(enriched_row)

    if (i + 1) % 10 == 0:
        print(f"✔ Financial progress: {i+1}/{len(df)}")

    time.sleep(0.3)

# -----------------------
# SAVE OUTPUT
# -----------------------
output_df = pd.DataFrame(results)
output_df.to_csv(OUTPUT_FILE, index=False)

print("\n========================")
print("FINANCIAL ENRICHMENT COMPLETE")
print(f"Saved to: {OUTPUT_FILE}")
print("========================\n")