#!/usr/bin/env python3
"""
8rand.py / swizzler_oracle.py
Temporal Entropy Oracle with Hebrew Alphabet and Punctuation Doodles.

Modes:
  1. no-punct:   Pure unpunctuated Hebrew letters.
  2. punctuated: Punctuated letters (doodles combined on/in the letter).
  3. separate:   Unpunctuated letters + bare punctuation symbols next to them.

Entropy Sources:
  - Random.org unauthenticated HTTP GET plain-text API (atmospheric noise).
  - OS-level CSPRNG (os.urandom) zero-downtime fallback.
  - Nanosecond CPU timing jitter distillation via BLAKE2b cryptographic pool.
"""

import os
import sys
import time
import struct
import random
import argparse
import urllib.request
import urllib.error
import hashlib
from typing import List, Tuple, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# ==============================================================================
# 1. HEBREW ALPHABET (22 Foundational Letters + Optional Sofit Forms)
# ==============================================================================
HEBREW_LETTERS_BASE: List[Tuple[str, str, str]] = [
    ("א", "Alef", "U+05D0"),
    ("ב", "Bet", "U+05D1"),
    ("ג", "Gimel", "U+05D2"),
    ("ד", "Dalet", "U+05D3"),
    ("ה", "He", "U+05D4"),
    ("ו", "Vav", "U+05D5"),
    ("ז", "Zayin", "U+05D6"),
    ("ח", "Het", "U+05D7"),
    ("ט", "Tet", "U+05D8"),
    ("י", "Yod", "U+05D9"),
    ("כ", "Kaf", "U+05DB"),
    ("ל", "Lamed", "U+05DC"),
    ("מ", "Mem", "U+05DE"),
    ("נ", "Nun", "U+05E0"),
    ("ס", "Samekh", "U+05E1"),
    ("ע", "Ayin", "U+05E2"),
    ("פ", "Pe", "U+05E4"),
    ("צ", "Tsadi", "U+05E6"),
    ("ק", "Qof", "U+05E7"),
    ("ר", "Resh", "U+05E8"),
    ("ש", "Shin", "U+05E9"),
    ("ת", "Tav", "U+05EA"),
]

HEBREW_LETTERS_SOFIT: List[Tuple[str, str, str]] = [
    ("ך", "Final Kaf", "U+05DA"),
    ("ם", "Final Mem", "U+05DD"),
    ("ן", "Final Nun", "U+05DF"),
    ("ף", "Final Pe", "U+05E3"),
    ("ץ", "Final Tsadi", "U+05E5"),
]

# ==============================================================================
# 2. HEBREW PUNCTUATION DOODLES & MARKS (Cantillation, Niqqud, Punctuation)
# ==============================================================================
HEBREW_DOODLES: List[Tuple[str, str, str, str, str]] = [
    # (Char, Name, Category, Standalone Display, Unicode)
    # --- Cantillation Tropes ("Doodles", Squiggles, Crowns, Horns) ---
    ("\u0591", "Etnahta", "cantillation", "◌֑", "U+0591"),
    ("\u0592", "Segolta", "cantillation", "◌֒", "U+0592"),
    ("\u0593", "Shalshelet", "cantillation", "◌֓", "U+0593"),      # Triple zigzag doodle
    ("\u0594", "Zaqef Qatan", "cantillation", "◌֔", "U+0594"),
    ("\u0595", "Zaqef Gadol", "cantillation", "◌֕", "U+0595"),
    ("\u0596", "Tipeha", "cantillation", "◌֖", "U+0596"),
    ("\u0597", "Revia", "cantillation", "◌֗", "U+0597"),
    ("\u0598", "Zarqa", "cantillation", "◌֘", "U+0598"),          # Hook doodle
    ("\u0599", "Pashta", "cantillation", "◌֙", "U+0599"),
    ("\u059A", "Yetiv", "cantillation", "◌֚", "U+059A"),
    ("\u059B", "Tevir", "cantillation", "◌֛", "U+059B"),
    ("\u059C", "Geresh", "cantillation", "◌֜", "U+059C"),
    ("\u059D", "Geresh Muqdam", "cantillation", "◌֝", "U+059D"),
    ("\u059E", "Gershayim", "cantillation", "◌֞", "U+059E"),
    ("\u059F", "Qarney Para", "cantillation", "◌֟", "U+059F"),    # Cow horns doodle
    ("\u05A0", "Telisha Gedola", "cantillation", "◌֠", "U+05A0"),  # Circle on stem
    ("\u05A1", "Pazer", "cantillation", "◌֡", "U+05A1"),          # Wavy doodle
    ("\u05A2", "Atnah Hafukh", "cantillation", "◌֢", "U+05A2"),
    ("\u05A3", "Munah", "cantillation", "◌֣", "U+05A3"),
    ("\u05A4", "Mahapakh", "cantillation", "◌֤", "U+05A4"),
    ("\u05A5", "Merkha", "cantillation", "◌֥", "U+05A5"),
    ("\u05A6", "Merkha Khefula", "cantillation", "◌֦", "U+05A6"),
    ("\u05A7", "Darga", "cantillation", "◌֧", "U+05A7"),           # S-curve doodle
    ("\u05A8", "Qadma", "cantillation", "◌֨", "U+05A8"),
    ("\u05A9", "Telisha Qetana", "cantillation", "◌֩", "U+05A9"),
    ("\u05AA", "Yerah Ben Yomo", "cantillation", "◌֪", "U+05AA"),  # Horseshoe doodle
    ("\u05AB", "Ole", "cantillation", "◌֫", "U+05AB"),
    ("\u05AC", "Iluy", "cantillation", "◌", "U+05AC"),
    ("\u05AD", "Dehi", "cantillation", "◌", "U+05AD"),
    ("\u05AE", "Zinor", "cantillation", "◌֮", "U+05AE"),          # Tilde / wave doodle

    # --- Niqqud (Vowels & Points) ---
    ("\u05B0", "Sheva", "niqqud", "◌ְ", "U+05B0"),
    ("\u05B1", "Hataf Segol", "niqqud", "◌ֱ", "U+05B1"),
    ("\u05B2", "Hataf Patah", "niqqud", "◌ֲ", "U+05B2"),
    ("\u05B3", "Hataf Qamats", "niqqud", "◌ֳ", "U+05B3"),
    ("\u05B4", "Hiriq", "niqqud", "◌ִ", "U+05B4"),
    ("\u05B5", "Tsere", "niqqud", "◌ֵ", "U+05B5"),
    ("\u05B6", "Segol", "niqqud", "◌ֶ", "U+05B6"),
    ("\u05B7", "Patah", "niqqud", "◌ַ", "U+05B7"),
    ("\u05B8", "Qamats", "niqqud", "◌ָ", "U+05B8"),
    ("\u05B9", "Holam", "niqqud", "◌ֹ", "U+05B9"),
    ("\u05BA", "Holam Haser", "niqqud", "◌ֺ", "U+05BA"),
    ("\u05BB", "Qubuts", "niqqud", "◌ֻ", "U+05BB"),
    ("\u05BC", "Dagesh / Mappiq", "niqqud", "◌ּ", "U+05BC"),
    ("\u05BD", "Meteg", "niqqud", "◌ֽ", "U+05BD"),
    ("\u05BF", "Rafe", "niqqud", "◌ֿ", "U+05BF"),
    ("\u05C1", "Shin Dot", "niqqud", "◌ׁ", "U+05C1"),
    ("\u05C2", "Sin Dot", "niqqud", "◌ׂ", "U+05C2"),
    ("\u05C7", "Qamats Qatan", "niqqud", "◌ׇ", "U+05C7"),

    # --- Punctuation Symbols ---
    ("\u05BE", "Maqaf (Hyphen)", "punctuation", "־", "U+05BE"),
    ("\u05C0", "Paseq (Divider)", "punctuation", "׀", "U+05C0"),
    ("\u05C3", "Sof Pasuq (Colon/Period)", "punctuation", "׃", "U+05C3"),
    ("\u05C6", "Nun Hafukha (Inverted)", "punctuation", "׆", "U+05C6"),
    ("\u05F3", "Geresh (Abbreviation)", "punctuation", "׳", "U+05F3"),
    ("\u05F4", "Gershayim (Acronym)", "punctuation", "״", "U+05F4"),
]

# ==============================================================================
# 3. MULTI-SOURCE ENTROPY HARVESTER
# ==============================================================================
def fetch_atmospheric_noise(num_bytes: int = 32, timeout: float = 3.0) -> bytes:
    """
    Fetches raw atmospheric noise bytes from Random.org's unauthenticated HTTP API.
    """
    url = f"https://www.random.org/integers/?num={num_bytes}&min=0&max=255&col=1&base=10&format=plain&rnd=new"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'SwizzlerOracleHebrew/2.0 (Temporal Entropy Harvester)'}
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP status {response.status}")
        body = response.read().decode('utf-8').strip()
        if body.startswith("Error:"):
            raise RuntimeError(body)
        raw_ints = [int(line.strip()) & 0xFF for line in body.split() if line.strip().isdigit()]
        if len(raw_ints) < num_bytes:
            raise RuntimeError("Truncated response from Random.org")
        return bytes(raw_ints[:num_bytes])

def harvest_entropy_block(
    num_bytes: int = 32,
    mode: str = "auto",
    timeout: float = 3.0
) -> Tuple[bytes, bytes, int, str]:
    """
    Harvests multi-stream entropy:
      1. Atmospheric noise (Random.org unauthenticated API)
      2. OS kernel CSPRNG (os.urandom)
      3. Nanosecond CPU timing jitter
    Returns:
      (atmospheric_bytes, os_bytes, timing_ns, source_description)
    """
    t_start = time.perf_counter_ns()
    os_bytes = os.urandom(num_bytes)
    source_desc = ""
    atm_bytes = b""

    if mode == "os":
        timing_ns = time.perf_counter_ns() - t_start
        return b"", os_bytes, timing_ns, f"os.urandom ({num_bytes}B)"

    if mode == "random.org":
        atm_bytes = fetch_atmospheric_noise(num_bytes=num_bytes, timeout=timeout)
        timing_ns = time.perf_counter_ns() - t_start
        return atm_bytes, os_bytes, timing_ns, f"random.org ({num_bytes}B)"

    # Default 'auto': Try Random.org, cleanly fall back to os.urandom
    try:
        atm_bytes = fetch_atmospheric_noise(num_bytes=num_bytes, timeout=timeout)
        timing_ns = time.perf_counter_ns() - t_start
        source_desc = f"random.org + os ({num_bytes}B)"
    except Exception:
        timing_ns = time.perf_counter_ns() - t_start
        atm_bytes = b""
        source_desc = f"os.urandom fallback ({num_bytes}B)"

    return atm_bytes, os_bytes, timing_ns, source_desc

def swizzle_entropy_pool(
    atm_bytes: bytes,
    os_bytes: bytes,
    step: int,
    timing_ns: int,
    prev_state: bytes,
    query_seed: bytes
) -> bytes:
    """
    Cryptographically distills and swizzles all entropy sources using BLAKE2b (256-bit).
    Mixes atmospheric noise, OS entropy, nanosecond clocks, query seed, and state chain.
    """
    hasher = hashlib.blake2b(digest_size=32, key=query_seed[:32])
    hasher.update(atm_bytes)
    hasher.update(os_bytes)
    # Pack high-resolution monotonic and thread clocks as jitter
    jitter_pack = struct.pack(">QQQ", timing_ns, time.monotonic_ns(), time.process_time_ns())
    hasher.update(jitter_pack)
    hasher.update(prev_state)
    hasher.update(step.to_bytes(4, "big"))

    digest = bytearray(hasher.digest())

    # Circular bit-rotation on the swizzled entropy digest
    shift = (step % 7) + 1
    for idx in range(len(digest)):
        byte = digest[idx]
        digest[idx] = ((byte << shift) & 0xFF) | (byte >> (8 - shift))

    return bytes(digest)

# ==============================================================================
# 4. TOKEN FORMATION ACCORDING TO THE 3 MODES
# ==============================================================================
def resolve_hebrew_token(
    entropy: bytes,
    letters: List[Tuple[str, str, str]],
    doodles: List[Tuple[str, str, str, str, str]],
    mode: str
) -> Dict[str, Any]:
    """
    Picks a letter and a punctuation doodle from entropy and formats according to mode:
      - 'no-punct': Pure bare Hebrew letter.
      - 'punctuated': Punctuation doodle attached directly to/in the letter.
      - 'separate': Bare letter followed by bare punctuation doodle as distinct symbols.
    """
    # High-entropy integer extraction
    letter_int = int.from_bytes(entropy[0:4], "big")
    doodle_int = int.from_bytes(entropy[4:8], "big")

    letter_char, letter_name, letter_uni = letters[letter_int % len(letters)]
    doodle_char, doodle_name, doodle_cat, doodle_bare, doodle_uni = doodles[doodle_int % len(doodles)]

    if mode == "no-punct":
        token_glyph = letter_char
        token_desc = f"{letter_char} ({letter_name})"
        used_doodle_str = "[dim](none)[/dim]"

    elif mode == "punctuated":
        # Attaches the doodle directly into/onto the Hebrew character
        token_glyph = f"{letter_char}{doodle_char}"
        token_desc = f"{token_glyph} ({letter_name} + {doodle_name})"
        used_doodle_str = f"{doodle_bare} {doodle_name} [dim]{doodle_uni}[/dim]"

    else:  # 'separate'
        # Emits unpunctuated letter + bare punctuation symbol side-by-side
        token_glyph = f"{letter_char} {doodle_bare}"
        token_desc = f"{letter_char} ({letter_name}) + {doodle_bare} ({doodle_name})"
        used_doodle_str = f"{doodle_bare} {doodle_name} [dim]{doodle_uni}[/dim]"

    return {
        "letter_char": letter_char,
        "letter_name": letter_name,
        "letter_uni": letter_uni,
        "doodle_char": doodle_char,
        "doodle_bare": doodle_bare,
        "doodle_name": doodle_name,
        "doodle_cat": doodle_cat,
        "doodle_uni": doodle_uni,
        "used_doodle_str": used_doodle_str,
        "token_glyph": token_glyph,
        "token_desc": token_desc,
        "raw_byte": entropy[0],
        "swizzled_byte": (entropy[0] ^ entropy[1]) & 0xFF,
    }

# ==============================================================================
# 5. CLI & MAIN RUNNER
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Temporal Entropy Oracle (Hebrew Alphabet & Punctuation Doodles)"
    )
    parser.add_argument('-q', '--query', required=True, help='The focus or question.')
    parser.add_argument('-n', '--num', type=int, default=3, help='Number of characters to generate (default: 3).')
    parser.add_argument(
        '-m', '--mode',
        choices=['no-punct', 'punctuated', 'separate'],
        default='punctuated',
        help='Oracle mode: "no-punct" (bare letters), "punctuated" (doodles on letters), or "separate" (letters + bare punctuation symbols next to them). Default: punctuated.'
    )
    parser.add_argument('--min-delay', type=float, default=0.2, help='Min timing stagger in seconds.')
    parser.add_argument('--max-delay', type=float, default=0.7, help='Max timing stagger in seconds.')
    parser.add_argument(
        '--source',
        choices=['auto', 'random.org', 'os'],
        default='auto',
        help='Entropy source: "auto" (Random.org with OS fallback), "random.org", or "os" (default: auto).'
    )
    parser.add_argument('--entropy-bytes', type=int, default=32, help='Bytes of raw entropy harvested per step (default: 32).')
    parser.add_argument('--timeout', type=float, default=3.0, help='HTTP timeout for Random.org in seconds (default: 3.0).')
    parser.add_argument('--include-sofit', action='store_true', help='Include the 5 final Hebrew letters (Kaf, Mem, Nun, Pe, Tsadi).')
    parser.add_argument('-v', '--show-bytes', action='store_true', help='Display raw entropy, swizzled digests, source, and Unicode breakdown tables.')
    args = parser.parse_args()

    # Prepare alphabet
    letters = list(HEBREW_LETTERS_BASE)
    if args.include_sofit:
        letters.extend(HEBREW_LETTERS_SOFIT)

    doodles = HEBREW_DOODLES

    # Query authentication
    query_hash = hashlib.sha256(args.query.encode()).digest()
    session_auth = query_hash.hex()[:8].upper()

    console.print(f"\n[bold magenta]TEMPORAL HEBREW ORACLE[/bold magenta]")
    console.print(f"[dim]Focus:[/dim] [italic]'{args.query}'[/italic]")
    console.print(f"[dim]Mode:[/dim] [bold yellow]{args.mode}[/bold yellow] | [dim]Auth:[/dim] [green]{session_auth}[/green] | [dim]Letters:[/dim] [cyan]{len(letters)}[/cyan] | [dim]Doodles:[/dim] [cyan]{len(doodles)}[/cyan]\n")

    revealed_tokens: List[Dict[str, Any]] = []
    records = []
    prev_state = query_hash

    # Dynamic status spinner during staggered entropy acquisition
    with console.status("[bold cyan]Gathering atmospheric entropy...") as status:
        for i in range(1, args.num + 1):
            stagger = random.uniform(args.min_delay, args.max_delay)
            time.sleep(stagger)

            atm_bytes, os_bytes, timing_ns, source_desc = harvest_entropy_block(
                num_bytes=args.entropy_bytes,
                mode=args.source,
                timeout=args.timeout
            )

            swizzled = swizzle_entropy_pool(
                atm_bytes=atm_bytes,
                os_bytes=os_bytes,
                step=i,
                timing_ns=timing_ns,
                prev_state=prev_state,
                query_seed=query_hash
            )
            prev_state = swizzled

            token = resolve_hebrew_token(swizzled, letters, doodles, args.mode)
            revealed_tokens.append(token)

            latency_ms = timing_ns / 1_000_000
            digest_hex = swizzled.hex()[:8].upper()
            records.append((i, stagger, source_desc, latency_ms, digest_hex, token))

            status.update(f"[bold cyan]Swizzling step {i}/{args.num}... [dim]({token['token_glyph']})[/dim]")

    # ==========================================================================
    # 1. ORACLE RESPONSE DISPLAY
    # ==========================================================================
    # Space tokens with clean margins for distinct visual readability
    token_glyphs = [t["token_glyph"] for t in revealed_tokens]
    oracle_text = "    ".join(token_glyphs)

    token_names = "  ·  ".join([t["token_desc"] for t in revealed_tokens])

    response_panel = Panel(
        f"[bold white font size=18]{oracle_text}[/bold white font size=18]\n\n[dim]{token_names}[/dim]",
        title=f"[bold green]Oracle Response ({args.mode})[/bold green]",
        subtitle=f"[dim]{args.num} tokens · {args.num * args.entropy_bytes * 8} bits entropy[/dim]",
        expand=False
    )
    console.print(response_panel)

    # ==========================================================================
    # 2. OPTIONAL VIEW: Detailed Entropy & Byte Table (--show-bytes / -v)
    # ==========================================================================
    if args.show_bytes:
        console.print("\n[dim]-- Entropy & Unicode Inspection --[/dim]")
        table = Table(show_header=True, header_style="bold blue", border_style="dim")
        table.add_column("#", justify="right", style="dim", width=3)
        table.add_column("Stagger", justify="right", style="cyan")
        table.add_column("Entropy Source", justify="center", style="magenta")
        table.add_column("Latency", justify="right", style="dim")
        table.add_column("Digest", justify="center", style="green")
        table.add_column("Letter", justify="left", style="bold white")
        table.add_column("Doodle Mark", justify="left", style="yellow")
        table.add_column("Output", justify="center", style="bold green")

        for idx, stagger, src, lat, dig, tok in records:
            table.add_row(
                str(idx),
                f"{stagger:.2f}s",
                src,
                f"{lat:.1f}ms",
                f"0x{dig}...",
                f"{tok['letter_char']} {tok['letter_name']} [dim]({tok['letter_uni']})[/dim]",
                tok['used_doodle_str'],
                f"[bold]{tok['token_glyph']}[/bold]"
            )
        console.print(table)

    console.print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]Aborted.[/red]")
