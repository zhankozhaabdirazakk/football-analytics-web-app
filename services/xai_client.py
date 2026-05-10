import os
import requests
from dotenv import load_dotenv

load_dotenv()

XAI_API_KEY = os.getenv("XAI_API_KEY")
BASE_URL = "https://api.x.ai/v1/responses"


def generate_team_insight(team_name: str, matches: list[dict], players: list[dict]) -> str:
    if not XAI_API_KEY:
        return ""

    recent = []
    for match in matches[:5]:
        recent.append(
            {
                "date": match.get("utcDate", "")[:10],
                "home": match.get("homeTeam", {}).get("name", ""),
                "away": match.get("awayTeam", {}).get("name", ""),
                "score": f'{match.get("score", {}).get("fullTime", {}).get("home", 0)}-'
                         f'{match.get("score", {}).get("fullTime", {}).get("away", 0)}'
            }
        )

    top_players = sorted(players, key=lambda x: x.get("contribution", 0), reverse=True)[:5]
    top_players_text = [
        f'{p["name"]}: {p["goals"]} goals, {p["assists"]} assists'
        for p in top_players
    ]

    prompt = f"""
You are writing one short football insight for a fan dashboard.

Team: {team_name}

Recent matches:
{recent}

Top player contributions this season:
{top_players_text}

Write 2-3 sentences. Mention form and 1-2 key contributors.
"""

    payload = {
        "model": "grok-3-mini",
        "input": prompt
    }

    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            print("xAI error:", response.status_code, response.text)
            return ""

        data = response.json()

        # Try a few common output shapes safely
        if "output_text" in data:
            return data["output_text"].strip()

        output = data.get("output", [])
        if output and isinstance(output, list):
            for item in output:
                content = item.get("content", [])
                for block in content:
                    if block.get("type") == "output_text":
                        return block.get("text", "").strip()

        return ""
    except Exception as e:
        print("xAI request failed:", e)
        return ""