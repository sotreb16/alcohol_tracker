def calculate_units(volume_ml, abv_percent):
    grams = volume_ml * (abv_percent / 100) * 0.789
    return round(grams / 10, 2)
