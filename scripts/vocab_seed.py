"""Seed the target vocabulary (data/lexicon/target_vocab.csv).

Three hand-written blocks (weather lane, curated news items, core) plus letters and
digits. ASL-LEX subjective-frequency Z scores are attached where an entry matches, for
ranking and for the report. Re-run after editing the blocks; the CSV is the artefact
the developer reviews.

Usage: python scripts/vocab_seed.py [path/to/asllex_signdata.csv]
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "lexicon" / "target_vocab.csv"

# concept_id: keywords (first keyword is the display gloss)
WEATHER = {
    "weather": "weather, climate", "forecast": "forecast, predict", "sunny": "sunny, sun, sunshine",
    "clear": "clear, mostly clear", "cloudy": "cloudy, cloud, clouds, overcast, partly cloudy",
    "rain": "rain, rainy, showers, rainfall, drizzle", "thunderstorm": "thunderstorm, thunderstorms, thunder, storm, storms",
    "lightning": "lightning", "snow": "snow, snowy, flurries", "ice": "ice, icy, sleet, freezing rain",
    "fog": "fog, foggy, mist", "wind": "wind, winds, windy, breeze, breezy, gusty, gusts",
    "calm": "calm, light winds", "hot": "hot, heat, heat index", "warm": "warm, warmer", "cool": "cool, cooler",
    "cold": "cold, chilly, freeze, freezing, frost", "temperature": "temperature, temperatures, degrees",
    "high": "high, highs, maximum", "low": "low, lows, minimum", "humid": "humid, humidity, muggy",
    "dry": "dry, drier", "wet": "wet", "chance": "chance, possible, possibly, likely, probability",
    "percent": "percent, %", "precipitation": "precipitation", "storm": "storm, severe", "hurricane": "hurricane, tropical storm",
    "tornado": "tornado, twister", "flood": "flood, flooding", "warning": "warning, warn, alert, advisory, watch",
    "danger": "danger, dangerous, risk, hazard", "sky": "sky, skies", "morning": "morning", "afternoon": "afternoon",
    "evening": "evening", "tonight": "tonight", "night": "night, overnight", "today": "today", "tomorrow": "tomorrow",
    "day": "day, daytime", "week": "week, weeks", "weekend": "weekend", "monday": "monday", "tuesday": "tuesday",
    "wednesday": "wednesday", "thursday": "thursday", "friday": "friday", "saturday": "saturday", "sunday": "sunday",
    "north": "north, northern, northwest, northeast", "south": "south, southern, southwest, southeast",
    "east": "east, eastern", "west": "west, western", "before": "before, until", "after": "after, then, later",
    "between": "between", "around": "around, near, about, approximately", "increase": "increase, increasing, rise, rising, higher",
    "decrease": "decrease, decreasing, fall, falling, lower, drop", "start": "start, begin, beginning", "end": "end, ending, stop",
    "continue": "continue, continuing, remain, remains, stay", "change": "change, changing, becoming", "mostly": "mostly, mainly",
    "slight": "slight, little", "heavy": "heavy", "strong": "strong, severe", "light": "light (weak), gentle",
}

NEWS = {
    "say": "say, said, says, told, tell, announce, announced", "official": "official, officials, authority, authorities, ministry",
    "government": "government, governing, federal, state (government)", "leader": "leader, chief, head, prime minister, minister",
    "president": "president, president-elect", "election": "election, elections, elect, elected, vote, voting",
    "party": "party (political)", "country": "country, nation, national", "city": "city, county, town", "people": "people, others, residents",
    "world": "world, international", "military": "military, navy, army, troops", "war": "war, conflict", "police": "police, officer",
    "fire": "fire, fires, wildfire, wildfires, blaze, blazes, caught fire", "firefighter": "firefighter, firefighters",
    "emergency": "emergency", "rescue": "rescue, rescuers, rescued, pulled out", "search": "search, searching, looking for",
    "safe": "safe, safety, taken to safety", "alive": "alive, survive, survived", "kill": "kill, killed, deadly, death, died",
    "destroy": "destroy, destroyed, damage", "evacuate": "evacuate, evacuated", "landslide": "landslide, mudslide",
    "earthquake": "earthquake, quake", "bury": "bury, buried", "house": "house, houses, home, homes, housing",
    "ship": "ship, boat, navy ship", "sink": "sink, sank, sunk", "oil": "oil", "spill": "spill, spilled, leak", "coast": "coast, shore",
    "island": "island", "ocean": "ocean, sea, pacific", "environment": "environment, environmental", "area": "area, region, province, zone",
    "space": "space, outer space", "station": "station, space station", "astronaut": "astronaut, astronauts", "rocket": "rocket, launch, launched",
    "earth": "earth, planet", "return": "return, returned, back, come back, ride back", "capsule": "capsule, spacecraft",
    "broken": "broken, malfunction, fail, failed", "expect": "expect, expected", "since": "since", "year": "year, years, year-old",
    "month": "month, months", "last": "last, previous, former, past", "next": "next, upcoming", "first": "first", "again": "again",
    "hundred": "hundred, hundreds", "thousand": "thousand, thousands", "many": "many, some, several, dozens",
    "health": "health, medical", "doctor": "doctor, expert, experts", "hospital": "hospital", "sick": "sick, infection, illness, suffering, suffer",
    "medicine": "medicine, drug, drugs, antibiotics, treatment, treat, treatable", "problem": "problem, problems, crisis, crises",
    "old": "old, older, elderly", "need": "need, require, must", "few": "few, little", "detail": "detail, details, information",
    "common": "common, uncommon, usual, unusual, rare", "right": "right, correct, proper", "pope": "pope, vatican", "church": "church, religion",
    "bank": "bank, banker, central bank", "money": "money, finance, financial", "price": "price, prices, cost, costs", "food": "food",
    "trade": "trade, tariffs, business", "threat": "threat, threaten, warning (political)", "replace": "replace, replaces, successor",
    "resign": "resign, resignation, quit", "become": "become, became, will become", "popular": "popular, popularity", "decline": "decline, declined, drop, fell",
    "immigration": "immigration, immigrant, migrant", "citizen": "citizen, noncitizen", "manage": "manage, run (organisation), lead, navigated",
    "establish": "establish, found, founded", "deal": "deal, agreement, negotiate", "law": "law, legal, court, judge", "attack": "attack, strike, strikes",
    "prepare": "prepare, bracing, brace, ready", "issue": "issue, issued, publish, release", "flag": "flag, red flag", "service": "service, agency, department",
    "signal": "signal, signaling, indicate", "increase-risk": "heightened, increased, greater", "due-to": "due to, because, caused by",
    "los-angeles": "los angeles", "california": "california, californians", "canada": "canada, canadian", "china": "china, chinese",
    "united-states": "u.s., us, united states, america, american", "england": "england, britain, british, uk", "florida": "florida",
}

CORE = {
    "yes": "yes", "no": "no, not", "help": "help", "want": "want", "know": "know", "think": "think, believe", "see": "see, look, watch",
    "go": "go, went", "come": "come, arrive", "make": "make, build", "give": "give, provide", "take": "take, taken", "get": "get, receive",
    "work": "work, job", "live": "live, living", "now": "now, currently", "here": "here", "there": "there", "with": "with, including", "without": "without",
    "more": "more, most", "less": "less, fewer", "all": "all, every", "other": "other, another", "new": "new", "big": "big, large, major",
    "small": "small, minor", "good": "good", "bad": "bad", "time": "time", "family": "family, son, daughter, child, children",
    "man": "man, male", "woman": "woman, female", "name": "name, called, named", "number": "number, count", "and": "and, also, plus",
    "but": "but, however", "if": "if, suppose", "how": "how", "what": "what", "where": "where", "when": "when", "who": "who", "why": "why",
    "water": "water", "home": "home", "school": "school", "car": "car, vehicle", "road": "road, street", "plane": "plane, airplane, flight",
    "true": "true, truth, real", "important": "important, major", "finish": "finish, done, complete, wrap up", "happen": "happen, occur, event",
}

LETTERS = {c.lower(): c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
DIGITS = {str(d): str(d) for d in range(10)}


def asllex_index(path):
    idx = {}
    if not path or not Path(path).exists():
        return idx
    with open(path, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            for key in (r.get("EntryID", ""), r.get("LemmaID", "")):
                k = key.lower().split("_")[0]
                try:
                    z = float(r.get("SignFrequency(Z)", ""))
                except ValueError:
                    continue
                if k and (k not in idx or z > idx[k][0]):
                    idx[k] = (z, r.get("SignBankAnnotationID", ""))
    return idx


def main():
    idx = asllex_index(sys.argv[1] if len(sys.argv) > 1 else None)
    rows = []
    for source, block in (("weather", WEATHER), ("news", NEWS), ("core", CORE)):
        for cid, kws in block.items():
            z, sb = idx.get(cid, ("", ""))
            rows.append({"concept_id": cid, "gloss": kws.split(",")[0].strip().upper(), "keywords": kws, "source": source,
                         "asllex_z": z, "signbank_hint": sb, "status": "planned"})
    for cid, kw in LETTERS.items():
        rows.append({"concept_id": f"letter-{cid}", "gloss": kw, "keywords": kw, "source": "letter", "asllex_z": "", "signbank_hint": "", "status": "planned"})
    for cid, kw in DIGITS.items():
        rows.append({"concept_id": f"digit-{cid}", "gloss": kw, "keywords": kw, "source": "digit", "asllex_z": "", "signbank_hint": "", "status": "planned"})
    seen = set()
    dedup = []
    for r in rows:
        if r["concept_id"] in seen:
            raise SystemExit(f"duplicate concept_id {r['concept_id']}")
        seen.add(r["concept_id"])
        dedup.append(r)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(dedup[0].keys()))
        w.writeheader()
        w.writerows(dedup)
    by = {}
    for r in dedup:
        by[r["source"]] = by.get(r["source"], 0) + 1
    print(f"wrote {OUT} with {len(dedup)} rows: {by}; ASL-LEX z attached to {sum(1 for r in dedup if r['asllex_z'] != '')}")


if __name__ == "__main__":
    main()
