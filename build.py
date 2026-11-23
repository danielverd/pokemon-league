"""Turn the stat sheet into a static dashboard: python build.py
polars loads the sheet; everything is shipped to the page as per-game rows so it can sort,
filter by round and re-aggregate (players, teams, draft rounds) in the browser."""
import ast, json, os
from collections import Counter
import polars as pl

SRC = "PokemonLeague_statsheet.tsv"

def load_names():
    """Optional private display names. Public builds leave these unset and show initials.
    Set PDL_NAMES='{"A":"Alex"}' or put the same JSON in names.local.json (gitignored)."""
    if os.environ.get("PDL_NAMES"):
        return json.loads(os.environ["PDL_NAMES"])
    if os.path.exists("names.local.json"):
        with open("names.local.json", encoding="utf-8") as f:
            return json.load(f)
    return {}

NAMES = load_names()
# A build that sees names can never overwrite the public page.
OUT = "index.private.html" if NAMES else "index.html"
DRAFT_ROUNDS = 10  # a DraftRoundNo above this, or DraftedByPlayer == None, marks a free agent
NULLS = (None, "", "NA", "None")

df = pl.read_csv(SRC, separator="\t")
roster, games = {}, {}
for r in df.iter_rows(named=True):
    p = roster.setdefault(r["Pokemon"], dict(name=r["Pokemon"], owner=r["PlayerName"], rounds=set(),
                                             by=set(), fa=False, moves=Counter(), log=[]))
    p["rounds"].add(r["DraftRoundNo"])
    if r["DraftedByPlayer"] in NULLS or r["DraftRoundNo"] > DRAFT_ROUNDS:
        p["fa"] = True
    else:
        p["by"].add(r["DraftedByPlayer"])  # differs from owner = traded
    for k in ("Move1", "Move2", "Move3", "Move4"):
        if r[k]:
            move, n = ast.literal_eval(r[k])  # cells look like "['Earthquake', 2]"
            p["moves"][move] += n
    won = str(r["Winner"]).lower() in ("true", "1")
    a, c = sorted((r["PlayerName"], r["OpponentName"]))
    games.setdefault((r["RegRound"], r["GameNumber"], a, c), set()).add(r["PlayerName"] if won else r["OpponentName"])
    p["log"].append(dict(r=r["RegRound"], n=r["GameNumber"], o=r["OpponentName"], w=int(won),
                         l=int(str(r["Lead"]).lower() in ("true", "1")),
                         t=r["TurnsIn"], m=r["MovesUsed"], k=r["Kills"]))

players = [dict(name=p["name"], owner=p["owner"],
                dr=None if p["fa"] else min(p["rounds"]),
                by=None if p["fa"] else sorted(p["by"])[0],
                moveList=p["moves"].most_common(6), log=p["log"]) for p in roster.values()]
# one row per game with its winner; the page derives matches (best of 3) and standings from these
for k, w in games.items():
    if len(w) != 1:
        print("WARNING: sides disagree on the winner of", k)
games = [dict(r=r, n=n, a=a, b=c, w=sorted(w)[0]) for (r, n, a, c), w in sorted(games.items())]
owners = {o: NAMES.get(o, o) for o in sorted({p["owner"] for p in players})}
html = open("template.html", encoding="utf-8").read().replace(
    "__DATA__", json.dumps(dict(owners=owners, players=players, games=games), ensure_ascii=False, separators=(",", ":")))
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print(f"{OUT} written: {len(players)} Pokémon, {len(owners)} teams, "
      f"{sum(p['by'] is None for p in players)} free agents, {len(games)} games")
