#!/usr/bin/env python3
"""
GALGAL4.py
Atmospheric Sefer Yetzirah Divination Engine across the Four Worlds (ABYA):
  1. Galgal ha-Atziluth (Emanation / Divine Will / Yod י)
  2. Galgal ha-Briah    (Creation / Mind / Heh ה)
  3. Galgal ha-Yetzirah (Formation / Astral / Vav ו)
  4. Galgal ha-Assiah   (Action / Matter / Heh final ה)

Uses random.org's unauthenticated HTTP API for atmospheric entropy
with local OS CSPRNG fallback, PBKDF2 cryptographic hardening,
and a clean, copy-pasteable plain-text UI mode.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import hashlib
import os
import re
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

THE_FOUR_GALGALIM = [
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
# 2. Entropy Engine & Cryptographic Hardening
# =====================================================================

class EntropyHarvester:
    RANDOM_ORG_URL = "https://www.random.org/integers/?num=32&min=0&max=255&col=1&base=10&format=plain&rnd=new"
    USER_AGENT = "GalgalimTarot/4.0 (Atmospheric Sefer Yetzirah Engine)"

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
                pass  # Fallback to local cryptographic entropy

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
    """Extracts the Hebrew character and description for the representing letter."""
    if node.is_major:
        m = re.search(r"\(([\u0590-\u05FF])\)", node.kabbalah_path)
        char = m.group(1) if m else "?"
        letter_name = node.kabbalah_path.split("•")[-1].strip()
        return char, f"Path Letter {letter_name}"
    else:
        # Map Minors to the Tetragrammaton letter of their Suit/World
        for suit_world, suit_name in WORLDS_SUITS:
            if suit_name in node.tarot_name or suit_world in node.kabbalah_path:
                if "Atziluth" in suit_world:
                    return "י", "Yod (י) of Atziluth / Wands"
                elif "Briah" in suit_world:
                    return "ה", "Heh (ה) of Briah / Cups"
                elif "Yetzirah" in suit_world:
                    return "ו", "Vav (ו) of Yetzirah / Swords"
                elif "Assiah" in suit_world:
                    return "ה", "Heh (ה) of Assiah / Pentacles"
        return "?", "Sephirah"


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
                is_reversed = (hash_for_int(self.seed, reversal_salt) % 2) == 1

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
        drawn_nodes: List[RotatedNode],
        wheel_info: dict,
        wheel_shift: int,
        direction: str,
        entropy_source: str,
        auth_string: str
    ):
        print(f"[{wheel_idx}/4] {wheel_info['title'].upper()} • {wheel_info['letter']}")
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
        description="Atmospheric Sefer Yetzirah 4-Galgalim Engine (Atziluth, Briah, Yetzirah, Assiah).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-q', '--query', required=True, help='Your sacred inquiry for the 4 Galgalim.')
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

    # Banner
    if use_rich:
        banner = Panel.fit(
            f"[bold yellow]ספר יצירה • The 4 Galgalim of Formation (ABYA)[/bold yellow]\n"
            f"[bold]Inquiry:[/bold] '{args.query}'\n"
            f"[dim]Rotating the Wheels of Atziluth (י), Briah (ה), Yetzirah (ו), and Assiah (ה)...[/dim]",
            border_style="purple"
        )
        console.print(banner)
        print()
    else:
        print("=" * 80)
        print(f"ספר יצירה • The 4 Galgalim of Formation (ABYA)")
        print(f"Inquiry:   '{args.query}'")
        print(f"Worlds:    Atziluth (י) -> Briah (ה) -> Yetzirah (ו) -> Assiah (ה)")
        print(f"Timestamp: {datetime.now().astimezone().isoformat(timespec='seconds')}")
        print("=" * 80 + "\n")

    representing_letters: List[Tuple[str, str, str, str]] = []

    # Spin through all 4 Galgalim
    for wheel_idx, wheel_meta in enumerate(THE_FOUR_GALGALIM, start=1):
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

        # Track the primary pointer letter (Thesis position at rotation angle)
        primary_node = drawn_nodes[0].node
        letter_char, letter_desc = extract_representing_letter(primary_node)
        representing_letters.append((wheel_meta['title'], wheel_meta['letter'], letter_char, letter_desc))

        # 5. Output
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
                drawn_nodes=drawn_nodes,
                wheel_info=wheel_meta,
                wheel_shift=wheel_shift,
                direction=direction,
                entropy_source=entropy_source,
                auth_string=auth_string
            )

    # Summary: The Constructed 4-Letter Word / Tetrad
    word_str = " - ".join([char for _, _, char, _ in representing_letters])
    
    if use_rich:
        summary_table = Table(title="[bold yellow]The 4 Representing Letters (Primary Rotation Axis)[/bold yellow]")
        summary_table.add_column("World", style="cyan")
        summary_table.add_column("Tetragrammaton", style="magenta", justify="center")
        summary_table.add_column("Drawn Letter", style="bold green", justify="center")
        summary_table.add_column("Attribution", style="yellow")

        for world_title, tetra_char, char, desc in representing_letters:
            summary_table.add_row(world_title, tetra_char, char, desc)

        console.print(summary_table)
        console.print(f"\n[bold]Constructed 4-Letter Tetrad:[/bold] [bold cyan]{word_str}[/bold cyan]\n")
    else:
        print("=" * 80)
        print("THE 4 REPRESENTING LETTERS (Primary Rotation Axis / Thesis):")
        for world_title, tetra_char, char, desc in representing_letters:
            print(f"  * {world_title:<38} [{tetra_char}] -> {char} ({desc})")
        print(f"\nConstructed 4-Letter Tetrad: {word_str}")
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
