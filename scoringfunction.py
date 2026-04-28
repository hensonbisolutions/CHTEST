def score_company(c):
    score = 0

    # distress
    if c.get("accounts_overdue"):
        score += 25
    if c.get("cs_overdue"):
        score += 20

    # size proxies
    if c.get("large_company_flag"):
        score += 15
    if c.get("has_full_accounts"):
        score += 10
    if c.get("company_type") == "plc":
        score += 20

    # age
    try:
        year = int(c.get("incorporated", "9999")[:4])
        age = 2026 - year
        if age > 10:
            score += 10
        elif age > 5:
            score += 5
    except:
        pass

    # industry signal
    if c.get("sic_codes"):
        score += 5

    return min(score, 100)