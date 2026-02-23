def audit_c_score(q1, q2, q3):
    map1 = {"Never": 0, "Monthly": 1, "Weekly": 2, "Daily": 4}
    map2 = {"1–2": 0, "3–4": 1, "5–6": 2, "7+": 3}
    map3 = {"Never": 0, "Monthly": 1, "Weekly": 2, "Daily": 4}
    return map1[q1] + map2[q2] + map3[q3]

def audit_c_risk(score):
    if score <= 3:
        return "Low risk"
    if score <= 7:
        return "Increasing risk"
    return "High risk"
