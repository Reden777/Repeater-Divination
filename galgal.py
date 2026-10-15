#!/usr/bin/env python3
"""
GALGALIM3.py
Atmospheric Sefer Yetzirah Divination Engine.
Simulates the 3 Concentric Galgalim (Wheels of Formation) across the Three Worlds:
  1. Galgal ha-Briah   (Mental / Creation)
  2. Galgal ha-Yetzirah (Astral / Formation)
  3. Galgal ha-Assiah   (Physical / Manifestation)

Randomness is harvested directly from atmospheric radio noise via random.org's
HTTP API, with graceful, zero-latency fallback to cryptographic OS entropy.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import hashlib
import sys
import os
import argparse
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

THE_THREE_GALGALIM = [
    {
        "name": "Galgal ha-Briah",
        "title": "Wheel I: Briah (World of Creation)",
        "sphere": "Upper / Archetypal & Mental Sphere",
        "color": "cyan"
    },
    {
        "name": "Galgal ha-Yetzirah",
        "title": "Wheel II: Yetzirah (World of Formation)",
        "sphere": "Middle / Astral & Formative Matrix",
        "color": "magenta"
    },
    {
        "name": "Galgal ha-Assiah",
        "title": "Wheel III: Assiah (World of Action)",
        "sphere": "Lower / Material & Concrete Reality",
        "color": "yellow"
    }
]


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
    is_reversed: bool          # In Sefer Yetzirah: Panim (Direct) vs Achor (Reversed)
    wheel_degree: int          # Position on the 360-degree perimeter


class GalgalWheel:
    """Represents a circular wheel of 78 archetypes ready for rotation."""
    def __init__(self):
        self.nodes: List[GalgalNode] = self._build_wheel()

    def _build_wheel(self) -> List[GalgalNode]:
        nodes = []
        # 1. 22 Foundation Letters (Major Arcana Paths)
        for path_num, letter, attr, tarot in HEBREW_PATHS:
            nodes.append(GalgalNode(
                tarot_name=tarot,
                kabbalah_path=f"{path_num} • {letter}",
                attribute=attr,
                is_major=True
            ))

        # 2. 40 Sephirotic Decanates (Pip Cards 1-10 across 4 Elements)
        for seph_idx, (seph_name, seph_attr) in enumerate(SEPHIROT):
            rank_name = "Ace" if seph_idx == 0 else str(seph_idx + 1)
            for suit_world, suit_name in WORLDS_SUITS:
                nodes.append(GalgalNode(
                    tarot_name=f"{rank_name} of {suit_name}",
                    kabbalah_path=f"{seph_name} in {suit_world}",
                    attribute=seph_attr,
                    is_major=False
                ))

        # 3. 16 Court Nodes (Princes, Queens, Kings, Pages)
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
# 2. Atmospheric & Cryptographic Entropy Engine
# =====================================================================

class EntropyHarvester:
    """
    Fetches true atmospheric quantum/radio noise from random.org's HTTP API.
    Gracefully falls back to OS CSPRNG (os.urandom) upon network issues or rate limits.
    """
    RANDOM_ORG_URL = "https://www.random.org/integers/?num=32&min=0&max=255&col=1&base=10&format=plain&rnd=new"
    USER_AGENT = "GalgalimTarot/3.0 (Atmospheric Sefer Yetzirah Engine)"

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
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception):
                pass  # Silent transition to OS randomness

        # Fallback to local cryptographic entropy
        return os.urandom(32), "OS CSPRNG (local urandom fallback)"


class ProtectiveHasher:
    """PBKDF2-HMAC cryptographic hardening layer with 888,888 rounds."""
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


# =====================================================================
# 3. Galgal Rotation & Reading Logic
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
        """
        Rotates the Galgal according to atmospheric entropy.
        Computes the rotation angle and returns the extracted Gates/Cards.
        """
        available_nodes = self.wheel.nodes.copy()
        drawn_nodes: List[RotatedNode] = []
        labels = self.POSITION_LABELS.get(num_draws, [f"Gate {i+1}" for i in range(num_draws)])

        # Calculate base rotation offset from atmospheric entropy
        base_rotation_raw = int.from_bytes(self.atmospheric_entropy[:4], 'big')
        wheel_shift_deg = (base_rotation_raw % 360)
        direction = "Panim (Face / Direct)" if (base_rotation_raw % 2 == 0) else "Achor (Back / Retrograde)"

        for i in range(num_draws):
            if not available_nodes:
                break

            # Combine atmospheric seed + PBKDF2 salt for draw index
            draw_salt = f"galgal-spin-gate-{i}"
            draw_idx = hash_for_int(self.seed, draw_salt) % len(available_nodes)
            node = available_nodes.pop(draw_idx)

            # Determine Panim (Upright) vs Achor (Reversed)
            is_reversed = False
            if self.reversals_enabled:
                reversal_salt = f"galgal-reversal-{i}"
                is_reversed = (hash_for_int(self.seed, reversal_salt) % 2) == 1

            # Approximate degree position on wheel perimeter (0 - 359°)
            node_degree = (wheel_shift_deg + int((i / num_draws) * 360)) % 360

            drawn_nodes.append(RotatedNode(
                node=node,
                position_label=labels[i] if i < len(labels) else f"Gate {i+1}",
                is_reversed=is_reversed,
                wheel_degree=node_degree
            ))

        return drawn_nodes, wheel_shift_deg, direction

    @staticmethod
    def display_galgal_reading(
        drawn_nodes: List[RotatedNode],
        wheel_info: dict,
        wheel_shift: int,
        direction: str,
        entropy_source: str,
        auth_string: str,
        query: str
    ):
        if RICH_AVAILABLE:
            title = f"[bold {wheel_info['color']}]{wheel_info['title']}[/bold {wheel_info['color']}]"
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
        else:
            print(f"=== {wheel_info['title']} ===")
            print(f"Sphere:   {wheel_info['sphere']}")
            print(f"Rotation: {wheel_shift}° ({direction})")
            print(f"Entropy:  {entropy_source}")
            print(f"Auth:     {auth_string}")
            print("-" * 75)
            for item in drawn_nodes:
                orient = "Achor (Reversed)" if item.is_reversed else "Panim (Upright)"
                print(f"{item.position_label} [{item.wheel_degree}°]: {item.node.tarot_name} | {item.node.kabbalah_path} ({item.node.attribute}) -> {orient}")
            print("\n")


# =====================================================================
# 4. Main Application
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Sefer Yetzirah Three Galgalim Divination Engine using random.org atmospheric noise.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-q', '--query', required=True, help='Your sacred inquiry for the 3 Galgalim.')
    parser.add_argument(
        '-n', '--num-cards',
        type=int,
        choices=[1, 3, 10],
        default=3,
        help="Number of paths/nodes drawn per Galgal wheel (1, 3, or 10). Default is 3."
    )
    parser.add_argument(
        '-r', '--reversals',
        action='store_true',
        help='Enable Panim / Achor polarity (Card Reversals).'
    )
    parser.add_argument(
        '--offline',
        action='store_true',
        help='Bypass random.org and use OS hardware CSPRNG directly.'
    )
    args = parser.parse_args()

    # Introduction Banner
    if RICH_AVAILABLE:
        banner = Panel.fit(
            f"[bold yellow]ספר יצירה • The 3 Galgalim of Formation[/bold yellow]\n"
            f"[bold]Inquiry:[/bold] '{args.query}'\n"
            f"[dim]Initiating atmospheric rotation of Briah, Yetzirah, and Assiah...[/dim]",
            border_style="purple"
        )
        console.print(banner)
        print()
    else:
        print("=====================================================================")
        print(f"ספר יצירה • The 3 Galgalim of Formation")
        print(f"Inquiry: '{args.query}'")
        print("Rotating Wheels of Briah, Yetzirah, and Assiah...")
        print("=====================================================================\n")

    # Rotate through the 3 Concentric Galgalim
    for wheel_idx, wheel_meta in enumerate(THE_THREE_GALGALIM, start=1):
        timestamp = datetime.now().astimezone().isoformat(timespec='seconds')

        # 1. Harvest atmospheric noise (or fallback)
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

        # 4. Spin the Galgal and draw nodes
        engine = GalgalEngine(
            seed=seed,
            atmospheric_entropy=atmospheric_bytes,
            reversals_enabled=args.reversals
        )
        drawn_nodes, wheel_shift, direction = engine.spin_wheel(args.num_cards)

        # 5. Output reading
        engine.display_galgal_reading(
            drawn_nodes=drawn_nodes,
            wheel_info=wheel_meta,
            wheel_shift=wheel_shift,
            direction=direction,
            entropy_source=entropy_source,
            auth_string=auth_string,
            query=args.query
        )


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
