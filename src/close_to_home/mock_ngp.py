"""Seeded fake-people generator, shaped like real VAN /people API responses.

The field names match the NGP VAN v4 API (verified against the AI Dems
Training NGP sandbox). geoLocation is populated here even though the sandbox
returns null — narrate it as "geocoded addresses".
"""

import random

SEED = 42
N_PEOPLE = 1200

# (name, center_lat, center_lng, sigma, zip)
CLUSTERS = [
    ("Midtown", 38.572, -121.478, 0.011, "95816"),
    ("East Sacramento", 38.573, -121.440, 0.010, "95819"),
    ("Land Park", 38.545, -121.510, 0.012, "95818"),
    ("Natomas", 38.650, -121.510, 0.016, "95835"),
    ("Elk Grove", 38.410, -121.370, 0.020, "95624"),
    ("Downtown", 38.581, -121.494, 0.008, "95814"),
    ("Oak Park", 38.545, -121.462, 0.010, "95817"),
    ("Tahoe Park", 38.546, -121.437, 0.010, "95820"),
    ("Pocket-Greenhaven", 38.495, -121.535, 0.013, "95831"),
    ("Meadowview", 38.468, -121.465, 0.012, "95832"),
    ("South Sacramento", 38.500, -121.440, 0.015, "95823"),
    ("Del Paso Heights", 38.630, -121.450, 0.013, "95838"),
    ("Arden-Arcade", 38.600, -121.385, 0.015, "95825"),
    ("South Natomas", 38.615, -121.510, 0.012, "95833"),
    ("Rosemont", 38.552, -121.355, 0.013, "95826"),
]
CLUSTER_WEIGHTS = [
    0.11, 0.09, 0.08, 0.07, 0.07,
    0.05, 0.07, 0.06, 0.06, 0.06,
    0.07, 0.06, 0.06, 0.05, 0.04,
]

FIRST_NAMES = [
    "James", "Maria", "Robert", "Linda", "Michael", "Patricia", "David",
    "Jennifer", "Carlos", "Elizabeth", "Kevin", "Susan", "Brian", "Jessica",
    "Angela", "Daniel", "Karen", "Marcus", "Nancy", "Anthony", "Lisa",
    "Miguel", "Sandra", "Eric", "Ashley", "Tina", "Jose", "Emily", "Frank",
    "Michelle", "Grace", "Andre", "Rachel", "Victor", "Diane", "Sam",
    "Priya", "Wei", "Fatima", "Dmitri",
]
LAST_NAMES = [
    "Smith", "Johnson", "Garcia", "Nguyen", "Brown", "Martinez", "Lee",
    "Davis", "Rodriguez", "Wilson", "Anderson", "Tran", "Thomas", "Moore",
    "Jackson", "Kim", "White", "Lopez", "Harris", "Chen", "Clark", "Ramirez",
    "Lewis", "Singh", "Walker", "Hall", "Young", "Torres", "Patel", "King",
    "Wright", "Scott", "Rivera", "Green", "Adams", "Baker", "Flores",
    "Campbell", "Mitchell", "Reyes",
]
STREETS = [
    "J St", "K St", "L St", "P St", "Q St", "Folsom Blvd", "Freeport Blvd",
    "Broadway", "Riverside Blvd", "Del Paso Blvd", "Stockton Blvd",
    "H St", "Elvas Ave", "McKinley Blvd", "Land Park Dr", "Truxel Rd",
    "El Camino Ave", "Laguna Blvd", "Bond Rd", "Meadow Ln", "Fair Oaks Blvd",
]
EMPLOYERS = [
    ("State of California", "Analyst"), ("Sutter Health", "Nurse"),
    ("Sacramento City USD", "Teacher"), ("Intel", "Engineer"),
    ("Self-employed", "Consultant"), ("Raley's", "Manager"),
    ("UC Davis Health", "Technician"), ("Acme Corp", "Engineer"),
    (None, None), (None, None), (None, None),
]


def _make_person(rng: random.Random, i: int) -> dict:
    (neighborhood, clat, clng, sigma, zipcode) = rng.choices(
        CLUSTERS, weights=CLUSTER_WEIGHTS
    )[0]
    lat = rng.gauss(clat, sigma)
    lng = rng.gauss(clng, sigma * 1.2)

    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)
    employer, occupation = rng.choice(EMPLOYERS)

    is_donor = rng.random() < 0.35
    contribution_summary = None
    if is_donor:
        gifts = rng.randint(1, 8)
        total = round(rng.lognormvariate(4.0, 1.0) + 10 * gifts, 2)
        contribution_summary = {"totalAmount": total, "totalGifts": gifts}

    is_volunteer = rng.random() < 0.15
    tags = ["Volunteer"] if is_volunteer else []

    email = f"{first.lower()}.{last.lower()}{rng.randint(1, 999)}@example.com"
    phone = f"916555{rng.randint(0, 9999):04d}"

    return {
        "vanId": 127240000 + i,
        "firstName": first,
        "lastName": last,
        "party": rng.choice(["D", "D", "D", "N", None]),
        "employer": employer,
        "occupation": occupation,
        "emails": [
            {
                "email": email,
                "type": "P",
                "isPreferred": True,
                "isSubscribed": True,
                "subscriptionStatus": "S",
            }
        ],
        "phones": [
            {
                "phoneNumber": phone,
                "phoneType": "Personal",
                "deviceType": "Cell",
                "isBest": True,
                "smsOptInStatus": "Unknown",
            }
        ],
        "addresses": [
            {
                "addressLine1": f"{rng.randint(100, 9899)} {rng.choice(STREETS)}",
                "addressLine2": (
                    f"Apt {rng.randint(1, 40)}" if rng.random() < 0.2 else None
                ),
                "city": "Sacramento" if neighborhood != "Elk Grove" else "Elk Grove",
                "stateOrProvince": "CA",
                "zipOrPostalCode": zipcode,
                "type": "Voting",
                "isPreferred": True,
                "geoLocation": {"lat": round(lat, 6), "lon": round(lng, 6)},
            }
        ],
        "contributionSummary": contribution_summary,
        "isVolunteer": is_volunteer,
        "tags": tags,
        # Demo conveniences (not VAN fields): flattened for the frontend.
        "lat": round(lat, 6),
        "lng": round(lng, 6),
        "neighborhood": neighborhood,
    }


def generate_people() -> list[dict]:
    rng = random.Random(SEED)
    return [_make_person(rng, i) for i in range(N_PEOPLE)]


PEOPLE = generate_people()
