def compute_simple_score(company):
    """
    Basic company health score (simple version)
    """

    score = 50

    # Active companies get boost
    if company.get("company_status") == "active":
        score += 20

    # LTD companies slightly more stable
    if company.get("type") == "ltd":
        score += 10

    # Dissolved = big risk
    if company.get("company_status") != "active":
        score -= 40

    return max(0, min(score, 100))