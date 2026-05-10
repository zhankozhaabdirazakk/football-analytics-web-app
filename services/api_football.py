import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_API_KEY")
BASE_URL = "https://v3.football.api-sports.io"


def _headers():
    return {
        "x-apisports-key": API_KEY
    }


def safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def search_team_id(team_name: str):
    """
    Resolves an API-Football team ID from a team name.
    This is a practical fallback so you don't have to manually map every club.
    """
    url = f"{BASE_URL}/teams"
    params = {"search": team_name}
    response = requests.get(url, headers=_headers(), params=params, timeout=20)

    if response.status_code != 200:
        print("API-Football team search error:", response.status_code, response.text)
        return None

    data = response.json()
    results = data.get("response", [])
    if not results:
        return None

    exact = next(
        (
            item for item in results
            if item.get("team", {}).get("name", "").lower() == team_name.lower()
        ),
        None
    )
    if exact:
        return exact.get("team", {}).get("id")

    return results[0].get("team", {}).get("id")


def fetch_team_player_stats(team_name: str, season: int):
    """
    Returns normalized player stats for one team from API-Football.
    """
    api_team_id = search_team_id(team_name)
    if not api_team_id:
        return []

    url = f"{BASE_URL}/players"
    params = {
        "team": api_team_id,
        "season": season,
    }
    response = requests.get(url, headers=_headers(), params=params, timeout=30)

    if response.status_code != 200:
        print("API-Football players error:", response.status_code, response.text)
        return []

    data = response.json()
    rows = data.get("response", [])
    normalized = []

    for item in rows:
        player = item.get("player", {})
        stats_list = item.get("statistics", [])

        # Pick the first statistics block for this season
        stats = stats_list[0] if stats_list else {}
        games = stats.get("games", {})
        goals = stats.get("goals", {})

        position = games.get("position") or "Unknown"
        goals_count = safe_int(goals.get("total"))
        assists_count = safe_int(goals.get("assists"))
        contribution = goals_count + assists_count

        normalized.append(
            {
                "name": player.get("name", "Unknown"),
                "firstname": player.get("firstname", ""),
                "lastname": player.get("lastname", ""),
                "photo": player.get("photo", ""),
                "position": position,
                "appearances": safe_int(games.get("appearences")),
                "minutes": safe_int(games.get("minutes")),
                "goals": goals_count,
                "assists": assists_count,
                "contribution": contribution,
            }
        )

    return normalized


def normalize_position(position: str) -> str:
    p = (position or "").lower()

    if "goalkeeper" in p or p == "g":
        return "GK"

    if "defender" in p or "back" in p or p in {"d", "defence"}:
        return "DEF"

    if "midfielder" in p or "midfield" in p or p in {"m"}:
        return "MID"

    if "forward" in p or "winger" in p or "striker" in p or p in {"f", "attacker", "attack"}:
        return "FWD"

    return "MID"


def group_players_by_position(players: list[dict]):
    grouped = {
        "Goalkeepers": [],
        "Defenders": [],
        "Midfielders": [],
        "Forwards": [],
    }

    for player in players:
        pos = normalize_position(player.get("position", ""))

        if pos == "GK":
            grouped["Goalkeepers"].append(player)
        elif pos == "DEF":
            grouped["Defenders"].append(player)
        elif pos == "MID":
            grouped["Midfielders"].append(player)
        else:
            grouped["Forwards"].append(player)

    for key in grouped:
        grouped[key].sort(key=lambda x: (-x["contribution"], -x["appearances"], x["name"]))

    return grouped


def build_pitch_players(players: list[dict]):
    """
    Builds a simple 4-3-3 using top contributors per position.
    """
    grouped = group_players_by_position(players)

    gk = grouped["Goalkeepers"][:1]
    defs = grouped["Defenders"][:4]
    mids = grouped["Midfielders"][:3]
    fwds = grouped["Forwards"][:3]

    slots = [
        ("p1", gk[0] if len(gk) > 0 else None),

        ("p2", defs[0] if len(defs) > 0 else None),
        ("p3", defs[1] if len(defs) > 1 else None),
        ("p4", defs[2] if len(defs) > 2 else None),
        ("p5", defs[3] if len(defs) > 3 else None),

        ("p6", mids[0] if len(mids) > 0 else None),
        ("p7", mids[1] if len(mids) > 1 else None),
        ("p8", mids[2] if len(mids) > 2 else None),

        ("p9", fwds[0] if len(fwds) > 0 else None),
        ("p10", fwds[1] if len(fwds) > 1 else None),
        ("p11", fwds[2] if len(fwds) > 2 else None),
    ]

def normalize_position_label(position: str) -> str:
    p = (position or "").lower()

    if "goalkeeper" in p:
        return "Goalkeepers"
    if "def" in p or "back" in p:
        return "Defenders"
    if "mid" in p:
        return "Midfielders"
    if "forward" in p or "wing" in p or "striker" in p or "attack" in p or "offence" in p:
        return "Forwards"

    return "Midfielders"


def merge_squad_with_stats(team_data, player_stats):
    """
    team_data comes from football-data.org and contains the squad
    player_stats comes from API-Football and may be empty
    """
    if not team_data or "squad" not in team_data:
        return []

    stats_lookup = {}
    for p in player_stats:
        name = p.get("name", "").strip().lower()
        if name:
            stats_lookup[name] = p

    merged = []

    for player in team_data["squad"]:
        name = player.get("name", "")
        position = player.get("position", "Unknown")
        match = stats_lookup.get(name.strip().lower())

        goals = match.get("goals", 0) if match else 0
        assists = match.get("assists", 0) if match else 0
        contribution = goals + assists

        merged.append({
            "name": name,
            "position": position,
            "goals": goals,
            "assists": assists,
            "contribution": contribution,
        })

    return merged


def group_merged_players_by_position(players):
    grouped = {
        "Goalkeepers": [],
        "Defenders": [],
        "Midfielders": [],
        "Forwards": [],
    }

    for player in players:
        label = normalize_position_label(player.get("position", ""))
        grouped[label].append(player)

    for key in grouped:
        grouped[key].sort(key=lambda x: (-x["contribution"], x["name"]))

    return grouped


def build_pitch_from_merged_players(players):
    grouped = group_merged_players_by_position(players)

    gk = grouped["Goalkeepers"][:1]
    defs = grouped["Defenders"][:4]
    mids = grouped["Midfielders"][:3]
    fwds = grouped["Forwards"][:3]

    slots = [
        ("p1", gk[0] if len(gk) > 0 else None),

        ("p2", defs[0] if len(defs) > 0 else None),
        ("p3", defs[1] if len(defs) > 1 else None),
        ("p4", defs[2] if len(defs) > 2 else None),
        ("p5", defs[3] if len(defs) > 3 else None),

        ("p6", mids[0] if len(mids) > 0 else None),
        ("p7", mids[1] if len(mids) > 1 else None),
        ("p8", mids[2] if len(mids) > 2 else None),

        ("p9", fwds[0] if len(fwds) > 0 else None),
        ("p10", fwds[1] if len(fwds) > 1 else None),
        ("p11", fwds[2] if len(fwds) > 2 else None),
    ]

    return slots