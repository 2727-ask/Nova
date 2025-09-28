# Midpoint factors per subcategory (kg CO2 per USD).
# For ranges like 0.15–0.25 we use mid = (min+max)/2.
EMISSION_FACTORS = {
    # Travel
    ("Travel", "Public transport (bus, metro, train)"): (0.15, 0.25),
    ("Travel", "Ride-hailing (Uber, Lyft)"): (0.30, 0.50),
    ("Travel", "Flights (domestic, international)"): (0.70, 1.50),
    ("Travel", "Car-related (fuel, parking, tolls, EV charging)"): (0.25, 0.60),

    # Food
    ("Food", "Groceries"): (0.10, 0.20),
    ("Food", "Restaurants / Cafés"): (0.20, 0.35),
    ("Food", "Fast food / takeout"): (0.25, 0.40),
    ("Food", "Alcohol / bars"): (0.20, 0.35),

    # Shopping
    ("Shopping", "Clothing & fashion"): (0.20, 0.50),
    ("Shopping", "Electronics & gadgets"): (0.30, 0.80),
    ("Shopping", "Furniture / household goods"): (0.25, 0.60),
    ("Shopping", "General e-commerce (Amazon, Walmart, etc.)"): (0.15, 0.40),

    # Housing
    # Electricity handled specially (region-specific)
    ("Housing", "Gas / heating oil"): (0.30, 0.70),
    ("Housing", "Water & waste services"): (0.05, 0.15),
    ("Housing", "Internet / telecom"): (0.05, 0.15),

    # Health
    ("Health", "Pharmacies / medical stores"): (0.10, 0.25),
    ("Health", "Health insurance"): (0.05, 0.15),
    ("Health", "Fitness / gym / wellness subscriptions"): (0.05, 0.20),

    # Entertainment
    ("Entertainment", "Streaming services (Netflix, Spotify)"): (0.02, 0.10),
    ("Entertainment", "Gaming (Steam, PlayStation)"): (0.10, 0.30),
    ("Entertainment", "Events / concerts / cinema"): (0.25, 0.60),
    ("Entertainment", "Books & media"): (0.10, 0.30),

    # Education
    ("Education", "Tuition / course fees"): (0.05, 0.20),
    ("Education", "Online learning platforms (Coursera, Udemy)"): (0.02, 0.10),
    ("Education", "Books, journals, educational materials"): (0.10, 0.30),

    # Finances
    ("Finances", "Bank fees"): (0.02, 0.10),
    ("Finances", "Loan / credit card payments"): (0.02, 0.10),
    ("Finances", "Insurance (car, home, life)"): (0.05, 0.20),

    # Charity
    ("Charity", "NGO contributions"): (0.01, 0.05),
    ("Charity", "Religious donations"): (0.01, 0.05),
}

def factor_for(category: str, subcategory: str, mode: str = "mid") -> float:
    """
    mode: 'min' | 'max' | 'mid'
    For Electricity, return 0 and let caller handle region-specific intensity.
    """
    if category == "Housing" and subcategory.lower().startswith("electricity"):
        return 0.0
    rng = EMISSION_FACTORS.get((category, subcategory))
    if not rng:
        lo, hi = (0.05, 0.20)
    else:
        lo, hi = rng
    if mode == "min":
        return lo
    if mode == "max":
        return hi
    return (lo + hi) / 2.0

def get_emission_factor(category: str, subcategory: str, mode: str = "mid") -> float:
    """
    Returns the emission factor (kg CO₂ per USD) for the given category/subcategory.
    
    Args:
        category (str): Main spending category, e.g. "Travel"
        subcategory (str): Subcategory, e.g. "Flights (domestic, international)"
        mode (str): 'min', 'max', or 'mid' (default). 
    
    Returns:
        float: kg CO₂ per USD
    """
    # Electricity is special (region-specific) → return 0, caller handles it
    if category == "Housing" and subcategory.lower().startswith("electricity"):
        return 0.0

    rng = EMISSION_FACTORS.get((category, subcategory))
    if not rng:
        # fallback if missing → generic factor
        lo, hi = (0.05, 0.20)
    else:
        lo, hi = rng

    if mode == "min":
        return lo
    if mode == "max":
        return hi
    return (lo + hi) / 2.0


# services/emission_factors.py
from typing import Dict, Tuple
# keep your existing EMISSION_FACTORS and factor_for(...)

def category_factor(category: str, mode: str = "mid") -> float:
    """
    Average the subcategory factors for a given category.
    Used to convert category-level dollar budgets into emissions budgets (kg/USD).
    """
    vals = []
    for (cat, sub) in EMISSION_FACTORS.keys():
        if cat != category:
            continue
        # Electricity is handled elsewhere; skip here
        if cat == "Housing" and sub.lower().startswith("electricity"):
            continue
        vals.append(factor_for(cat, sub, mode=mode))
    if not vals:
        # sensible fallback if category has no sub-factors listed
        return (0.05 + 0.20) / 2.0  # 0.125 kg/USD mid
    return sum(vals) / len(vals)