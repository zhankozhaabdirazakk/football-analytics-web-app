from flask import Flask, render_template, request
from services.football_data import (
    fetch_table,
    fetch_team_matches,
    fetch_team_info,
    fetch_competition_matches,
    build_knockout_ties,
    find_tie_by_key,
)
from services.api_football import (
    fetch_team_player_stats,
    merge_squad_with_stats,
    group_merged_players_by_position,
    build_pitch_from_merged_players,
)
from services.xai_client import generate_team_insight

app = Flask(__name__)

LEAGUES = {
    "1": {
        "name": "Premier League",
        "code": "PL",
        "ucl_spots": 5,
        "rel_from": 18,
        "logo": "https://crests.football-data.org/PL.png",
        "season": 2025,
    },
    "2": {
        "name": "La Liga",
        "code": "PD",
        "ucl_spots": 4,
        "rel_from": 18,
        "logo": "https://crests.football-data.org/PD.png",
        "season": 2025,
    },
    "3": {
        "name": "Bundesliga",
        "code": "BL1",
        "ucl_spots": 4,
        "rel_from": 16,
        "logo": "https://crests.football-data.org/BL1.png",
        "season": 2025,
    },
    "4": {
        "name": "Serie A",
        "code": "SA",
        "ucl_spots": 4,
        "rel_from": 18,
        "logo": "https://crests.football-data.org/SA.png",
        "season": 2025,
    },
    "5": {
        "name": "Ligue 1",
        "code": "FL1",
        "ucl_spots": 3,
        "rel_from": 16,
        "logo": "https://crests.football-data.org/FL1.png",
        "season": 2025,
    },
    "6": {
    "name": "Champions League",
    "code": "CL",
    "ucl_spots": 0,
    "rel_from": 0,
    "logo": "https://crests.football-data.org/CL.png",
    "season": 2025,
},
}
BRACKET_SLOTS = {
    "left_last16": [
        "LAST_16-64-610",    # Liverpool FC vs Galatasaray SK
        "LAST_16-61-524",    # Chelsea FC vs Paris Saint-Germain FC

        "LAST_16-5-102",     # FC Bayern München vs Atalanta BC
        "LAST_16-65-86",     # Manchester City FC vs Real Madrid CF
    ],

    "right_last16": [
        "LAST_16-67-81",     # Newcastle United FC vs FC Barcelona
        "LAST_16-73-78",     # Tottenham Hotspur FC vs Club Atlético de Madrid

        "LAST_16-3-57",      # Bayer 04 Leverkusen vs Arsenal FC
        "LAST_16-498-5721",  # Sporting Clube de Portugal vs FK Bodø/Glimt
    ],

    "left_quarters": [
        "QUARTER_FINALS-64-524",  # Liverpool FC vs Paris Saint-Germain FC
        "QUARTER_FINALS-5-86",    # FC Bayern München vs Real Madrid CF
    ],

    "right_quarters": [
        "QUARTER_FINALS-78-81",   # Club Atlético de Madrid vs FC Barcelona
        "QUARTER_FINALS-57-498",  # Arsenal FC vs Sporting Clube de Portugal
    ],

    "left_semis": [],
    "right_semis": [],
    "final": [],
}

@app.route("/", methods=["GET"])
def index():
    table = None
    selected_league = request.args.get("league")
    league_data = None

    if selected_league in LEAGUES:
        league_data = LEAGUES[selected_league]
        table = fetch_table(league_data["code"])

    return render_template(
        "index.html",
        table=table,
        leagues=LEAGUES,
        selected_league=selected_league,
        league_data=league_data,
    )

@app.route("/champions-league/knockout", methods=["GET"])
def champions_league_knockout():
    season = 2025
    matches = fetch_competition_matches("CL", season=season)
    ties_by_stage = build_knockout_ties(matches)

    all_ties = {}
    for stage_ties in ties_by_stage.values():
        for tie in stage_ties:
            all_ties[tie["tie_key"]] = tie

    def fill_slots(slot_keys):
        filled = []
        for key in slot_keys:
            if key in all_ties:
                filled.append(all_ties[key])
            else:
                filled.append(None)
        return filled

    rounds = {
        "left_last16": fill_slots(BRACKET_SLOTS["left_last16"]),
        "right_last16": fill_slots(BRACKET_SLOTS["right_last16"]),
        "left_quarters": fill_slots(BRACKET_SLOTS["left_quarters"]),
        "right_quarters": fill_slots(BRACKET_SLOTS["right_quarters"]),
        "left_semis": fill_slots(BRACKET_SLOTS["left_semis"]),
        "right_semis": fill_slots(BRACKET_SLOTS["right_semis"]),
        "final": fill_slots(BRACKET_SLOTS["final"]),
    }

    return render_template("ucl_knockout.html", rounds=rounds)

@app.route("/champions-league/tie/<tie_key>", methods=["GET"])
def champions_league_tie(tie_key):
    season = 2025
    matches = fetch_competition_matches("CL", season=season)
    tie = find_tie_by_key(matches, tie_key)

    if not tie:
        return "Tie not found", 404

    return render_template("ucl_tie.html", tie=tie)

@app.route("/team/<int:team_id>", methods=["GET"])
def team_page(team_id: int):
    team_name = request.args.get("name", "Team")
    crest = request.args.get("crest", "")
    league_key = request.args.get("league", "")
    league_data = LEAGUES.get(league_key)

    matches = fetch_team_matches(team_id, limit=5)
    team_data = fetch_team_info(team_id)

    season = league_data["season"] if league_data else 2025

    player_stats = fetch_team_player_stats(team_name=team_name, season=season)
    print("TEAM:", team_name)
    print("API-FOOTBALL PLAYER STATS COUNT:", len(player_stats))

    merged_squad = merge_squad_with_stats(team_data, player_stats)
    grouped_players = group_merged_players_by_position(merged_squad)
    pitch_players = build_pitch_from_merged_players(merged_squad)

    ai_insight = generate_team_insight(team_name, matches, player_stats)

    return render_template(
        "team.html",
        team_id=team_id,
        team_name=team_name,
        crest=crest,
        league_key=league_key,
        matches=matches,
        team_data=team_data,
        merged_squad=merged_squad,
        grouped_players=grouped_players,
        pitch_players=pitch_players,
        ai_insight=ai_insight,
    )

if __name__ == "__main__":
    app.run(debug=True, port=5003)