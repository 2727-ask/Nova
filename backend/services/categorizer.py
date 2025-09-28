import re
from typing import Dict, Tuple, List
from models.schemas import Transaction

# ---- Categories & Subcategories ----
# You can keep expanding the keyword map over time.
# Order matters: first match wins.
RULES: List[Tuple[re.Pattern, str, str]] = [
    # ========== TRAVEL ==========
    # Public transport
    (re.compile(r"\b(metro|lrt|subway|amtrak|bus pass|valley metro)\b", re.I), "Travel", "Public transport (bus, metro, train)"),
    # Ride-hailing
    (re.compile(r"\b(uber|lyft)\b", re.I), "Travel", "Ride-hailing (Uber, Lyft)"),
    # Flights
    (re.compile(r"\b(delta|united|american airlines|aa\.com|southwest|british airways|lufthansa|air india|alaska airlines)\b", re.I), "Travel", "Flights (domestic, international)"),
    # Car-related
    (re.compile(r"\b(shell|chevron|bp|exxon|mobil|circle k|qt|speedway|parking|toll|evgo|chargepoint)\b", re.I), "Travel", "Car-related (fuel, parking, tolls, EV charging)"),

    # ========== FOOD ==========
    # Groceries
    (re.compile(r"\b(costco|walmart|kroger|safeway|whole foods|trader joe'?s?)\b", re.I), "Food", "Groceries"),
    # Restaurants / Cafés
    (re.compile(r"\b(restaurant|cafe|coffee|starbucks|panera|chipotle|shake shack|chick-?fil-?a|subway|bk|kfc|domino'?s?)\b", re.I), "Food", "Restaurants / Cafés"),
    # Fast food / takeout
    (re.compile(r"\b(doordash|ubereats|grubhub|takeout|drive[- ]?thru)\b", re.I), "Food", "Fast food / takeout"),
    # Alcohol / bars
    (re.compile(r"\b(bar|pub|brewery|liquor)\b", re.I), "Food", "Alcohol / bars"),

    # ========== SHOPPING ==========
    (re.compile(r"\b(amazon|amzn|walmart|target|best buy|ikea|etsy|shein)\b", re.I), "Shopping", "General e-commerce (Amazon, Walmart, etc.)"),
    (re.compile(r"\b(nordstrom|h&m|zara|uniqlo|gap|old navy|forever 21)\b", re.I), "Shopping", "Clothing & fashion"),
    (re.compile(r"\b(apple store|best buy|micro center|newegg)\b", re.I), "Shopping", "Electronics & gadgets"),
    (re.compile(r"\b(ashley furniture|wayfair|ikea)\b", re.I), "Shopping", "Furniture / household goods"),

    # ========== HOUSING ==========
    (re.compile(r"\b(rent|landlord|mortgage|imt desert palm|property management|hoa)\b", re.I), "Housing", "Rent / mortgage"),
    (re.compile(r"\b(aps|srp|electric|electricity)\b", re.I), "Housing", "Electricity (grid-specific carbon intensity)"),
    (re.compile(r"\b(gas company|southwest gas|heating oil)\b", re.I), "Housing", "Gas / heating oil"),
    (re.compile(r"\b(water|waste|trash|city of .+ water)\b", re.I), "Housing", "Water & waste services"),
    (re.compile(r"\b(comcast|xfinity|cox|verizon|t-mobile|at&t|internet|telecom)\b", re.I), "Housing", "Internet / telecom"),

    # ========== HEALTH ==========
    (re.compile(r"\b(walgreens|cvs|rite aid|pharmacy|clinic|dental|vision)\b", re.I), "Health", "Pharmacies / medical stores"),
    (re.compile(r"\b(health insurance|insurance premium)\b", re.I), "Health", "Health insurance"),
    (re.compile(r"\b(gym|fitness|yoga|wellness)\b", re.I), "Health", "Fitness / gym / wellness subscriptions"),

    # ========== ENTERTAINMENT ==========
    (re.compile(r"\b(netflix|spotify|hulu|disney\+)\b", re.I), "Entertainment", "Streaming services (Netflix, Spotify)"),
    (re.compile(r"\b(steam|playstation|xbox)\b", re.I), "Entertainment", "Gaming (Steam, PlayStation)"),
    (re.compile(r"\b(concert|cinema|theatre|amc)\b", re.I), "Entertainment", "Events / concerts / cinema"),
    (re.compile(r"\b(bookstore|book|audible)\b", re.I), "Entertainment", "Books & media"),

    # ========== EDUCATION ==========
    (re.compile(r"\b(tuition|university|college)\b", re.I), "Education", "Tuition / course fees"),
    (re.compile(r"\b(coursera|udemy|edx|khan academy)\b", re.I), "Education", "Online learning platforms (Coursera, Udemy)"),
    (re.compile(r"\b(textbook|journal)\b", re.I), "Education", "Books, journals, educational materials"),

    # ========== FINANCES ==========
    (re.compile(r"\b(bank fee|service fee|overdraft fee|interest fee)\b", re.I), "Finances", "Bank fees"),
    (re.compile(r"\b(payment|e-payment|discover|loan)\b", re.I), "Finances", "Loan / credit card payments"),
    (re.compile(r"\b(car insurance|home insurance|life insurance|insurance)\b", re.I), "Finances", "Insurance (car, home, life)"),

    # ========== CHARITY ==========
    (re.compile(r"\b(donation|donate|gofundme|ngo|charity)\b", re.I), "Charity", "NGO contributions"),
    (re.compile(r"\b(church|temple|masjid)\b", re.I), "Charity", "Religious donations"),
]

def categorize(description: str) -> Tuple[str, str]:
    desc = description.lower()
    for pattern, cat, sub in RULES:
        if pattern.search(desc):
            return cat, sub
    return "Uncategorized", "Uncategorized"

def summarize_transactions(transactions: List[Transaction]):
    """
    Aggregate NEGATIVE amounts (spend) by Category/Subcategory.
    Positive amounts (deposits/refunds) are ignored for the spend summary.
    """
    summary: Dict[str, Dict[str, float]] = {}
    uncategorized_total = 0.0

    for t in transactions:
        amt = t.amount
        if amt >= 0:
            continue  # ignore deposits/income for spend summary

        cat, sub = categorize(t.description)
        if cat == "Uncategorized":
            uncategorized_total += abs(amt)
            continue

        summary.setdefault(cat, {})
        summary[cat].setdefault(sub, 0.0)
        summary[cat][sub] += abs(amt)

    # round to 2 decimals
    for cat in list(summary.keys()):
        for sub in list(summary[cat].keys()):
            summary[cat][sub] = round(summary[cat][sub], 2)

    return summary, uncategorized_total