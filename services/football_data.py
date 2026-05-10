import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
BASE_URL = "https://api.football-data.org/v4"


def build_knockout_ties(matches):
    """
    Groups knockout matches into ties and computes aggregate score.
    A winner is only set when the tie is complete.
    """
    stages = {
        "PLAY_OFFS": {},
        "LAST_16": {},
        "QUARTER_FINALS": {},
        "SEMI_FINALS": {},
        "FINAL": {},
    }

    for match in matches:
        stage = match.get("stage")
        if stage not in stages:
            continue

        home = match.get("homeTeam", {})
        away = match.get("awayTeam", {})

        home_id = home.get("id")
        away_id = away.get("id")

        if not home_id or not away_id:
            continue

        pair = tuple(sorted([home_id, away_id]))
        tie_key = f"{stage}-{pair[0]}-{pair[1]}"

        if tie_key not in stages[stage]:
            stages[stage][tie_key] = {
                "tie_key": tie_key,
                "stage": stage,
                "team1_id": pair[0],
                "team2_id": pair[1],
                "team1_name": None,
                "team2_name": None,
                "team1_tla": None,
                "team2_tla": None,
                "team1_crest": None,
                "team2_crest": None,
                "team1_agg": 0,
                "team2_agg": 0,
                "legs": [],
                "winner_id": None,
                "is_complete": False,
            }

        stages[stage][tie_key]["legs"].append(match)

    for stage_name, stage_ties in stages.items():
        for tie in stage_ties.values():
            tie["legs"].sort(key=lambda m: m.get("utcDate", ""))

            id1 = tie["team1_id"]
            id2 = tie["team2_id"]

            all_finished = True

            for leg in tie["legs"]:
                home = leg.get("homeTeam", {})
                away = leg.get("awayTeam", {})
                score = leg.get("score", {}).get("fullTime", {})

                home_goals = score.get("home")
                away_goals = score.get("away")

                status = leg.get("status")
                if status != "FINISHED" or home_goals is None or away_goals is None:
                    all_finished = False
                    continue

                if home.get("id") == id1:
                    tie["team1_name"] = home.get("name")
                    tie["team1_tla"] = home.get("tla")
                    tie["team1_crest"] = home.get("crest")
                    tie["team2_name"] = away.get("name")
                    tie["team2_tla"] = away.get("tla")
                    tie["team2_crest"] = away.get("crest")

                    tie["team1_agg"] += home_goals
                    tie["team2_agg"] += away_goals
                else:
                    tie["team1_name"] = away.get("name")
                    tie["team1_tla"] = away.get("tla")
                    tie["team1_crest"] = away.get("crest")
                    tie["team2_name"] = home.get("name")
                    tie["team2_tla"] = home.get("tla")
                    tie["team2_crest"] = home.get("crest")

                    tie["team1_agg"] += away_goals
                    tie["team2_agg"] += home_goals

            tie["is_complete"] = all_finished

            if all_finished:
                if tie["team1_agg"] > tie["team2_agg"]:
                    tie["winner_id"] = id1
                elif tie["team2_agg"] > tie["team1_agg"]:
                    tie["winner_id"] = id2

    return {
        stage: list(stage_ties.values())
        for stage, stage_ties in stages.items()
    }

def find_tie_by_key(matches, tie_key):
    ties = build_knockout_ties(matches)
    for stage_ties in ties.values():
        for tie in stage_ties:
            if tie["tie_key"] == tie_key:
                return tie
    return None


def _headers():
    return {"X-Auth-Token": API_KEY}


def fetch_table(league_code: str):
    url = f"{BASE_URL}/competitions/{league_code}/standings"
    response = requests.get(url, headers=_headers(), timeout=20)

    if response.status_code != 200:
        print("football-data standings error:", response.status_code, response.text)
        return None

    data = response.json()
    standings = data.get("standings", [])
    if not standings:
        return None
    return standings[0].get("table", [])


def fetch_team_matches(team_id: int, limit: int = 5):
    url = f"{BASE_URL}/teams/{team_id}/matches?status=FINISHED&limit={limit}"
    response = requests.get(url, headers=_headers(), timeout=20)

    if response.status_code != 200:
        print("football-data team matches error:", response.status_code, response.text)
        return []

    data = response.json()
    return data.get("matches", [])


def fetch_team_info(team_id: int):
    url = f"{BASE_URL}/teams/{team_id}"
    response = requests.get(url, headers=_headers(), timeout=20)

    if response.status_code != 200:
        print("football-data team info error:", response.status_code, response.text)
        return None

def fetch_competition_matches(competition_code: str, season: int | None = None):
    url = f"{BASE_URL}/competitions/{competition_code}/matches"
    params = {}

    if season:
        params["season"] = season

    response = requests.get(
        url,
        headers=_headers(),
        params=params,
        timeout=20
    )

    if response.status_code != 200:
        print("football-data competition matches error:", response.status_code, response.text)
        return []

    data = response.json()
    return data.get("matches", [])
    return response.json()