#!/usr/bin/env python3
"""
golden_dawn_geomancy.py — Hermetic Order of the Golden Dawn Astrological Geomancy
Entropy Source: Atmospheric radio static via Random.org (16 binary taps).
Maps the 4 Mothers, 4 Daughters, 4 Nephews into the 12 Astrological Houses,
and derives the Two Witnesses, the Supreme Judge, and the Reconciler.
"""

import sys
import argparse
import urllib.request
import hashlib
from typing import List, Tuple, Dict
from rich.console import Console
from rich.table import Table

console = Console()

# === GOLDEN DAWN GEOMANTIC DATABASE ===

GEOMANTIC_FIGURES = {
    (1, 1, 1, 1): {"name": "Via", "english": "The Way", "planet": "Moon (☽)", "zodiac": "Cancer (♋)", "element": "Water", "spirit": "Chasmodai", "quality": "Neutral/Changing"},
    (2, 2, 2, 2): {"name": "Populus", "english": "The People", "planet": "Moon (☽)", "zodiac": "Cancer (♋)", "element": "Water", "spirit": "Chasmodai", "quality": "Neutral/Crowd"},
    (1, 2, 1, 2): {"name": "Conjunctio", "english": "Conjunction", "planet": "Mercury (☿)", "zodiac": "Virgo (♍)", "element": "Earth", "spirit": "Taphthartharath", "quality": "Good with Good, Bad with Bad"},
    (2, 1, 2, 1): {"name": "Carcer", "english": "The Prison", "planet": "Saturn (♄)", "zodiac": "Capricorn (♑)", "element": "Earth", "spirit": "Zazel", "quality": "Binding/Delay/Severe"},
    (1, 1, 2, 2): {"name": "Fortuna Major", "english": "Greater Fortune", "planet": "Sun (☉)", "zodiac": "Leo (♌)", "element": "Fire", "spirit": "Sorath", "quality": "Highly Favorable/Success"},
    (2, 2, 1, 1): {"name": "Fortuna Minor", "english": "Lesser Fortune", "planet": "Sun (☉)", "zodiac": "Leo (♌)", "element": "Fire", "spirit": "Sorath", "quality": "Quick Success/External Aid"},
    (1, 2, 2, 1): {"name": "Acquisitio", "english": "Gain / Success", "planet": "Jupiter (♃)", "zodiac": "Sagittarius (♐)", "element": "Fire", "spirit": "Hismael", "quality": "Very Fortunate/Abundance"},
    (2, 1, 1, 2): {"name": "Amissio", "english": "Loss / Release", "planet": "Venus (♀)", "zodiac": "Taurus (♉)", "element": "Earth", "spirit": "Kedemel", "quality": "Loss in Wealth / Good in Love"},
    (2, 1, 2, 2): {"name": "Laetitia", "english": "Joy / Gladness", "planet": "Jupiter (♃)", "zodiac": "Pisces (♓)", "element": "Water", "spirit": "Hismael", "quality": "Very Favorable/Health/Praise"},
    (2, 2, 1, 2): {"name": "Tristitia", "english": "Sorrow / Grief", "planet": "Saturn (♄)", "zodiac": "Aquarius (♒)", "element": "Air", "spirit": "Zazel", "quality": "Unfavorable/Melancholy"},
    (1, 1, 2, 1): {"name": "Puella", "english": "The Girl", "planet": "Venus (♀)", "zodiac": "Libra (♎)", "element": "Air", "spirit": "Kedemel", "quality": "Good in Love/Short-term Joy"},
    (1, 2, 1, 1): {"name": "Puer", "english": "The Boy", "planet": "Mars (♂)", "zodiac": "Aries (♈)", "element": "Fire", "spirit": "Bartzabel", "quality": "Impulsive/Aggressive/Conflict"},
    (2, 1, 1, 1): {"name": "Rubeus", "english": "Red / Passion", "planet": "Mars (♂)", "zodiac": "Scorpio (♏)", "element": "Water", "spirit": "Bartzabel", "quality": "Deceit/Violence/Toxicity"},
    (1, 1, 1, 2): {"name": "Albus", "english": "White / Wisdom", "planet": "Mercury (☿)", "zodiac": "Gemini (♊)", "element": "Air", "spirit": "Taphthartharath", "quality": "Favorable/Clear Intellect"},
    (1, 2, 2, 2): {"name": "Caput Draconis", "english": "Dragon's Head", "planet": "North Node (☊)", "zodiac": "Earth", "element": "Earth", "spirit": "Iophiel", "quality": "Entrance/Expansion/Favorable"},
    (2, 2, 2, 1): {"name": "Cauda Draconis", "english": "Dragon's Tail", "planet": "South Node (☋)", "zodiac": "Fire", "element": "Fire", "spirit": "Zadkiel", "quality": "Exit/Severing/End of Matter"}
}

HOUSES = [
    "1st House: The Querent, Health, Vitality, Beginning",
    "2nd House: Money, Wealth, Resources, Possessions",
    "3rd House: Communication, Siblings, Short Journeys",
    "4th House: Home, Real Estate, Family, The End of Matter",
    "5th House: Pleasures, Children, Risk, Creativity",
    "6th House: Illness, Work Environment, Service, Debts",
    "7th House: Relationships, Marriage, Contracts, Open Enemies",
    "8th House: Death, Transformation, Inheritance, Hidden Debt",
    "9th House: Long Journeys, Philosophy, Higher Studies",
    "10th House: Career, Ambition, Honor, Reputation, Authority",
    "11th House: Friends, Community, Wishes, Hopes",
    "12th House: Secret Enemies, Self-Undoing, Fears, Confinement"
]


# === ENTROPY & MATH ===

def get_random_org_pool(num_integers: int = 64) -> List[int]:
    url = (f"https://www.random.org/integers/?num={num_integers}"
           f"&min=0&max=255&col=1&base=10&format=plain&rnd=new")
    headers = {'User-Agent': 'GoldenDawn-Geomancy/1.0'}
    req = urllib.request.Request(url, headers=headers)
    try:
        response = urllib.request.urlopen(req)
        data = response.read().decode('utf-8').strip()
        return [int(x) for x in data.split('\n') if x.strip()]
    except Exception as e:
        console.print(f"[bold red]Entropy Fetch Error ({e}); using local cryptographic fallback.[/bold red]")
        import secrets
        return [secrets.randbelow(256) for _ in range(num_integers)]


def add_lines(a: int, b: int) -> int:
    """Golden Dawn Modulo-2 Addition: Odd+Odd=Even(2), Odd+Even=Odd(1), Even+Even=Even(2)"""
    return 2 if (a + b) % 2 == 0 else 1


def add_figures(fig1: Tuple[int, int, int, int], fig2: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
    return tuple(add_lines(fig1[i], fig2[i]) for i in range(4))


def format_figure_dots(fig: Tuple[int, int, int, int]) -> str:
    lines = []
    for line in fig:
        lines.append(" • " if line == 1 else "•• ")
    return " | ".join(lines)


# === MAIN CALCULATION ENGINE ===

def cast_geomancy():
    pool = get_random_org_pool(64)
    auth_bytes = bytes([pool.pop() for _ in range(16)])
    auth_hash = hashlib.sha256(auth_bytes).hexdigest()[:8].upper()

    # Step 1: Draw the 4 Mothers (16 lines of entropy)
    mothers = []
    for _ in range(4):
        lines = []
        for _ in range(4):
            val = pool.pop()
            lines.append(1 if val % 2 != 0 else 2)
        mothers.append(tuple(lines))

    # Step 2: Form the 4 Daughters (Reading horizontally across the Mothers)
    daughters = []
    for line_idx in range(4):
        daughters.append((mothers[0][line_idx], mothers[1][line_idx], mothers[2][line_idx], mothers[3][line_idx]))

    # Step 3: Form the 4 Nephews (Addition of pairs)
    nephews = [
        add_figures(mothers[0], mothers[1]),      # 9th: Mother 1 + Mother 2
        add_figures(mothers[2], mothers[3]),      # 10th: Mother 3 + Mother 4
        add_figures(daughters[0], daughters[1]),  # 11th: Daughter 1 + Daughter 2
        add_figures(daughters[2], daughters[3])   # 12th: Daughter 3 + Daughter 4
    ]

    # The 12 Astrological Houses (Mothers 1-4, Daughters 1-4, Nephews 1-4)
    houses = mothers + daughters + nephews

    # Step 4: The Witnesses (13 & 14)
    right_witness = add_figures(nephews[0], nephews[1])  # 9 + 10 (The Querent's Past/State)
    left_witness = add_figures(nephews[2], nephews[3])   # 11 + 12 (The Future/Environment)

    # Step 5: The Supreme Judge (15)
    judge = add_figures(right_witness, left_witness)

    # Step 6: The Reconciler (16)
    reconciler = add_figures(judge, mothers[0])

    return auth_hash, houses, right_witness, left_witness, judge, reconciler


# === CLI & DISPLAY ===

def main():
    parser = argparse.ArgumentParser(description="Golden Dawn Astrological Geomancy Divination Engine")
    parser.add_argument('-q', '--query', required=True, help="Your sacred divination question.")
    args = parser.parse_args()

    auth_hash, houses, rw, lw, judge, reconciler = cast_geomancy()

    console.print(f"\n[bold gold1]✦ THE HERMETIC ORDER OF THE GOLDEN DAWN ✦[/bold gold1]")
    console.print(f"[bold white]Geomantic Oracle for:[/bold white] '[bold italic]{args.query}[/bold italic]'")
    console.print(f"[dim]Atmospheric Auth Hash:[/dim] [bold cyan]{auth_hash}[/bold cyan]\n")

    # Table of the 12 Houses
    table = Table(title="The Twelve Astrological Houses", show_header=True, header_style="bold magenta")
    table.add_column("House / Life Sphere", style="dim", width=45)
    table.add_column("Figure", style="bold yellow")
    table.add_column("Dots", style="bold green")
    table.add_column("Astrology / Spirit", style="cyan")

    for i, fig in enumerate(houses):
        data = GEOMANTIC_FIGURES[fig]
        dots = format_figure_dots(fig)
        table.add_row(HOUSES[i], f"{data['name']} ({data['english']})", dots, f"{data['planet']} {data['zodiac']} | {data['spirit']}")

    console.print(table)

    # The Final Court (Witnesses, Judge, Reconciler)
    rw_data = GEOMANTIC_FIGURES[rw]
    lw_data = GEOMANTIC_FIGURES[lw]
    j_data = GEOMANTIC_FIGURES[judge]
    rec_data = GEOMANTIC_FIGURES[reconciler]

    console.print("\n[bold magenta]════════════════ THE COURT OF THE JUDGE ════════════════[/bold magenta]")
    console.print(f"[bold]Right Witness (The Querent's Current/Past Energy):[/bold]")
    console.print(f"  [yellow]{rw_data['name']}[/yellow] ({rw_data['english']}) [{format_figure_dots(rw)}] | {rw_data['planet']} — [dim]{rw_data['quality']}[/dim]")

    console.print(f"\n[bold]Left Witness (The External World / Future Force):[/bold]")
    console.print(f"  [yellow]{lw_data['name']}[/yellow] ({lw_data['english']}) [{format_figure_dots(lw)}] | {lw_data['planet']} — [dim]{lw_data['quality']}[/dim]")

    console.print(f"\n[bold green]⚡ THE SUPREME JUDGE (The Final Verdict): ⚡[/bold green]")
    console.print(f"  [bold red]{j_data['name']}[/bold red] ({j_data['english']}) [{format_figure_dots(judge)}]")
    console.print(f"  [cyan]Ruling Planet:[/cyan] {j_data['planet']} | [cyan]Zodiac:[/cyan] {j_data['zodiac']} | [cyan]Spirit:[/cyan] [bold]{j_data['spirit']}[/bold]")
    console.print(f"  [bold white]Judgment:[/bold white] {j_data['quality']}")

    console.print(f"\n[dim]The Reconciler (Synthesizing Judge with 1st House): {rec_data['name']} ({rec_data['english']})[/dim]\n")

if __name__ == "__main__":
    main()
