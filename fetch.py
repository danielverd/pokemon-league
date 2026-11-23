"""Download the latest stat sheet from Google Sheets: python fetch.py
Overwrites PokemonLeague_statsheet.tsv; git keeps the history of earlier versions.

The sheet location is private config, kept out of the repo. Either set environment variables
    PDL_SHEET_ID   the long ID in the sheet URL: docs.google.com/spreadsheets/d/<ID>/edit
    PDL_SHEET_GID  the tab's number, shown as #gid=<GID> in the URL (0 for the first tab)
or put the same values in sheet.local.json (gitignored): {"id": "<ID>", "gid": "<GID>"}
The sheet must be shared as "Anyone with the link can view" for this to work without signing in."""
import json, os, sys, urllib.error, urllib.request

OUT = "PokemonLeague_statsheet.tsv"
REQUIRED = {"Pokemon", "PlayerName", "OpponentName", "DraftRoundNo", "DraftedByPlayer",
            "RegRound", "GameNumber", "Winner"}  # columns build.py relies on


def load_config():
    if os.environ.get("PDL_SHEET_ID"):
        return os.environ["PDL_SHEET_ID"], os.environ.get("PDL_SHEET_GID", "0")
    if os.path.exists("sheet.local.json"):
        with open("sheet.local.json", encoding="utf-8") as f:
            c = json.load(f)
        return c["id"], str(c.get("gid", "0"))
    sys.exit("No sheet configured. Set PDL_SHEET_ID / PDL_SHEET_GID or create sheet.local.json "
             '({"id": "...", "gid": "0"}). See the top of fetch.py.')


def main():
    sheet_id, gid = load_config()
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=tsv&gid={gid}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            ctype, body = r.headers.get("Content-Type", ""), r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        sys.exit(f"Download failed (HTTP {e.code}). Check the sheet ID and gid.")
    # A private sheet answers with a Google sign-in page instead of data.
    if "text/html" in ctype or body.lstrip().startswith("<"):
        sys.exit('Got a web page, not data: share the sheet as "Anyone with the link can view".')

    header = set(body.split("\n", 1)[0].rstrip("\r").split("\t"))
    if missing := REQUIRED - header:
        sys.exit(f"Downloaded tab is missing columns {sorted(missing)}; is the gid the right tab? "
                 f"{OUT} was left unchanged.")

    # Write to a temp file, then swap it in, so a failed write never leaves a half-written sheet.
    tmp = OUT + ".part"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(body)
    os.replace(tmp, OUT)
    print(f"{OUT} updated: {len(body.splitlines()) - 1} data rows")


if __name__ == "__main__":
    main()
