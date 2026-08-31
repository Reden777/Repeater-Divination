#!/usr/bin/env python3
"""
swizzler_oracle.py
Temporally staggered entropy oracle.
Default: Outputs a clean, punctuated sentence.
Opt-in: Pass --show-bytes to inspect raw/swizzled byte values and timing metrics.
"""

import sys
import time
import random
import argparse
import urllib.request
import hashlib
from typing import List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# === THE 256 WORD VOCABULARY (0-255) ===
WORDS = [
    "Abundance", "Abyss", "Action", "Alchemy", "Alpha", "Anchor", "Ancient", "Angel", "Anthem", "Arcane",
    "Arrival", "Aspect", "Astral", "Atlas", "Atmos", "Atom", "Aura", "Aurora", "Autumn", "Avatar",
    "Axis", "Azure", "Balance", "Beacon", "Beast", "Belief", "Birth", "Blade", "Bless", "Bloom",
    "Blossom", "Blue", "Bond", "Bone", "Bound", "Brave", "Breath", "Bridge", "Bright", "Burning",
    "Burst", "Cabal", "Calm", "Canyon", "Canvas", "Castle", "Cavern", "Cedar", "Celestial", "Cell",
    "Center", "Chain", "Chalice", "Chaos", "Charm", "Chrome", "Cipher", "Circle", "Citadel", "Clarity",
    "Cliff", "Clock", "Cloud", "Coast", "Code", "Coil", "Cold", "Comet", "Compass", "Complex",
    "Conduit", "Copper", "Core", "Cosmic", "Courage", "Crag", "Crater", "Create", "Crescent", "Cross",
    "Crown", "Crypt", "Crystal", "Cube", "Cycle", "Dance", "Daring", "Dark", "Dawn", "Death",
    "Deep", "Delta", "Depth", "Desert", "Desire", "Destiny", "Diamond", "Digit", "Disc", "Distant",
    "Divine", "Domain", "Door", "Dragon", "Dream", "Drift", "Drone", "Drop", "Drum", "Dust",
    "Eagle", "Earth", "Echo", "Eclipse", "Edge", "Ego", "Elder", "Electric", "Element", "Ember",
    "Emerald", "Empty", "Endless", "Energy", "Enigma", "Entropy", "Entry", "Envoy", "Epoch", "Equal",
    "Essence", "Eternal", "Ether", "Ethics", "Event", "Ever", "Evoke", "Evolution", "Exile", "Exodus",
    "Eye", "Fable", "Faith", "Falcon", "Fall", "Fathom", "Feather", "Field", "Final", "Fire",
    "Flame", "Flash", "Flight", "Flow", "Flower", "Fluid", "Flux", "Focus", "Fog", "Force",
    "Forest", "Forge", "Form", "Fortress", "Fortune", "Fossil", "Found", "Fractal", "Fragment", "Freedom",
    "Frequency", "Frost", "Frozen", "Fruit", "Future", "Galaxy", "Garden", "Gate", "Gaze", "Gear",
    "Gem", "Ghost", "Giant", "Glass", "Glide", "Glimmer", "Glow", "Glyph", "Gold", "Grace",
    "Graph", "Gravity", "Gray", "Green", "Grid", "Ground", "Growth", "Guard", "Guide", "Gulf",
    "Habit", "Halo", "Hammer", "Harmony", "Harvest", "Haze", "Heart", "Heat", "Heaven", "Heavy",
    "Helix", "Helm", "Herald", "Hidden", "High", "Hollow", "Holy", "Honest", "Horizon", "Host",
    "Hour", "Human", "Humble", "Hunter", "Hybrid", "Icon", "Idea", "Idol", "Ignite", "Image",
    "Impact", "Impulse", "Index", "Infinite", "Inner", "Input", "Insight", "Ion", "Iron", "Island",
    "Ivory", "Jade", "Joint", "Journey", "Judge", "Jump", "Jungle", "Jupiter", "Justice", "Karma",
    "Key", "Kinetic", "King", "Kingdom", "Knight", "Knot", "Labyrinth", "Lake", "Lamp", "Land",
    "Lantern", "Laser", "Last", "Lava", "Law", "Layer", "Lead", "Leaf", "Legacy", "Legend",
    "Lens", "Level", "Life", "Light", "Limit", "Line", "Link", "Liquid", "Logic", "Lost",
    "Lotus", "Loud", "Love", "Low", "Loyal", "Lucid", "Lunar", "Lure", "Lust", "Lute",
    "Lyric", "Machine", "Magic", "Magma", "Magnet", "Malice", "Mantle", "Map", "Marble", "Mark",
    "Mars", "Mask", "Mass", "Master", "Matrix", "Matter", "Maze", "Meadow", "Media", "Melody",
    "Melt", "Memory", "Mercy", "Meridian", "Metal", "Meteor", "Method", "Metric", "Micro", "Mid",
    "Might", "Mind", "Mine", "Minor", "Mirror", "Mist", "Mobile", "Mode", "Model", "Modern",
    "Module", "Moment", "Monad", "Monolith", "Moon", "Mortal", "Motion", "Motive", "Mountain", "Mouth",
    "Move", "Music", "Mute", "Myth", "Nadir", "Nail", "Name", "Nano", "Native", "Nature",
    "Navigation", "Nebula", "Needle", "Neon", "Neptune", "Nerve", "Nest", "Net", "Network", "Neural",
    "Neutral", "Never", "New", "Nexus", "Night", "Nimbus", "Noble", "Node", "Noise", "Nomad",
    "North", "Note", "Nova", "Novel", "Nucleus", "Null", "Number", "Oak", "Object", "Oblivion",
    "Observant", "Obsidian", "Ocean", "Ochre", "Octave", "Omen", "Omega", "Onyx", "Open", "Opera",
    "Optic", "Oracle", "Orbit", "Order", "Ore", "Organ", "Origin", "Orion", "Ornament", "Out",
    "Outer", "Output", "Oval", "Oven", "Over", "Owl", "Oxide", "Oxygen", "Oyster", "Ozone",
    "Pace", "Pacific", "Pack", "Pact", "Page", "Paint", "Pair", "Palace", "Palm", "Panel",
    "Panic", "Paper", "Parable", "Paradigm", "Parallel", "Parent", "Particle", "Part", "Passage", "Passive",
    "Past", "Patch", "Path", "Patient", "Pattern", "Pause", "Peace", "Peak", "Pearl", "Pebble",
    "Pelican", "Pen", "Pendulum", "Perfect", "Period", "Petal", "Phantom", "Phase", "Phenomenon", "Phoenix",
    "Phone", "Photon", "Phrase", "Physical", "Piano", "Pick", "Picture", "Piece", "Pillar", "Pilot",
    "Pine", "Pink", "Pioneer", "Pipe", "Pirate", "Piston", "Pitch", "Pixel", "Place", "Plain",
    "Planet", "Plant", "Plasma", "Plate", "Platform", "Play", "Plot", "Plug", "Plum", "Plunge",
    "Plural", "Plus", "Poem", "Point", "Polar", "Pole", "Policy", "Polish", "Pollen", "Poly",
    "Pomp", "Pool", "Pop", "Port", "Portal", "Position", "Positive", "Post", "Potent", "Powder",
    "Power", "Practice", "Precious", "Prefix", "Premium", "Presence", "Press", "Price", "Pride", "Priest",
    "Prime", "Primitive", "Prince", "Print", "Prior", "Prism", "Private", "Prize", "Probe", "Problem",
    "Process", "Produce", "Product", "Profile", "Profit", "Program", "Progress", "Project", "Promise", "Prompt",
    "Proof", "Prophet", "Prosper", "Protect", "Protein", "Protocol", "Proud", "Prove", "Proxy", "Prune",
    "Psalm", "Pseudo", "Public", "Puff", "Pull", "Pulse", "Pump", "Punch", "Pure", "Purple",
    "Purpose", "Push", "Python", "Pyre", "Pyramid", "Quaint", "Quake", "Quantum", "Quarry", "Quartz",
    "Queen", "Quest", "Queue", "Quick", "Quiet", "Quilt", "Quiver", "Quota", "Quote", "Radar",
    "Radiant", "Radical", "Radio", "Radius", "Raft", "Rail", "Rain", "Rainbow", "Raise", "Rally",
    "Ram", "Ramp", "Random", "Range", "Rank", "Rapid", "Rare", "Rate", "Ratio", "Rattle",
    "Raven", "Raw", "Ray", "Reach", "React", "Reader", "Real", "Realm", "Rear", "Reason",
    "Rebel", "Recall", "Recent", "Record", "Red", "Reduce", "Reed", "Reel", "Reflect", "Reform",
    "Refresh", "Refuge", "Regal", "Region", "Register", "Regret", "Reign", "Relay", "Relic", "Relief",
    "Remedy", "Remote", "Render", "Renew", "Repair", "Repeat", "Report", "Rescue", "Research", "Reset",
    "Resin", "Resist", "Resolve", "Resort", "Resource", "Respect", "Respond", "Rest", "Restore", "Result",
    "Resume", "Retail", "Retain", "Retire", "Retort", "Return", "Reveal", "Reverse", "Review", "Revive",
    "Revolt", "Reward", "Rhythm", "Rib", "Ribbon", "Rich", "Ride", "Ridge", "Rifle", "Right",
    "Rigid", "Ring", "Riot", "Rip", "Ripple", "Rise", "Risk", "Ritual", "Rival", "River",
    "Road", "Roar", "Robot", "Rock", "Rocket", "Rod", "Roll", "Roman", "Roof", "Room",
    "Root", "Rope", "Rose", "Rotate", "Rough", "Round", "Route", "Row", "Royal", "Ruby",
    "Ruin", "Rule", "Rumor", "Run", "Rune", "Rural", "Rush", "Rust", "Sacred", "Saddle",
    "Safe", "Sage", "Sail", "Saint", "Salad", "Salary", "Sale", "Salt", "Salvage", "Samaritan",
    "Sample", "Sand", "Sane", "Sap", "Sapphire", "Sash", "Satin", "Satire", "Saturn", "Sauce",
    "Savage", "Save", "Savior", "Savor", "Saw", "Scale", "Scalp", "Scan", "Scant", "Scar",
    "Scarce", "Scare", "Scarf", "Scene", "Scent", "Scepter", "Schedule", "Scheme", "Scholar", "School",
    "Science", "Scoop", "Scope", "Scorch", "Score", "Scorn", "Scout", "Scrap", "Scream", "Screen",
    "Screw", "Script", "Scroll", "Scrub", "Sculpt", "Sea", "Seal", "Search", "Season", "Seat",
    "Second", "Secret", "Section", "Sector", "Secure", "Sediment", "Seed", "Seek", "Segment", "Select",
    "Self", "Sell", "Semen", "Semi", "Senate", "Send", "Senior", "Sense", "Sensor", "Sentence",
    "Sentry", "Sequel", "Sequence", "Serene", "Serial", "Series", "Sermon", "Serpent", "Serum", "Serve",
    "Server", "Service", "Session", "Set", "Setting", "Settle", "Seven", "Severe", "Sew", "Shabby",
    "Shade", "Shadow", "Shaft", "Shake", "Shallow", "Sham", "Shape", "Share", "Shark", "Sharp",
    "Shave", "Shear", "Shed", "Sheep", "Sheet", "Shelf", "Shell", "Shelter", "Sheriff", "Shield",
    "Shift", "Shimmer", "Shin", "Shine", "Ship", "Shirt", "Shiver", "Shock", "Shoe", "Shoot",
    "Shop", "Shore", "Short", "Shot", "Shoulder", "Shout", "Shovel", "Show", "Shower", "Shrimp",
    "Shrine", "Shrink", "Shroud", "Shrub", "Shrug", "Shuffle", "Shun", "Shut", "Shutter", "Shy",
    "Sibling", "Sick", "Side", "Siege", "Sigh", "Sight", "Sigma", "Sign", "Signal", "Signature",
    "Silence", "Silica", "Silk", "Sill", "Silo", "Silver", "Similar", "Simple", "Since", "Sing",
    "Singe", "Single", "Sink", "Sinner", "Siren", "Sirius", "Sister", "Site", "Six", "Size",
    "Sketch", "Skill", "Skin", "Skip", "Skirt", "Skull", "Sky", "Slab", "Slack", "Slain",
    "Slam", "Slang", "Slant", "Slap", "Slate", "Slave", "Sleek", "Sleep", "Sleeve", "Slice",
    "Slide", "Slight", "Slim", "Slip", "Slope", "Slot", "Slow", "Sludge", "Slug", "Slum",
    "Slump", "Small", "Smart", "Smash", "Smell", "Smile", "Smirk", "Smith", "Smoke", "Smooth",
    "Smug", "Snake", "Snap", "Snare", "Sneak", "Sniff", "Snow", "Soak", "Soap", "Soar",
    "Sober", "Social", "Sock", "Socket", "Soda", "Sofa", "Soft", "Soil", "Solar", "Soldier",
    "Sole", "Solid", "Solo", "Solstice", "Solvent", "Solve", "Somber", "Sonar", "Sonata", "Song",
    "Sonic", "Soon", "Soot", "Soothe", "Sore", "Sorrow", "Sort", "Soul", "Sound", "Soup",
    "Source", "South", "Space", "Spade", "Span", "Spare", "Spark", "Sparrow", "Speak", "Special",
    "Species", "Specter", "Speech", "Speed", "Spell", "Spend", "Sphere", "Spice", "Spider", "Spike",
    "Spill", "Spin", "Spine", "Spiral", "Spirit", "Spit", "Splash", "Split", "Spoil", "Spoke",
    "Sponge", "Sponsor", "Spoon", "Sport", "Spot", "Spouse", "Spray", "Spread", "Spring", "Sprint",
    "Sprout", "Spur", "Spy", "Squad", "Square", "Squash", "Squat", "Squeak", "Squid", "Stab",
    "Stable", "Stack", "Staff", "Stage", "Stain", "Stair", "Stake", "Stale", "Stall", "Stamp",
    "Stand", "Stanza", "Star", "Starch", "Stare", "Stark", "Start", "State", "Static", "Statue",
    "Status", "Stay", "Steady", "Steak", "Steal", "Steam", "Steel", "Steep", "Steer", "Stem",
    "Step", "Stereo", "Stern", "Stew", "Stick", "Stiff", "Stifle", "Still", "Sting", "Stir",
    "Stitch", "Stock", "Stoic", "Stone", "Stoop", "Stop", "Store", "Storm", "Story", "Stout",
    "Stove", "Strain", "Strait", "Strand", "Strange", "Strap", "Strategy", "Straw", "Stray", "Streak",
    "Stream", "Street", "Stress", "Stretch", "Strict", "Stride", "Strike", "String", "Strip", "Strive",
    "Stroke", "Strong", "Struck", "Stubborn", "Studio", "Study", "Stuff", "Stumble", "Stump", "Stun",
    "Sturdy", "Style", "Subject", "Submit", "Subtle", "Suburb", "Subway", "Success", "Suck", "Sudden",
    "Suffer", "Sugar", "Suggest", "Suit", "Sulfur", "Sullen", "Sultan", "Sum", "Summer", "Summit",
    "Sun", "Sunday", "Sunflower", "Sunset", "Super", "Supply", "Support", "Supreme", "Surf", "Surge",
    "Surplus", "Surprise", "Surround", "Survey", "Survival", "Survive", "Suspect", "Suspend", "Sustain", "Swamp",
    "Swan", "Swap", "Swarm", "Sway", "Swear", "Sweat", "Sweep", "Sweet", "Swell", "Swift",
    "Swim", "Swing", "Switch", "Sword", "Symbol", "Symmetry", "Symptom", "Synapse", "Sync", "Syndicate",
    "Syntax", "Syphon", "Syrup", "System", "Table", "Tablet", "Tackle", "Tact", "Tail", "Talent",
    "Talk", "Tall", "Talon", "Tame", "Tank", "Target", "Task", "Taste", "Tattoo", "Taurus",
    "Teach", "Team", "Tear", "Tech", "Teeth", "Tell", "Temper", "Temple", "Tempo", "Ten",
    "Tend", "Tent", "Term", "Terrain", "Terror", "Test", "Text", "Theory", "Thermal", "Thesis",
    "Thick", "Thief", "Thigh", "Thin", "Thing", "Think", "Third", "Thirst", "Thorn", "Thought",
    "Thread", "Threat", "Three", "Thrill", "Thrive", "Throat", "Throne", "Throw", "Thrust", "Thumb",
    "Thunder", "Thyme", "Tide", "Tier", "Tiger", "Tight", "Tile", "Tilt", "Timber", "Time",
    "Tin", "Tingle", "Tint", "Tiny", "Tip", "Tissue", "Titan", "Title", "Toad", "Toast",
    "Tobacco", "Today", "Toggle", "Token", "Toll", "Tomato", "Tomb", "Tone", "Tongue", "Tonic",
    "Tool", "Tooth", "Top", "Topic", "Torch", "Torque", "Total", "Touch", "Tough", "Tour",
    "Tower", "Town", "Toxic", "Toy", "Trace", "Track", "Tractor", "Trade", "Traffic", "Tragedy",
    "Trail", "Train", "Trait", "Traitor", "Trance", "Transfer", "Transit", "Transmission", "Trap", "Trauma",
    "Travel", "Tray", "Tread", "Treasure", "Treaty", "Tree", "Trek", "Tremor", "Trench", "Trend",
    "Trial", "Triangle", "Tribe", "Trick", "Trident", "Trigger", "Trill", "Trilogy", "Trim", "Trinity",
    "Trip", "Triple", "Tripod", "Triumph", "Trivial", "Troop", "Trophy", "Tropic", "Trouble", "Truce",
    "Truck", "True", "Trumpet", "Trunk", "Trust", "Truth", "Try", "Tube", "Tumble", "Tumor",
    "Tune", "Tunnel", "Turbine", "Turf", "Turkey", "Turn", "Turtle", "Tusk", "Tutor", "Twelve",
    "Twenty", "Twice", "Twilight", "Twin", "Twist", "Two", "Type", "Tyrant", "Ugly", "Ulterior",
    "Ultimate", "Ultra", "Umbra", "Unseen", "Under", "Unit", "Unity", "Universe", "Update", "Upward",
    "Urgent", "User", "Utmost", "Utopia", "Vacuum", "Vague", "Valiant", "Valley", "Value", "Valve",
    "Vampire", "Vanish", "Vapor", "Variable", "Vase", "Vast", "Vault", "Vector", "Veil", "Velocity",
    "Velvet", "Vendor", "Venture", "Venus", "Verb", "Verdict", "Verge", "Verify", "Verse", "Version",
    "Vessel", "Vest", "Veteran", "Veto", "Vibrant", "Vicar", "Vice", "Victim", "Victor", "Victory",
    "Video", "View", "Vigor", "Vile", "Villa", "Village", "Vine", "Vintage", "Vinyl", "Violent",
    "Violet", "Violin", "Viral", "Virtue", "Virus", "Visa", "Visage", "Vision", "Visit", "Visual",
    "Vital", "Vivid", "Vocal", "Voice", "Void", "Volt", "Volume", "Vortex", "Vote", "Voucher",
    "Vow", "Vowel", "Voyage", "Vulcan", "Vulture", "Wade", "Wafer", "Wager", "Wagon", "Waist",
    "Wait", "Wake", "Walk", "Wall", "Wallet", "Walnut", "Wander", "Want", "War", "Warden",
    "Warm", "Warn", "Warp", "Warrant", "Warrior", "Wash", "Wasp", "Waste", "Watch", "Water",
    "Wave", "Wax", "Way", "Weak", "Wealth", "Weapon", "Wear", "Weather", "Web", "Wedding",
    "Wedge", "Week", "Weigh", "Weird", "Welcome", "Weld", "Well", "West", "Whale", "Wharf",
    "Wheat", "Wheel", "While", "Whim", "Whip", "Whirl", "Whisper", "White", "Whole", "Wide",
    "Width", "Wield", "Wife", "Wild", "Will", "Wind", "Window", "Wine", "Wing", "Wink",
    "Winner", "Winter", "Wire", "Wisdom", "Wise", "Wish", "Wit", "Witch", "Witness", "Wizard",
    "Wolf", "Woman", "Wonder", "Wood", "Wool", "Word", "Work", "World", "Worm", "Worry",
    "Worth", "Wound", "Wrap", "Wrath", "Wreath", "Wreck", "Wrestle", "Wrist", "Write", "Wrong",
    "Xenon", "Xray", "Yacht", "Yard", "Yarn", "Year", "Yeast", "Yellow", "Yield", "Yoga",
    "Yoke", "Young", "Youth", "Zebra", "Zenith", "Zero", "Zinc", "Zip", "Zone", "Zodiac"
]

def fetch_single_atmospheric_byte() -> int:
    """Fetches a single raw byte (0-255) from Random.org atmospheric noise."""
    url = "https://www.random.org/integers/?num=1&min=0&max=255&col=1&base=10&format=plain&rnd=new"
    req = urllib.request.Request(url, headers={'User-Agent': 'SwizzlerOracle256/1.0'})
    with urllib.request.urlopen(req) as response:
        data = response.read().decode('utf-8').strip()
        return int(data)

def swizzle_byte(raw_byte: int, step: int, timing_ns: int, prev_byte: int) -> int:
    """Swizzles byte using jitter, state chaining, and circular bit-rotation."""
    jitter = timing_ns & 0xFF
    swizzled = raw_byte ^ jitter ^ prev_byte
    shift = (step % 7) + 1
    swizzled = ((swizzled << shift) & 0xFF) | (swizzled >> (8 - shift))
    return swizzled & 0xFF

def format_sentence(words: List[str]) -> str:
    """Formats a list of words into a single clean sentence."""
    joined = " ".join(words).strip()
    return f"{joined}."

def main():
    parser = argparse.ArgumentParser(description="Temporal Entropy Oracle")
    parser.add_argument('-q', '--query', required=True, help='The focus or question.')
    parser.add_argument('-n', '--num', type=int, default=3, help='Number of words in the sentence (default: 3).')
    parser.add_argument('--min-delay', type=float, default=0.2, help='Min timing stagger in seconds.')
    parser.add_argument('--max-delay', type=float, default=0.7, help='Max timing stagger in seconds.')
    # Opt-in flag: hidden/false by default
    parser.add_argument('-v', '--show-bytes', action='store_true', help='Display raw and swizzled byte tables.')
    args = parser.parse_args()

    query_hash = hashlib.sha256(args.query.encode()).hexdigest().upper()
    session_auth = query_hash[:8]

    console.print(f"\n[bold magenta]TEMPORAL ORACLE[/bold magenta]")
    console.print(f"[dim]Focus:[/dim] [italic]'{args.query}'[/italic]")
    console.print(f"[dim]Auth:[/dim] [green]{session_auth}[/green]\n")

    revealed_words = []
    records = []
    prev_byte = 0xAA
    used_indices = set()

    # Dynamic status spinner during the staggered entropy acquisition
    with console.status("[bold cyan]Gathering entropy...") as status:
        for i in range(1, args.num + 1):
            stagger = random.uniform(args.min_delay, args.max_delay)
            time.sleep(stagger)

            t_start = time.perf_counter_ns()
            raw_byte = fetch_single_atmospheric_byte()
            t_delta = time.perf_counter_ns() - t_start

            final_byte = swizzle_byte(raw_byte, i, t_delta, prev_byte)
            while final_byte in used_indices:
                final_byte = (final_byte + 1) % 256

            used_indices.add(final_byte)
            prev_byte = final_byte
            word = WORDS[final_byte]

            revealed_words.append(word)
            records.append((i, stagger, raw_byte, final_byte, word))
            status.update(f"[bold cyan]Swizzling byte {i}/{args.num}... [dim]({word})[/dim]")

    # 1. DEFAULT VIEW: Continuous Sentence Output
    sentence = format_sentence(revealed_words)
    console.print(Panel(f"[bold white italic]{sentence}[/bold white italic]", title="[bold green]Oracle Response[/bold green]", expand=False))

    # 2. OPTIONAL VIEW: Byte table when --show-bytes / -v is explicitly passed
    if args.show_bytes:
        console.print("\n[dim]-- Byte Inspection --[/dim]")
        table = Table(show_header=True, header_style="bold blue", border_style="dim")
        table.add_column("#", justify="right", style="dim", width=3)
        table.add_column("Stagger", justify="right", style="cyan")
        table.add_column("Raw Byte", justify="center", style="dim")
        table.add_column("Swizzled Byte", justify="center", style="yellow")
        table.add_column("Word", style="bold white")

        for idx, stagger, raw_b, swizzled_b, word in records:
            table.add_row(
                str(idx),
                f"{stagger:.2f}s",
                f"0x{raw_b:02X}",
                f"0x{swizzled_b:02X} ({swizzled_b})",
                word
            )
        console.print(table)

    console.print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]Aborted.[/red]")
