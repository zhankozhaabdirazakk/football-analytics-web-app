import requests

API_KEY = "0321de127b7e41a3af69e1d6d08ccc21"  



LEAGUES = {
    "1": ("Premier League",   "PL",  5, 18),  # 20 teams, top 5 UCL, bottom 3 from pos 18
    "2": ("La Liga",          "PD",  4, 18),  # 20 teams, top 4 UCL, bottom 3 from pos 18
    "3": ("Bundesliga",       "BL1", 4, 16),  # 18 teams, top 4 UCL, bottom 3 from pos 16
    "4": ("Serie A",          "SA",  4, 18),  # 20 teams, top 4 UCL, bottom 3 from pos 18
    "5": ("Ligue 1",          "FL1", 3, 16),  # 18 teams, top 3 UCL, bottom 3 from pos 16
    "6": ("Champions League", "CL",  0,  0),  # no highlights
}

def fetch_team_info(team_id):
    url = f"https://api.football-data.org/v4/teams/{team_id}"
    headers = {"X-Auth-Token": API_KEY}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("Error fetching team info:", response.status_code)
            return None
        return response.json()
    except Exception as e:
        print("Request failed:", e)
        return None

def fetch_table(league_code):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/standings"
    headers = {"X-Auth-Token": API_KEY}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("Error fetching table:", response.status_code)
            return None

        data = response.json()
        return data["standings"][0]["table"]

    except Exception as e:
        print("Request failed:", e)
        return None


def fetch_team_matches(team_id):
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=5"
    headers = {"X-Auth-Token": API_KEY}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("Error fetching team matches:", response.status_code)
            return None

        data = response.json()
        return data.get("matches", [])

    except Exception as e:
        print("Request failed:", e)
        return None

def pick_league():
    print("\n⚽ LEAGUE TABLE TRACKER\n")
    for key, (name, _, _, _) in LEAGUES.items():
        print(f"  {key}. {name}")
    choice = input("\nPick a league (1-6): ")
    return LEAGUES.get(choice)


def fetch_table(league_code):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/standings"
    headers = {"X-Auth-Token": API_KEY}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("Error:", response.status_code)
            print(response.text)
            return None

        data = response.json()
        return data["standings"][0]["table"]

    except Exception as e:
        print("Request failed:", e)
        return None

def display_table(table, league_name, ucl_spots, rel_from):
    print(f"\n📊 {league_name} — Current Standings\n")
    print(f"{'Pos':<5}{'Team':<30}{'P':<5}{'W':<5}{'D':<5}{'L':<5}{'GF':<5}{'GA':<5}{'GD':<5}{'Pts'}")
    print("-" * 75)
    for row in table:
        pos  = row["position"]
        team = row["team"]["name"]
        p    = row["playedGames"]
        w    = row["won"]
        d    = row["draw"]
        l    = row["lost"]
        gf   = row["goalsFor"]
        ga   = row["goalsAgainst"]
        gd   = row["goalDifference"]
        pts  = row["points"]

        if ucl_spots > 0 and pos <= ucl_spots:
            marker = "🔵"
        elif rel_from > 0 and pos >= rel_from:
            marker = "🔴"
        else:
            marker = "  "

        print(f"{marker} {pos:<5}{team:<30}{p:<5}{w:<5}{d:<5}{l:<5}{gf:<5}{ga:<5}{gd:<5}{pts}")


def show_last_matches(team_id, team_name):
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=FINISHED&limit=5"
    headers = {"X-Auth-Token": API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("❌ Error fetching matches.")
        return

    matches = response.json()["matches"][-5:]

    print(f"\n📅 Last 5 matches for {team_name}:\n")
    print(f"{'Date':<15}{'Home':<25}{'Score':<10}{'Away'}")
    print("-" * 65)

    for m in matches:
        date       = m["utcDate"][:10]
        home       = m["homeTeam"]["name"]
        away       = m["awayTeam"]["name"]
        home_goals = m["score"]["fullTime"]["home"]
        away_goals = m["score"]["fullTime"]["away"]
        print(f"{date:<15}{home:<25}{str(home_goals) + '-' + str(away_goals):<10}{away}")

def search_team(table):
    team_name = input("\n🔍 Search for a team (or press Enter to skip): ")
    if team_name == "":
        return
    found = False
    for row in table:
        if team_name.lower() in row["team"]["name"].lower():
            pos  = row["position"]
            team = row["team"]["name"]
            p    = row["playedGames"]
            w    = row["won"]
            d    = row["draw"]
            l    = row["lost"]
            gf   = row["goalsFor"]
            ga   = row["goalsAgainst"]
            gd   = row["goalDifference"]
            pts  = row["points"]
            print(f"\n✅ Found!\n")
            print(f"{'Pos':<5}{'Team':<30}{'P':<5}{'W':<5}{'D':<5}{'L':<5}{'GF':<5}{'GA':<5}{'GD':<5}{'Pts'}")
            print("-" * 75)
            print(f"{pos:<5}{team:<30}{p:<5}{w:<5}{d:<5}{l:<5}{gf:<5}{ga:<5}{gd:<5}{pts}")
            see_matches = input("\n📅 Want to see their last 5 matches? (yes/no): ")
            if see_matches.lower() == "yes":
                team_id = row["team"]["id"]
                show_last_matches(team_id, team)
            found = True
            break
    if not found:
        print(f"\n❌ Team '{team_name}' not found. Try a different name!")

def save_table(table, league_name):
    save = input("\n💾 Want to save the table to a file? (yes/no): ")
    if save.lower() != "yes":
        return
    filename = league_name.lower().replace(" ", "_") + "_table.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"{league_name} — Current Standings\n\n")
        f.write(f"{'Pos':<5}{'Team':<30}{'P':<5}{'W':<5}{'D':<5}{'L':<5}{'GF':<5}{'GA':<5}{'GD':<5}{'Pts'}\n")
        f.write("-" * 75 + "\n")
        for row in table:
            pos  = row["position"]
            team = row["team"]["name"]
            p    = row["playedGames"]
            w    = row["won"]
            d    = row["draw"]
            l    = row["lost"]
            gf   = row["goalsFor"]
            ga   = row["goalsAgainst"]
            gd   = row["goalDifference"]
            pts  = row["points"]
            f.write(f"{pos:<5}{team:<30}{p:<5}{w:<5}{d:<5}{l:<5}{gf:<5}{ga:<5}{gd:<5}{pts}\n")
    print(f"\n✅ Table saved as '{filename}'!")


def main():
    print("\n👋 Welcome to League Table Tracker!")
    while True:
        result = pick_league()
        if not result:
            print("❌ Invalid choice, try again.")
            continue

        league_name, league_code, ucl_spots, rel_from = result
        print(f"\n⏳ Fetching {league_name} table...")

        table = fetch_table(league_code)
        if table:
            display_table(table, league_name, ucl_spots, rel_from)
            search_team(table)
            save_table(table, league_name)

        again = input("\n🔄 Want to check another league? (yes/no): ")
        if again.lower() != "yes":
            print("\n👋 See you later!\n")
            break

if __name__ == "__main__":

    main()