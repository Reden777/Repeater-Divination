#!/usr/bin/env python3
"""
GALGAL4.py
Atmospheric Sefer Yetzirah Divination & Word Discovery Engine:
  - Default (3 Wheels): Briah (ה), Yetzirah (ו), Assiah (ה) -> 3-Letter Triad (Shoresh)
  - Optional (--atziluth): Atziluth (י), Briah (ה), Yetzirah (ו), Assiah (ה) -> 4-Letter Tetrad (Tzeruf)

Automatically extracts and decodes words via:
  Method 1: Primary Rotation Axis (Thesis / Hesed Vector)
  Method 2: Synthesis Axis (Outcome / Tiphareth Vector)
  Method 3: Active Foundation Reservoir (Major Arcana Filter)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import hashlib
import os
import re
import argparse
import itertools
import urllib.request
import urllib.error
from datetime import datetime

# ----- Optional color UI via rich -----
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# =====================================================================
# 1. Kabbalistic Structure (Sefer Yetzirah & Tree of Life Mapping)
# =====================================================================

HEBREW_PATHS = [
    ("Path 11", "Aleph (א)", "Air / Mother", "The Fool"),
    ("Path 12", "Beth (ב)", "Mercury / Double", "The Magician"),
    ("Path 13", "Gimel (ג)", "Moon / Double", "The High Priestess"),
    ("Path 14", "Daleth (ד)", "Venus / Double", "The Empress"),
    ("Path 15", "Heh (ה)", "Aries / Simple", "The Emperor"),
    ("Path 16", "Vau (ו)", "Taurus / Simple", "The Hierophant"),
    ("Path 17", "Zayin (ז)", "Gemini / Simple", "The Lovers"),
    ("Path 18", "Cheth (ח)", "Cancer / Simple", "The Chariot"),
    ("Path 19", "Teth (ט)", "Leo / Simple", "Strength"),
    ("Path 20", "Yod (י)", "Virgo / Simple", "The Hermit"),
    ("Path 21", "Kaph (כ)", "Jupiter / Double", "Wheel of Fortune"),
    ("Path 22", "Lamed (ל)", "Libra / Simple", "Justice"),
    ("Path 23", "Mem (מ)", "Water / Mother", "The Hanged Man"),
    ("Path 24", "Nun (נ)", "Scorpio / Simple", "Death"),
    ("Path 25", "Samekh (ס)", "Sagittarius / Simple", "Temperance"),
    ("Path 26", "Ayin (ע)", "Capricorn / Simple", "The Devil"),
    ("Path 27", "Peh (פ)", "Mars / Double", "The Tower"),
    ("Path 28", "Tzaddi (צ)", "Aquarius / Simple", "The Star"),
    ("Path 29", "Qoph (ק)", "Pisces / Simple", "The Moon"),
    ("Path 30", "Resh (ר)", "Sun / Double", "The Sun"),
    ("Path 31", "Shin (ש)", "Fire / Mother", "Judgement"),
    ("Path 32", "Tau (ת)", "Saturn / Double", "The World"),
]

SEPHIROT = [
    ("Kether", "Crown / Primordial Will"),
    ("Chokmah", "Wisdom / Creative Spark"),
    ("Binah", "Understanding / Formative Matrix"),
    ("Chesed", "Mercy / Boundless Grace"),
    ("Geburah", "Severity / Judgment & Strength"),
    ("Tiphareth", "Beauty / Harmonizing Sun"),
    ("Netzach", "Eternity / Victory & Passion"),
    ("Hod", "Splendor / Intellect & Resonance"),
    ("Yesod", "Foundation / Astral Conduit"),
    ("Malkuth", "Kingdom / Manifest Reality")
]

WORLDS_SUITS = [
    ("Atziluth (Fire)", "Wands"),
    ("Briah (Water)", "Cups"),
    ("Yetzirah (Air)", "Swords"),
    ("Assiah (Earth)", "Pentacles")
]

COURT_RANKS = [
    ("Page", "Princess / Earth"),
    ("Knight", "Prince / Air"),
    ("Queen", "Mother / Water"),
    ("King", "Father / Fire")
]

# Gematria values of the 22 Foundation Letters
HEBREW_GEMATRIA: Dict[str, int] = {
    'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9,
    'י': 10, 'כ': 20, 'ך': 20, 'ל': 30, 'מ': 40, 'ם': 40, 'נ': 50, 'ן': 50,
    'ס': 60, 'ע': 70, 'פ': 80, 'ף': 80, 'צ': 90, 'ץ': 90, 'ק': 100, 'ר': 200,
    'ש': 300, 'ת': 400
}

# Key Cosmological Values (Section 4.4)
GEMATRIA_KEYS: Dict[int, str] = {
    21: "אֶהְיֶה (Ehyeh — 'I Will Be' / Primordial Divine Becoming)",
    22: "כ״ב אותיות (The 22 Foundation Letters — Balance of Paths)",
    25: "כֹּה (Koh — 'Thus' / Divine Decree)",
    26: "יהו״ה (The Tetragrammaton — Complete Divine Name)",
    42: "שם מ״ב (Shem Mem-Bet — 42-Letter Name of Creation)",
    48: "גִּילָה (Gilah — Joy / Exultant Revelation) / כּוֹכָב (Kokhav — Mercury / Illumination)",
    51: "לִוְיָה (Livyāh — Escort / Garland of Grace)",
    72: "חֶסֶד (Chesed — Boundless Mercy) / ע״ב שמות (72 Names)",
    80: "יְסוֹד (Yesod — Astral Foundation / The Conduit of Flow) / פ (Letter Peh — Speech & Outward Expression)",
    86: "אֱלֹהִים (Elohim) / הַטֶּבַע (Ha-Teva — Nature / Physical Order)",
    220: "220 (22 Letters x 10 Sephirot — Full Saturation)",
    230: "230 (Threshold of the 231 Gates of Sefer Yetzirah)",
    280: "ר״פ גְּבוּרוֹת (The 280 Powers of Formative Precision)",
    455: "שִׁפְעָה (Shif'ah — Overflowing Abundance & Insight)",
}

# Recognized Roots and Words for Permutation Matching
KNOWN_WORDS: Dict[str, str] = {
    "החל": "הֵחֵל (Hechel — 'He began / initiated')",
    "הכרה": "הַכָּרָה (Hakarah — 'Consciousness / Recognition')",
    "לויה": "לִוְיָה (Livyāh — 'Escort / Grace / Harmony')",
    "הוה": "הוֹוֶה (Hoveh — 'The Present / Reality / Being')",
    "יהו": "יָהוּ (Yahu / Yeho — Divine Trigrammaton)",
    "יוי": "יו״י (Y-V-Y — Sacred Divine Cipher, Gematria 26)",
    "יהוה": "יהו״ה / הֲוָיָה (Havayah — 'Being / The Tetragrammaton')",
    "אהה": "אֲהָהּ (Ahah — 'Alas! / Breath of wonder and release')",
    "אחך": "אַחַר כָּךְ (Achar Kach — 'Afterwards / Next / Move forward')",
    "אמש": "אֶמֶשׁ (Emesh — 'Yesterday / The past / Primordial 3 Mothers')",
    "שמא": "שֶׁמָּא (Shema — 'Perhaps / Lest')",
    "משא": "מַשָּׂא (Masa — 'Oracle / Burden / Utterance')",
    "אמת": "אֱמֶת (Emet — 'Truth / The Divine Seal')",
    "אשת": "אֵשֶׁת (Eshet — 'Partner / Woman of character')",
    "שש": "שָׂשׂ (Sas — 'Joy / Exultation / Delight')",
    "יאה": "יָאֶה (Ya'eh — 'Fitting / Suitable / Proper')",
    "יאי": "יָאֶה (Ya'eh — 'Fitting / Suitable')",
    "אי": "אִי (I — 'Island / Shore') / אַיֵּה (Aye — 'Where')",
    "אהיה": "אֶהְיֶה (Ehyeh — 'I Will Be / Divine Becoming')",
    "אסף": "אָסַף (Asaf — 'To gather, assemble, and harvest')",
    "דף": "דַּף (Daf — 'A new leaf / Turn of the page')",
    "לכך": "לְכָךְ (Le'khach — 'For this very purpose')",
    "לב": "לֵב (Lev — 'Heart / Center')",
    "בכל": "בַּכֹּל (Bakol — 'In all things / Complete blessing')",
    "שבת": "שַׁבָּת (Shabbat — 'Rest / Wholeness')",
    "אור": "אוֹר (Or — 'Light / Illumination')",
    "טוב": "טוֹב (Tov — 'Goodness / Harmonic alignment')",
    "שלום": "שָׁלוֹם (Shalom — 'Peace / Completeness')",
    "חי": "חַי (Chai — 'Life / Living')",
    "ברא": "בָּרָא (Bara — 'To create')",
    "יצר": "יָצַר (Yatzar — 'To form')",
    "עשה": "עָשָׂה (Asah — 'To manifest / complete action')",
    "גלגל": "גַּלְגַּל (Galgal — 'Wheel / Revolving cycle')",
}


@dataclass(frozen=True)
class GalgalNode:
    tarot_name: str
    kabbalah_path: str
    attribute: str
    is_major: bool


@dataclass(frozen=True)
class RotatedNode:
    node: GalgalNode
    position_label: str
    is_reversed: bool
    wheel_degree: int


class GalgalWheel:
    def __init__(self):
        self.nodes: List[GalgalNode] = self._build_wheel()

    def _build_wheel(self) -> List[GalgalNode]:
        nodes = []
        # 1. 22 Foundation Letters (Major Arcana)
        for path_num, letter, attr, tarot in HEBREW_PATHS:
            nodes.append(GalgalNode(
                tarot_name=tarot,
                kabbalah_path=f"{path_num} • {letter}",
                attribute=attr,
                is_major=True
            ))

        # 2. 40 Sephirotic Decanates (Pip Cards across 4 Elements)
        for seph_idx, (seph_name, seph_attr) in enumerate(SEPHIROT):
            rank_name = "Ace" if seph_idx == 0 else str(seph_idx + 1)
            for suit_world, suit_name in WORLDS_SUITS:
                nodes.append(GalgalNode(
                    tarot_name=f"{rank_name} of {suit_name}",
                    kabbalah_path=f"{seph_name} in {suit_world}",
                    attribute=seph_attr,
                    is_major=False
                ))

        # 3. 16 Court Nodes
        for rank_name, court_attr in COURT_RANKS:
            for suit_world, suit_name in WORLDS_SUITS:
                nodes.append(GalgalNode(
                    tarot_name=f"{rank_name} of {suit_name}",
                    kabbalah_path=f"Persona of {suit_world}",
                    attribute=court_attr,
                    is_major=False
                ))

        return nodes

    def __len__(self) -> int:
        return len(self.nodes)


# =====================================================================
# 2. Entropy Engine & Letter Extraction
# =====================================================================

class EntropyHarvester:
    RANDOM_ORG_URL = "https://www.random.org/integers/?num=32&min=0&max=255&col=1&base=10&format=plain&rnd=new"
    USER_AGENT = "GalgalimTarot/4.1 (Atmospheric Sefer Yetzirah Engine)"

    @classmethod
    def harvest(cls, force_offline: bool = False) -> Tuple[bytes, str]:
        if not force_offline:
            try:
                req = urllib.request.Request(
                    cls.RANDOM_ORG_URL,
                    headers={"User-Agent": cls.USER_AGENT}
                )
                with urllib.request.urlopen(req, timeout=3.5) as response:
                    if response.status == 200:
                        raw_text = response.read().decode('utf-8').strip()
                        byte_vals = [
                            int(line) for line in raw_text.split()
                            if line.isdigit()
                        ]
                        if len(byte_vals) == 32:
                            return bytes(byte_vals), "Atmospheric Radio Noise (random.org)"
            except Exception:
                pass

        return os.urandom(32), "OS CSPRNG (local urandom fallback)"


class ProtectiveHasher:
    PROTECTION_ITERATIONS = 888_888
    HASH_LENGTH = 32

    @staticmethod
    def derive_protected_bytes(base_bytes: bytes, salt_bytes: bytes) -> bytes:
        try:
            return hashlib.pbkdf2_hmac(
                'sha256', base_bytes, salt_bytes,
                ProtectiveHasher.PROTECTION_ITERATIONS,
                dklen=ProtectiveHasher.HASH_LENGTH
            )
        except Exception:
            result = base_bytes
            for _ in range(ProtectiveHasher.PROTECTION_ITERATIONS):
                result = hashlib.sha256(result + salt_bytes).digest()
            return result[:ProtectiveHasher.HASH_LENGTH]


def hash_for_int(seed: bytes, salt: str) -> int:
    salt_bytes = salt.encode("utf-8")
    hashed_bytes = ProtectiveHasher.derive_protected_bytes(seed, salt_bytes)
    return int.from_bytes(hashed_bytes, 'big')


def extract_representing_letter(node: GalgalNode) -> Tuple[str, str]:
    """
    Extracts the Hebrew character according to:
      1. Major Arcana -> The 22 Foundation Letters
      2. Minor Arcana -> Tetragrammaton Suit Reduction (Y-H-V-H)
    """
    if node.is_major:
        m = re.search(r"\(([\u0590-\u05FF])\)", node.kabbalah_path)
        char = m.group(1) if m else "?"
        letter_name = node.kabbalah_path.split("•")[-1].strip()
        return char, f"Major Arcana • {letter_name}"
    else:
        name_and_path = f"{node.tarot_name} {node.kabbalah_path}"
        if "Wands" in name_and_path or "Atziluth" in name_and_path:
            return "י", "Yod (י) of Atziluth / Wands"
        elif "Cups" in name_and_path or "Briah" in name_and_path:
            return "ה", "Heh (ה) of Briah / Cups"
        elif "Swords" in name_and_path or "Yetzirah" in name_and_path:
            return "ו", "Vav (ו) of Yetzirah / Swords"
        elif "Pentacles" in name_and_path or "Assiah" in name_and_path:
            return "ה", "Heh (ה) of Assiah / Pentacles"
        return "?", "Sephirah Node"


def analyze_letter_sequence(letters: List[str]) -> Dict:
    """Analyzes a sequence of Hebrew letters for gematria, direct readings, and circular anagrams."""
    clean = [c for c in letters if c in HEBREW_GEMATRIA]
    if not clean:
        return {
            "letters": letters,
            "raw_str": " - ".join(letters),
            "gematria": 0,
            "gematria_desc": "",
            "matches": []
        }

    raw_str = " - ".join(clean)
    direct_str = "".join(clean)
    gematria_val = sum(HEBREW_GEMATRIA.get(c, 0) for c in clean)
    gematria_desc = GEMATRIA_KEYS.get(gematria_val, "")

    seen_words = set()
    matches = []

    # 1. Direct Reading
    if direct_str in KNOWN_WORDS:
        seen_words.add(direct_str)
        matches.append((direct_str, KNOWN_WORDS[direct_str], "Direct Reading (Kritat ha-Ot)"))

    # 2. Wheel Anagram Permutations (Tzeruf & Temurah)
    for p in set(itertools.permutations(clean)):
        perm_word = "".join(p)
        if perm_word in KNOWN_WORDS and perm_word not in seen_words:
            seen_words.add(perm_word)
            matches.append((perm_word, KNOWN_WORDS[perm_word], "Wheel Anagram (Tzeruf)"))

    return {
        "letters": clean,
        "raw_str": raw_str,
        "direct_word": direct_str,
        "gematria": gematria_val,
        "gematria_desc": gematria_desc,
        "matches": matches
    }


# =====================================================================
# 3. Galgal Engine & Display Routines
# =====================================================================

class GalgalEngine:
    POSITION_LABELS = {
        1: ["The Axis (Kav ha-Emtza)"],
        3: ["Thesis (Hesed/Right)", "Antithesis (Gevurah/Left)", "Synthesis (Tiphareth/Balance)"],
        10: [
            "1. Kether (Significator)", "2. Chokmah (Crossing Force)", "3. Binah (Subconscious Ground)",
            "4. Chesed (Recent Past)", "5. Geburah (Conscious Crown)", "6. Tiphareth (Near Horizon)",
            "7. Netzach (Inner Self)", "8. Hod (External Field)", "9. Yesod (Hopes & Veils)",
            "10. Malkuth (Physical Manifestation)"
        ]
    }

    def __init__(self, seed: bytes, atmospheric_entropy: bytes, reversals_enabled: bool):
        self.wheel = GalgalWheel()
        self.seed = seed
        self.atmospheric_entropy = atmospheric_entropy
        self.reversals_enabled = reversals_enabled

    def spin_wheel(self, num_draws: int) -> Tuple[List[RotatedNode], int, str]:
        available_nodes = self.wheel.nodes.copy()
        drawn_nodes: List[RotatedNode] = []
        labels = self.POSITION_LABELS.get(num_draws, [f"Gate {i+1}" for i in range(num_draws)])

        base_rotation_raw = int.from_bytes(self.atmospheric_entropy[:4], 'big')
        wheel_shift_deg = (base_rotation_raw % 360)
        direction = "Panim (Direct)" if (base_rotation_raw % 2 == 0) else "Achor (Retrograde)"

        for i in range(num_draws):
            if not available_nodes:
                break

            draw_salt = f"galgal-draw-gate-{i}"
            draw_idx = hash_for_int(self.seed, draw_salt) % len(available_nodes)
            node = available_nodes.pop(draw_idx)

            is_reversed = False
            if self.reversals_enabled:
                reversal_salt = f"galgal-reversal-{i}"
                is_reversed = (hash_for_int(self.seed, reversal_salt) % 100) < 8

            node_degree = (wheel_shift_deg + int((i / num_draws) * 360)) % 360

            drawn_nodes.append(RotatedNode(
                node=node,
                position_label=labels[i] if i < len(labels) else f"Gate {i+1}",
                is_reversed=is_reversed,
                wheel_degree=node_degree
            ))

        return drawn_nodes, wheel_shift_deg, direction

    @staticmethod
    def display_rich(
        drawn_nodes: List[RotatedNode],
        wheel_info: dict,
        wheel_shift: int,
        direction: str,
        entropy_source: str,
        auth_string: str
    ):
        title = f"[bold {wheel_info['color']}]{wheel_info['title']} • {wheel_info['letter']}[/bold {wheel_info['color']}]"
        sub = f"[dim]{wheel_info['sphere']} • Rotation: {wheel_shift}° ({direction})[/dim]"

        table = Table(title=f"{title}\n{sub}", caption=f'Entropy: [bold green]{entropy_source}[/bold green] | Hash: [cyan]{auth_string}[/cyan]')
        table.add_column("Pos", justify="center", style="dim")
        table.add_column("Path / Sphere", style="cyan")
        table.add_column("Arcana Archetype", style="magenta")
        table.add_column("Sefer Yetzirah Attribution", style="yellow")
        table.add_column("Orientation", justify="center")

        for item in drawn_nodes:
            orient_text = "Achor (Reversed)" if item.is_reversed else "Panim (Upright)"
            orient_style = "red" if item.is_reversed else "green"

            table.add_row(
                item.position_label,
                f"{item.wheel_degree}°",
                item.node.tarot_name,
                f"{item.node.kabbalah_path} [dim]({item.node.attribute})[/dim]",
                f"[{orient_style}]{orient_text}[/{orient_style}]"
            )
        console.print(table)
        print()

    @staticmethod
    def display_plain(
        wheel_idx: int,
        total_wheels: int,
        drawn_nodes: List[RotatedNode],
        wheel_info: dict,
        wheel_shift: int,
        direction: str,
        entropy_source: str,
        auth_string: str
    ):
        print(f"[{wheel_idx}/{total_wheels}] {wheel_info['title'].upper()} • {wheel_info['letter']}")
        print(f"    Sphere:    {wheel_info['sphere']}")
        print(f"    Rotation:  {wheel_shift}° | Direction: {direction}")
        print(f"    Entropy:   {entropy_source} | Auth: {auth_string}")
        print("    Draws:")
        for item in drawn_nodes:
            orient = "Achor (Reversed)" if item.is_reversed else "Panim (Upright)"
            print(f"      * {item.position_label:<25} [{item.wheel_degree:>3}°] : {item.node.tarot_name:<18} | {item.node.kabbalah_path} ({item.node.attribute}) -> {orient}")
        print()


# =====================================================================
# 4. Main Application
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Atmospheric Sefer Yetzirah Divination & Word Discovery Engine.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-q', '--query', required=True, help='Your sacred inquiry for the Galgalim.')
    parser.add_argument(
        '-a', '--atziluth',
        action='store_true',
        help='Toggle ON the 4th wheel of Galgal ha-Atziluth (ABYA / 4 Wheels).\nDefault is 3 Wheels (Briah, Yetzirah, Assiah / BYA).'
    )
    parser.add_argument(
        '-n', '--num-cards',
        type=int,
        choices=[1, 3, 10],
        default=3,
        help="Number of nodes drawn per Galgal (1, 3, or 10). Default is 3."
    )
    parser.add_argument(
        '-r', '--reversals',
        action='store_true',
        help='Enable Panim / Achor polarity (Card Reversals).'
    )
    parser.add_argument(
        '-p', '--plain',
        action='store_true',
        help='Force clean plaintext output (easy to copy-paste without borders).'
    )
    parser.add_argument(
        '--offline',
        action='store_true',
        help='Bypass random.org and harvest OS hardware CSPRNG directly.'
    )
    args = parser.parse_args()

    use_rich = RICH_AVAILABLE and not args.plain

    # Configure active wheels (3 by default, 4 if --atziluth is toggled)
    if args.atziluth:
        active_galgalim = [
            {
                "name": "Galgal ha-Atziluth",
                "letter": "Yod (י)",
                "title": "Wheel I: Atziluth (World of Emanation)",
                "sphere": "Primordial Divine Will / Archetypal Fire",
                "color": "bright_red"
            },
            {
                "name": "Galgal ha-Briah",
                "letter": "Heh (ה)",
                "title": "Wheel II: Briah (World of Creation)",
                "sphere": "Upper / Archetypal & Mental Matrix",
                "color": "cyan"
            },
            {
                "name": "Galgal ha-Yetzirah",
                "letter": "Vav (ו)",
                "title": "Wheel III: Yetzirah (World of Formation)",
                "sphere": "Middle / Astral & Formative Matrix",
                "color": "magenta"
            },
            {
                "name": "Galgal ha-Assiah",
                "letter": "Heh (ה)",
                "title": "Wheel IV: Assiah (World of Action)",
                "sphere": "Lower / Material & Concrete Manifestation",
                "color": "yellow"
            }
        ]
        cosmology_mode = "4 Wheels: Atziluth (י) -> Briah (ה) -> Yetzirah (ו) -> Assiah (ה) [ABYA]"
        target_output_type = "4-Letter Tetrad (Tzeruf / Complete Word)"
    else:
        active_galgalim = [
            {
                "name": "Galgal ha-Briah",
                "letter": "Heh (ה)",
                "title": "Wheel I: Briah (World of Creation)",
                "sphere": "Upper / Archetypal & Mental Matrix",
                "color": "cyan"
            },
            {
                "name": "Galgal ha-Yetzirah",
                "letter": "Vav (ו)",
                "title": "Wheel II: Yetzirah (World of Formation)",
                "sphere": "Middle / Astral & Formative Matrix",
                "color": "magenta"
            },
            {
                "name": "Galgal ha-Assiah",
                "letter": "Heh (ה)",
                "title": "Wheel III: Assiah (World of Action)",
                "sphere": "Lower / Material & Concrete Manifestation",
                "color": "yellow"
            }
        ]
        cosmology_mode = "3 Wheels: Briah (ה) -> Yetzirah (ו) -> Assiah (ה) [BYA]"
        target_output_type = "3-Letter Triad (Shoresh / Root Dynamic)"

    total_wheels = len(active_galgalim)

    # Banner
    if use_rich:
        banner = Panel.fit(
            f"[bold yellow]ספר יצירה • The Galgalim of Formation[/bold yellow]\n"
            f"[bold]Inquiry:[/bold] '{args.query}'\n"
            f"[bold cyan]Cosmology:[/bold cyan] {cosmology_mode}\n"
            f"[dim]Harvesting atmospheric entropy from random.org...[/dim]",
            border_style="purple"
        )
        console.print(banner)
        print()
    else:
        print("=" * 80)
        print(f"ספר יצירה • The Galgalim of Formation")
        print(f"Inquiry:   '{args.query}'")
        print(f"Cosmology: {cosmology_mode}")
        print(f"Target:    {target_output_type}")
        print(f"Timestamp: {datetime.now().astimezone().isoformat(timespec='seconds')}")
        print("=" * 80 + "\n")

    wheel_draws: List[List[RotatedNode]] = []
    thesis_letters: List[Tuple[str, str, str, str]] = []
    synthesis_letters: List[Tuple[str, str, str, str]] = []
    major_arcana_reservoir: List[Tuple[str, str, str, str]] = []

    # Spin through active Galgalim
    for wheel_idx, wheel_meta in enumerate(active_galgalim, start=1):
        timestamp = datetime.now().astimezone().isoformat(timespec='seconds')

        # 1. Atmospheric entropy
        atmospheric_bytes, entropy_source = EntropyHarvester.harvest(force_offline=args.offline)

        # 2. Derive cryptographically protected seed
        seed_material = (
            f"{args.query}|{timestamp}|galgal-{wheel_idx}|"
            f"{atmospheric_bytes.hex()}"
        ).encode('utf-8')
        seed = hashlib.sha256(seed_material).digest()

        # 3. Derive 8-character verification hash
        auth_hash = ProtectiveHasher.derive_protected_bytes(seed, b"galgal-auth-seal")
        auth_string = auth_hash.hex()[:8].upper()

        # 4. Spin the Galgal
        engine = GalgalEngine(
            seed=seed,
            atmospheric_entropy=atmospheric_bytes,
            reversals_enabled=args.reversals
        )
        drawn_nodes, wheel_shift, direction = engine.spin_wheel(args.num_cards)
        wheel_draws.append(drawn_nodes)

        # Method 1 Tracker: Primary Rotation Axis (Thesis Node at index 0)
        thesis_node = drawn_nodes[0].node
        t_char, t_desc = extract_representing_letter(thesis_node)
        thesis_letters.append((wheel_meta['title'], wheel_meta['letter'], t_char, thesis_node.tarot_name))

        # Method 2 Tracker: Synthesis Node (Index 2, if at least 3 cards drawn)
        if len(drawn_nodes) >= 3:
            synthesis_node = drawn_nodes[2].node
            s_char, s_desc = extract_representing_letter(synthesis_node)
            synthesis_letters.append((wheel_meta['title'], wheel_meta['letter'], s_char, synthesis_node.tarot_name))

        # Method 3 Tracker: Major Arcana Filter (Check all drawn cards on this wheel)
        for rn in drawn_nodes:
            if rn.node.is_major:
                m_char, _ = extract_representing_letter(rn.node)
                major_arcana_reservoir.append((wheel_meta['title'], rn.position_label, m_char, rn.node.tarot_name))

        # Output Wheel Cards
        if use_rich:
            engine.display_rich(
                drawn_nodes=drawn_nodes,
                wheel_info=wheel_meta,
                wheel_shift=wheel_shift,
                direction=direction,
                entropy_source=entropy_source,
                auth_string=auth_string
            )
        else:
            engine.display_plain(
                wheel_idx=wheel_idx,
                total_wheels=total_wheels,
                drawn_nodes=drawn_nodes,
                wheel_info=wheel_meta,
                wheel_shift=wheel_shift,
                direction=direction,
                entropy_source=entropy_source,
                auth_string=auth_string
            )

    # =====================================================================
    # 5. Automated Word Discovery (The 3 Methods)
    # =====================================================================

    m1_analysis = analyze_letter_sequence([c for _, _, c, _ in thesis_letters])
    m2_analysis = analyze_letter_sequence([c for _, _, c, _ in synthesis_letters]) if synthesis_letters else None
    m3_analysis = analyze_letter_sequence([c for _, _, c, _ in major_arcana_reservoir]) if major_arcana_reservoir else None

    if use_rich:
        summary_panel = Table(title="[bold yellow]Linguistic Word Discovery (Shorashim & Tzerufim)[/bold yellow]")
        summary_panel.add_column("Discovery Method", style="cyan", width=34)
        summary_panel.add_column("Extracted Letters", style="bold green", justify="center")
        summary_panel.add_column("Gematria", style="magenta", justify="center")
        summary_panel.add_column("Discovered Roots & Decoded Meaning", style="yellow")

        # Row 1: Method 1 (Primary Rotation Axis / Thesis)
        m1_details = f"[bold cyan]{m1_analysis['raw_str']}[/bold cyan]"
        m1_matches = []
        if m1_analysis['gematria_desc']:
            m1_matches.append(f"[bold]{m1_analysis['gematria_desc']}[/bold]")
        for word, desc, m_type in m1_analysis['matches']:
            m1_matches.append(f"• {desc} [dim]({m_type})[/dim]")
        if not m1_matches:
            m1_matches.append("[dim]Consonant sequence open for meditation[/dim]")

        summary_panel.add_row(
            "Method 1: Primary Rotation Axis\n[dim](Thesis / Hesed Vector)[/dim]",
            m1_details,
            str(m1_analysis['gematria']),
            "\n".join(m1_matches)
        )

        # Row 2: Method 2 (Synthesis Axis / Outcome)
        if m2_analysis:
            m2_details = f"[bold cyan]{m2_analysis['raw_str']}[/bold cyan]"
            m2_matches = []
            if m2_analysis['gematria_desc']:
                m2_matches.append(f"[bold]{m2_analysis['gematria_desc']}[/bold]")
            for word, desc, m_type in m2_analysis['matches']:
                m2_matches.append(f"• {desc} [dim]({m_type})[/dim]")
            if not m2_matches:
                m2_matches.append("[dim]Outcome sequence open for meditation[/dim]")

            summary_panel.add_row(
                "Method 2: Synthesis Axis\n[dim](Outcome / Tiphareth Vector)[/dim]",
                m2_details,
                str(m2_analysis['gematria']),
                "\n".join(m2_matches)
            )

        # Row 3: Method 3 (Active Foundation Reservoir / Major Arcana Filter)
        if m3_analysis and major_arcana_reservoir:
            m3_details = f"[bold cyan]{m3_analysis['raw_str']}[/bold cyan]"
            m3_matches = []
            if m3_analysis['gematria_desc']:
                m3_matches.append(f"[bold]{m3_analysis['gematria_desc']}[/bold]")
            for word, desc, m_type in m3_analysis['matches']:
                m3_matches.append(f"• {desc} [dim]({m_type})[/dim]")
            if not m3_matches:
                m3_matches.append("[dim]Isolated Foundation Letters[/dim]")

            # Add which cards yielded the letters
            source_cards = ", ".join([f"{c} ({card})" for _, _, c, card in major_arcana_reservoir])
            m3_note = f"[dim]From:[/dim] {source_cards}\n" + "\n".join(m3_matches)

            summary_panel.add_row(
                "Method 3: Foundation Reservoir\n[dim](Major Arcana Filter)[/dim]",
                m3_details,
                str(m3_analysis['gematria']),
                m3_note
            )
        else:
            summary_panel.add_row(
                "Method 3: Foundation Reservoir\n[dim](Major Arcana Filter)[/dim]",
                "[dim]None[/dim]",
                "-",
                "[dim]No Major Arcana drawn in this casting (Elemental flow dominant)[/dim]"
            )

        console.print(summary_panel)
        print()
    else:
        print("=" * 80)
        print("LINGUISTIC WORD DISCOVERY (SHORASHIM & TZERUFIM)")
        print("=" * 80)

        # Method 1
        print("Method 1: Primary Rotation Axis (Thesis / Hesed Vector):")
        print(f"  * Extracted Letters: {m1_analysis['raw_str']}")
        print(f"  * Gematria Value:    {m1_analysis['gematria']}", end="")
        if m1_analysis['gematria_desc']:
            print(f" -> {m1_analysis['gematria_desc']}")
        else:
            print()
        if m1_analysis['matches']:
            print("  * Decoded Roots & Permutations:")
            for word, desc, m_type in m1_analysis['matches']:
                print(f"      - {desc} ({m_type})")
        print()

        # Method 2
        if m2_analysis:
            print("Method 2: The Synthesis Axis (Outcome / Tiphareth Vector):")
            print(f"  * Extracted Letters: {m2_analysis['raw_str']}")
            print(f"  * Gematria Value:    {m2_analysis['gematria']}", end="")
            if m2_analysis['gematria_desc']:
                print(f" -> {m2_analysis['gematria_desc']}")
            else:
                print()
            if m2_analysis['matches']:
                print("  * Decoded Roots & Permutations:")
                for word, desc, m_type in m2_analysis['matches']:
                    print(f"      - {desc} ({m_type})")
            print()

        # Method 3
        print("Method 3: The Active Foundation Reservoir (Major Arcana Filter):")
        if m3_analysis and major_arcana_reservoir:
            print(f"  * Extracted Letters: {m3_analysis['raw_str']}")
            source_cards = ", ".join([f"{c} from {card}" for _, _, c, card in major_arcana_reservoir])
            print(f"  * Source Cards:      {source_cards}")
            print(f"  * Gematria Value:    {m3_analysis['gematria']}", end="")
            if m3_analysis['gematria_desc']:
                print(f" -> {m3_analysis['gematria_desc']}")
            else:
                print()
            if m3_analysis['matches']:
                print("  * Decoded Roots & Permutations:")
                for word, desc, m_type in m3_analysis['matches']:
                    print(f"      - {desc} ({m_type})")
        else:
            print("  * No Major Arcana drawn in this casting (Elemental flow dominant).")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        if RICH_AVAILABLE:
            console.print("\n[bold red]⏹️ Galgal rotation halted.[/bold red]")
        else:
            print("\nGalgal rotation halted.")
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[bold red]An unexpected anomaly occurred: {e}[/bold red]")
        else:
            print(f"An unexpected anomaly occurred: {e}")
