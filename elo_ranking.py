import os
import json
import logging
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any, DefaultDict

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DATA_DIR: str = os.path.join(os.path.dirname(__file__), "data")
FILES: Dict[str, str] = {
    "Grupo6": "matches_Grupo6_enriched.json",
    "Grupo7": "matches_Grupo7_enriched.json"
}

INITIAL_ELO: int = 1400
K_FACTOR: int = 100
ABC_CODES: set = {"A", "B", "C", "ABC"}
XYZ_CODES: set = {"X", "Y", "Z", "XYZ"}

def is_valid_player(name: str) -> bool:
    if not name or name.strip() == "":
        return False
    name = name.strip().upper()
    if name in {"A", "B", "C", "X", "Y", "Z", "ABC", "XYZ"}:
        return False
    if "DOBLE" in name:
        return False
    return True

def compute_result(home_score: int, away_score: int) -> float:
    total = home_score + away_score
    if total == 0:
        return 0.5
    return home_score / total

def update_elo(scores: Dict[str, int], player: str, opponent: str, result: float, k: int = K_FACTOR) -> None:
    p_elo = scores[player]
    o_elo = scores[opponent]
    expected = 1 / (1 + 10 ** ((o_elo - p_elo) / 400))
    delta = k * (result - expected)
    scores[player] = round(p_elo + delta)

def get_club_from_code(code: str, match: Dict[str, Any]) -> str:
    abc_wins: int = 0
    xyz_wins: int = 0

    for g in match.get("games", []):
        hc = g.get("home_code", "").strip()
        hs = g.get("home_score", 0)
        ac = g.get("away_code", "").strip()
        as_ = g.get("away_score", 0)

        if hc in ABC_CODES and hs > as_:
            abc_wins += 1
        elif ac in ABC_CODES and as_ > hs:
            abc_wins += 1
        elif hc in XYZ_CODES and hs > as_:
            xyz_wins += 1
        elif ac in XYZ_CODES and as_ > hs:
            xyz_wins += 1

    if abc_wins == match.get("score_home", 0):
        abc_team = match.get("home_team")
        xyz_team = match.get("away_team")
    else:
        abc_team = match.get("away_team")
        xyz_team = match.get("home_team")

    if code in ABC_CODES:
        return abc_team or "Unknown"
    elif code in XYZ_CODES:
        return xyz_team or "Unknown"
    return "Unknown"

def process_group(group: str, filename: str) -> None:
    path = os.path.join(DATA_DIR, filename)
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            matches = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading {filename}: {e}")
        return

    scores: Dict[str, int] = defaultdict(lambda: INITIAL_ELO)
    club_counts: DefaultDict[str, DefaultDict[str, int]] = defaultdict(lambda: defaultdict(int))
    player_stats: DefaultDict[str, Dict[str, int]] = defaultdict(lambda: {"matches": 0, "wins": 0})

    for match in matches:
        for duel in match.get("games", []):
            h = duel.get("home_player", "").strip()
            a = duel.get("away_player", "").strip()
            hs = duel.get("home_score", 0)
            as_ = duel.get("away_score", 0)
            hc = duel.get("home_code", "").strip()
            ac = duel.get("away_code", "").strip()

            if not is_valid_player(h) or not is_valid_player(a):
                continue

            h_team = get_club_from_code(hc, match)
            a_team = get_club_from_code(ac, match)

            club_counts[h][h_team] += 1
            club_counts[a][a_team] += 1

            player_stats[h]["matches"] += 1
            player_stats[a]["matches"] += 1

            if hs > as_:
                player_stats[h]["wins"] += 1
            elif as_ > hs:
                player_stats[a]["wins"] += 1

            result_home = compute_result(hs, as_)
            result_away = compute_result(as_, hs)

            update_elo(scores, h, a, result_home)
            update_elo(scores, a, h, result_away)

    player_clubs: Dict[str, str] = {
        player: max(clubs.items(), key=lambda x: x[1])[0]
        for player, clubs in club_counts.items()
    }

    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    ranking_data: List[Dict[str, Any]] = [
        {
            "player": player,
            "elo": score,
            "club": player_clubs.get(player, "Unknown"),
            "matches": player_stats[player]["matches"],
            "wins": player_stats[player]["wins"],
            "win_rate": round(player_stats[player]["wins"] / player_stats[player]["matches"] * 100, 1) if player_stats[player]["matches"] > 0 else 0.0
        }
        for player, score in ranking
    ]

    out_path = os.path.join(DATA_DIR, f"elo_{group}.json")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(ranking_data, f, ensure_ascii=False, indent=2)
        logger.info(f"\n🏓 Elo Ranking for {group}:")
        for i, entry in enumerate(ranking_data, 1):
            logger.info(f"{i:2d}. {entry['player']:<35} Elo: {entry['elo']:>4d}  |  {entry['matches']:>2d} matches  |  {entry['win_rate']:>5.1f}%  |  Club: {entry['club']}")
        logger.info(f"✅ File saved: {out_path}")
    except IOError as e:
        logger.error(f"Error saving {out_path}: {e}")

for group, filename in FILES.items():
    process_group(group, filename)
