import random

# Major Arcana = 22 Paths
PATHS = [f"Path {i}: {name}" for i, name in enumerate([
    "Aleph", "Beth", "Gimel", "Daleth", "Heh", "Vau", "Zain", "Cheth", 
    "Teth", "Yod", "Kaph", "Lamed", "Mem", "Nun", "Samekh", "Ayin", 
    "Peh", "Tzaddi", "Qoph", "Resh", "Shin", "Tau"
], start=11)]

# Minor Arcana = 10 Sephirot across 4 Elements
SEPHIROT = [
    "Kether", "Chokmah", "Binah", "Chesed", "Geburah", 
    "Tiphareth", "Netzach", "Hod", "Yesod", "Malkuth"
]
SUITS = ["Atziluth (Fire)", "Briah (Water)", "Yetzirah (Air)", "Assiah (Earth)"]

MINORS = [f"{seph} of {suit}" for seph in SEPHIROT for suit in SUITS]

WORLDS = ["1. Briah (Mental World)", "2. Yetzirah (Emotional World)", "3. Assiah (Physical World)"]

def generate_deck():
    # Fresh tree: 10 Sephirot x 4 suits + 22 Paths
    return MINORS + PATHS

# Execution matching your logic
for world in WORLDS:
    deck = generate_deck()  # Brand new deck (World)
    draw = random.sample(deck, 3)  # 3 mixed elements
    print(f"--- {world} ---")
    print(draw)
