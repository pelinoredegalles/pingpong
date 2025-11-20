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

def compute_result(home_score: int, away_score: int, home_sets: List[int] = None, away_sets: List[int] = None) -> float:
    """
    Enhanced result calculation:
    - Sets won (70% weight): higher impact than pure score
    - Points across all sets (30% weight): refinement
    
    Example: 3-2 victory with 150-140 points → strong win but not dominant
    Example: 3-0 victory with 160-80 points → dominant win
    """
    if home_score == away_score == 0:
        return 0.5
    
    # Sets-based result (70% weight)
    total_sets = home_score + away_score
    if total_sets > 0:
        sets_result = home_score / total_sets
    else:
        sets_result = 0.5
    
    # Points-based refinement (30% weight)
    if home_sets and away_sets:
        home_points = sum(s for s in home_sets if s > 0)
        away_points = sum(s for s in away_sets if s > 0)
        total_points = home_points + away_points
        if total_points > 0:
            points_result = home_points / total_points
        else:
            points_result = 0.5
        # Weighted combination
        result = 0.7 * sets_result + 0.3 * points_result
    else:
        result = sets_result
    
    return max(0.0, min(1.0, result))

def get_margin_coefficient(home_score: int, away_score: int) -> float:
    """
    Adjust K-factor based on match margin:
    - 3-0 or 0-3: dominant win/loss (1.2x)
    - 3-1 or 1-3: clear win/loss (1.0x)
    - 3-2 or 2-3: narrow win/loss (0.85x) - less impactful
    """
    margin = abs(home_score - away_score)
    if margin == 3:  # 3-0
        return 1.2
    elif margin == 2:  # 3-1
        return 1.0
    else:  # 3-2
        return 0.85

def get_dynamic_k_factor(player: str, opponent: str, scores: Dict[str, int], player_matches: Dict[str, int], elo_diff: float) -> float:
    """
    Dynamic K-factor based on:
    1. Experience: New players (< 5 matches) get higher K
    2. Rating gap: Upsetting stronger opponent gets higher K
    3. Consistency: Established players get lower K for stability
    """
    base_k = K_FACTOR
    
    # 1. Experience factor (players with few matches should gain/lose more)
    player_match_count = player_matches.get(player, 0)
    if player_match_count < 5:
        exp_factor = 1.5  # New players
    elif player_match_count < 15:
        exp_factor = 1.2  # Growing players
    else:
        exp_factor = 1.0  # Established
    
    # 2. Rating gap factor (upsets should have more impact)
    if abs(elo_diff) > 200:
        gap_factor = 1.3  # Playing much stronger/weaker opponent
    elif abs(elo_diff) > 100:
        gap_factor = 1.15
    else:
        gap_factor = 1.0
    
    dynamic_k = base_k * exp_factor * gap_factor
    return round(dynamic_k)

def update_elo(scores: Dict[str, int], player: str, opponent: str, result: float, 
               home_score: int, away_score: int, player_matches: Dict[str, int], 
               k: int = None) -> None:
    """
    Updated ELO calculation with:
    - Dynamic K-factor
    - Margin coefficient
    - Better result weighting (sets + points)
    """
    p_elo = scores[player]
    o_elo = scores[opponent]
    elo_diff = o_elo - p_elo
    
    # Calculate dynamic K
    if k is None:
        k = get_dynamic_k_factor(player, opponent, scores, player_matches, elo_diff)
    
    # Calculate expected result (standard ELO formula)
    expected = 1 / (1 + 10 ** (elo_diff / 400))
    
    # Apply margin coefficient (3-0 matters more than 3-2)
    margin_coeff = get_margin_coefficient(home_score, away_score)
    
    # Calculate ELO change
    delta = k * margin_coeff * (result - expected)
    
    # Update with minimum floor
    new_elo = p_elo + delta
    new_elo = max(800, new_elo)  # Minimum ELO floor to prevent rating collapse
    
    scores[player] = round(new_elo)

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
    player_match_count: Dict[str, int] = defaultdict(int)

    for match in matches:
        for duel in match.get("games", []):
            h = duel.get("home_player", "").strip()
            a = duel.get("away_player", "").strip()
            hs = duel.get("home_score", 0)
            as_ = duel.get("away_score", 0)
            hc = duel.get("home_code", "").strip()
            ac = duel.get("away_code", "").strip()
            h_sets = duel.get("home_sets", [])
            a_sets = duel.get("away_sets", [])

            if not is_valid_player(h) or not is_valid_player(a):
                continue

            h_team = get_club_from_code(hc, match)
            a_team = get_club_from_code(ac, match)

            club_counts[h][h_team] += 1
            club_counts[a][a_team] += 1

            player_stats[h]["matches"] += 1
            player_stats[a]["matches"] += 1
            player_match_count[h] += 1
            player_match_count[a] += 1

            if hs > as_:
                player_stats[h]["wins"] += 1
            elif as_ > hs:
                player_stats[a]["wins"] += 1

            result_home = compute_result(hs, as_, h_sets, a_sets)
            result_away = compute_result(as_, hs, a_sets, h_sets)

            update_elo(scores, h, a, result_home, hs, as_, player_match_count)
            update_elo(scores, a, h, result_away, as_, hs, player_match_count)

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
