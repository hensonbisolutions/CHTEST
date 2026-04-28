import requests

BASE_URL = "https://api.company-information.service.gov.uk"

def ch_get(endpoint, api_key):
    return requests.get(
        f"{BASE_URL}{endpoint}",
        auth=(api_key.strip(), "")
    ).json()


def search_company(api_key, query):
    data = ch_get(f"/search/companies?q={query}", api_key)
    return data.get("items", [])


def get_company(api_key, company_number):
    return ch_get(f"/company/{company_number}", api_key)


def get_officers(api_key, company_number):
    return ch_get(f"/company/{company_number}/officers", api_key)