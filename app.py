import streamlit as st
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, List, Set, Tuple, Any, Optional

INITIAL_ELO = 1400
K_FACTOR = 100
ABC_CODES = {"A", "B", "C", "ABC"}
XYZ_CODES = {"X", "Y", "Z", "XYZ"}
INVALID_PLAYER_NAMES = {"DOBLE", "A", "B", "C", "X", "Y", "Z", "ABC", "XYZ"}
RESULT_WIN = "Victoria"
RESULT_LOSS = "Derrota"
DATE_FORMAT = "%d %b %Y"

def load_matches_data() -> pd.DataFrame:
    try:
        df_g6 = pd.read_json("data/matches_Grupo6_enriched.json")
    except (FileNotFoundError, json.JSONDecodeError):
        df_g6 = pd.DataFrame()

    try:
        df_g7 = pd.read_json("data/matches_Grupo7_enriched.json")
    except (FileNotFoundError, json.JSONDecodeError):
        df_g7 = pd.DataFrame()
    
    return pd.concat([df_g6, df_g7], ignore_index=True)

def load_matches_by_group(grupo: str) -> pd.DataFrame:
    try:
        grupo_id = grupo.replace(" ", "")
        df = pd.read_json(f"data/matches_{grupo_id}_enriched.json")
        return df
    except (FileNotFoundError, json.JSONDecodeError):
        return pd.DataFrame()

df_all = load_matches_data()

EXPECTED_COLS = ["match_id", "date", "home_team", "away_team", "games", "score_home", "score_away"]
for col in EXPECTED_COLS:
    if col not in df_all.columns:
        df_all[col] = None

data_dir = os.path.join(os.path.dirname(__file__), "data")
st.set_page_config(page_title="Comparador Elo", layout="wide")

if "nav_vista" not in st.session_state:
    st.session_state.nav_vista = "Calendario de partidos"
if "nav_equipo1" not in st.session_state:
    st.session_state.nav_equipo1 = None
if "nav_equipo2" not in st.session_state:
    st.session_state.nav_equipo2 = None
if "nav_jugador" not in st.session_state:
    st.session_state.nav_jugador = None
if "nav_equipo" not in st.session_state:
    st.session_state.nav_equipo = None

st.sidebar.title("🧭 Navegación")

categoria_map = {
    "DHA - División Honor Andalucía": "Grupo 6",
    "SDA - Super División Andalucía": "Grupo 7"
}

categoria_selected = st.sidebar.selectbox(
    "Selecciona categoría", 
    list(categoria_map.keys())
)
grupo = categoria_map[categoria_selected]

with st.sidebar:
    st.markdown("### 👥 **Jugadores**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆚 Comparar", use_container_width=True, key="btn_comparar_j"):
            st.session_state.nav_vista = "Comparar jugadores"
            st.rerun()
    with col2:
        if st.button("📊 Ranking + H2H", use_container_width=True, key="btn_ranking_h2h"):
            st.session_state.nav_vista = "Ranking y H2H"
            st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Resumen", use_container_width=True, key="btn_resumen_j"):
            st.session_state.nav_vista = "Resumen por jugador"
            st.rerun()
    with col2:
        if st.button("🔬 Análisis Avanzado", use_container_width=True, key="btn_analisis_j"):
            st.session_state.nav_vista = "Análisis Jugador Avanzado"
            st.rerun()
    
    st.markdown("### ⚽ **Equipos**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📈 Comparar", use_container_width=True, key="btn_comparar_eq"):
            st.session_state.nav_vista = "Comparar equipos"
            st.rerun()
    with col2:
        if st.button("📊 Dashboard", use_container_width=True, key="btn_dashboard_eq"):
            st.session_state.nav_vista = "Dashboard Equipo"
            st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📅 Calendario", use_container_width=True, key="btn_calendario"):
            st.session_state.nav_vista = "Calendario de partidos"
            st.rerun()
    with col2:
        if st.button("🏆 Clasificación", use_container_width=True, key="btn_clasificacion"):
            st.session_state.nav_vista = "Clasificación"
            st.rerun()
grupo_id = grupo.replace(" ", "")
ELO_FILE = os.path.join(data_dir, f"elo_{grupo_id}.json")
MATCHES_FILE = os.path.join(data_dir, f"matches_{grupo_id}_enriched.json")

division_map = {
    "Grupo 6": "DHA",
    "Grupo 7": "SDA"
}

vista_to_section = {
    "Comparar jugadores": "👥 Jugadores",
    "Ranking y H2H": "👥 Jugadores",
    "Resumen por jugador": "👥 Jugadores",
    "Comparar equipos": "⚽ Equipos",
    "Dashboard Equipo": "⚽ Equipos",
    "Estadísticas Equipo": "⚽ Equipos",
    "Calendario de partidos": "📋 Varias",
    "Clasificación": "📋 Varias",
    "Análisis Jugador Avanzado": "👥 Jugadores"
}

vista_to_display = {
    "Comparar jugadores": "Comparar Jugadores",
    "Ranking y H2H": "Ranking + H2H",
    "Resumen por jugador": "Perfil Jugador",
    "Comparar equipos": "Comparar Equipos",
    "Dashboard Equipo": "Dashboard Equipos",
    "Estadísticas Equipo": "Estadísticas Equipo",
    "Calendario de partidos": "Calendario",
    "Clasificación": "Clasificación",
    "Análisis Jugador Avanzado": "Análisis Avanzado"
}

def get_page_title():
    vista = st.session_state.nav_vista
    section = vista_to_section.get(vista, "")
    display_name = vista_to_display.get(vista, vista)
    division = division_map.get(grupo, "")
    
    if section:
        return f"{section} - {display_name} - {division}"
    return f"{display_name} - {division}"

def load_elo_data(filepath: str) -> pd.DataFrame:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            elo_data = json.load(f)
        return pd.DataFrame(elo_data).sort_values(by="elo", ascending=False)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error loading ELO data: {e}")
        return pd.DataFrame()

def load_matches(filepath: str) -> List[Dict[str, Any]]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error loading matches: {e}")
        return []

def navigate_to_player(player: str) -> None:
    st.session_state.nav_jugador = player
    st.session_state.nav_vista = "Resumen por jugador"
    st.rerun()

def navigate_to_team(team: str) -> None:
    st.session_state.nav_equipo = team
    st.session_state.nav_vista = "Dashboard Equipo"
    st.rerun()

def load_standings(grupo_id: str) -> pd.DataFrame:
    try:
        filepath = os.path.join(data_dir, f"standings_{grupo_id}.json")
        with open(filepath, "r", encoding="utf-8") as f:
            standings_data = json.load(f)
        
        target_group = f"Grupo {grupo_id[-1]}"
        teams_list = standings_data.get(target_group, [])
        
        if not teams_list:
            return pd.DataFrame()
        
        df = pd.DataFrame(teams_list)
        return df.sort_values(by="points", ascending=False).reset_index(drop=True)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        st.error(f"Error loading standings: {e}")
        return pd.DataFrame()

@st.cache_data
def get_duels(player: str) -> List[Dict[str, str]]:
    duels = []
    for match in matches:
        for g in match.get("games", []):
            if g.get("home_player") == player or g.get("away_player") == player:
                is_home = g["home_player"] == player
                score = g["home_score"] if is_home else g["away_score"]
                opp_score = g["away_score"] if is_home else g["home_score"]
                opponent = g["away_player"] if is_home else g["home_player"]
                result = RESULT_WIN if score > opp_score else RESULT_LOSS
                casa_away = "Casa" if is_home else "Away"
                duels.append({
                    "rival": opponent,
                    "marcador": f"{score} - {opp_score}",
                    "resultado": result,
                    "casa_away": casa_away
                })
    return duels

@st.cache_data
def get_stats(player: str) -> Tuple[int, int]:
    duels = get_duels(player)
    wins = sum(1 for d in duels if d["resultado"] == RESULT_WIN)
    losses = sum(1 for d in duels if d["resultado"] == RESULT_LOSS)
    return wins, losses

@st.cache_data
def get_common_opponents(p1: str, p2: str) -> List[str]:
    opp1 = {d["rival"] for d in get_duels(p1)}
    opp2 = {d["rival"] for d in get_duels(p2)}
    return sorted(opp1 & opp2)

@st.cache_data
def plot_elo(player: str) -> List[int]:
    elo = INITIAL_ELO
    history = []
    for match in matches:
        for g in match.get("games", []):
            if g.get("home_player") == player or g.get("away_player") == player:
                is_home = g["home_player"] == player
                score = g["home_score"] if is_home else g["away_score"]
                opp_score = g["away_score"] if is_home else g["home_score"]
                
                h_sets = g.get("home_sets", [])
                a_sets = g.get("away_sets", [])
                
                if is_home:
                    player_sets = h_sets
                    opp_sets = a_sets
                else:
                    player_sets = a_sets
                    opp_sets = h_sets
                
                player_points = sum(s for s in player_sets if s > 0)
                opp_points = sum(s for s in opp_sets if s > 0)
                
                sets_result = score / (score + opp_score) if (score + opp_score) > 0 else 0.5
                points_result = player_points / (player_points + opp_points) if (player_points + opp_points) > 0 else 0.5
                
                result = 0.7 * sets_result + 0.3 * points_result
                
                elo += K_FACTOR * (result - 0.5)
                history.append(round(elo))
    return history

def get_team_players(match: Dict[str, Any], team_name: str) -> Dict[str, Dict[str, int]]:
    players = {}
    for g in match["games"]:
        if match["home_team"] == team_name and g.get("home_player"):
            players[g["home_player"]] = {"score": g["home_score"], "opponent_score": g["away_score"]}
        elif match["away_team"] == team_name and g.get("away_player"):
            players[g["away_player"]] = {"score": g["away_score"], "opponent_score": g["home_score"]}
    return players

def build_team_table(players: Dict[str, Dict[str, int]], team_name: str) -> pd.DataFrame:
    rows = []
    for name, stats in players.items():
        info = elo_df[elo_df["player"] == name]
        if not info.empty:
            elo = info.iloc[0]["elo"]
            club = info.iloc[0]["club"]
            wins, losses = get_stats(name)
        else:
            elo = None
            club = team_name
            wins, losses = 0, 0
        result = RESULT_WIN if stats["score"] > stats["opponent_score"] else RESULT_LOSS
        color = "🟢" if result == RESULT_WIN else "🔴"
        rows.append({
            "Jugador": name,
            "Equipo": club,
            "Elo": elo,
            "Resultado": f"{color} {result}",
            "Marcador": f"{stats['score']} - {stats['opponent_score']}",
            "Victorias": wins,
            "Derrotas": losses
        })
    df = pd.DataFrame(rows)
    if "Elo" in df.columns:
        df["Elo"] = pd.to_numeric(df["Elo"], errors="coerce").fillna(1000)
        df = df.sort_values(by="Elo", ascending=False)
    else:
        df["Elo"] = 1000

    return df

def get_real_team(code: str, match: Dict[str, Any]) -> str:
    abc_wins = 0
    xyz_wins = 0

    for g in match.get("games", []):
        hc = g.get("home_code", "")
        hs = g.get("home_score", 0)
        ac = g.get("away_code", "")
        as_ = g.get("away_score", 0)

        if hc in ABC_CODES and hs > as_:
            abc_wins += 1
        elif ac in ABC_CODES and as_ > hs:
            abc_wins += 1
        elif hc in XYZ_CODES and hs > as_:
            xyz_wins += 1
        elif ac in XYZ_CODES and as_ > hs:
            xyz_wins += 1

    if abc_wins == match["score_home"]:
        abc_team = match["home_team"]
        xyz_team = match["away_team"]
    else:
        abc_team = match["away_team"]
        xyz_team = match["home_team"]

    if code in ABC_CODES:
        return abc_team
    elif code in XYZ_CODES:
        return xyz_team
    return "Inconnu"

def hay_doble(match: Dict[str, Any], equipo: str) -> bool:
    for g in match.get("games", []):
        code_home = g.get("home_code", "")
        code_away = g.get("away_code", "")

        team_home = get_real_team(code_home, match)
        team_away = get_real_team(code_away, match)

        if team_home == equipo and code_home in ABC_CODES:
            return True
        if team_away == equipo and code_away in XYZ_CODES:
            return True

    return False

def est_match_futur(match: Dict[str, Any]) -> bool:
    try:
        match_date = datetime.strptime(match["date"], DATE_FORMAT)
        return match.get("result", "").strip() == "" or match_date >= datetime.today()
    except (ValueError, KeyError):
        return False

def extract_player_match_data(game: Dict[str, Any], match: Dict[str, Any], player: str) -> Optional[Dict[str, Any]]:
    is_home = game.get("home_player") == player
    if not is_home and game.get("away_player") != player:
        return None
    
    code = game.get("home_code") if is_home else game.get("away_code")
    score = game["home_score"] if is_home else game["away_score"]
    opp_score = game["away_score"] if is_home else game["home_score"]
    opponent = game["away_player"] if is_home else game["home_player"]
    opponent_code = game["away_code"] if is_home else game["home_code"]
    sets_home = game.get("home_sets", []) if is_home else game.get("away_sets", [])
    sets_away = game.get("away_sets", []) if is_home else game.get("home_sets", [])
    
    player_team = get_real_team(code, match)
    opponent_team = get_real_team(opponent_code, match)
    result = RESULT_WIN if score > opp_score else RESULT_LOSS
    
    sets_html = []
    for h, a in zip(sets_home, sets_away):
        if h == 0 and a == 0:
            continue
        color = "green" if h > a else "red"
        sets_html.append(f"<span style='color:{color}'>{h}-{a}</span>")
    
    sets_str = " / ".join(sets_html)
    marcador = f"{score} - {opp_score}"
    
    return {
        "Fecha": match["date"],
        "Rival": opponent,
        "Equipo rival": opponent_team,
        "Marcador": marcador,
        "Sets": sets_str,
        "Resultado": result,
        "Lugar": match.get("venue", "")
    }

def is_valid_player_name(nombre: str) -> bool:
    if not nombre:
        return False
    n = nombre.upper()
    if n.startswith("DOBLE"):
        return False
    return n not in INVALID_PLAYER_NAMES

def get_team_regular_players(equipo: str) -> pd.Series:
    jugadores = []
    for match in matches:
        if equipo not in [match["home_team"], match["away_team"]]:
            continue
        
        games = match.get("games", [])
        if not games:
            continue
        
        for g in games:
            home = g.get("home_player", "").strip()
            away = g.get("away_player", "").strip()
            code_h = g.get("home_code", "")
            code_a = g.get("away_code", "")
            
            team_h = get_real_team(code_h, match)
            team_a = get_real_team(code_a, match)
            
            if is_valid_player_name(home) and team_h == equipo:
                jugadores.append(home)
            
            if is_valid_player_name(away) and team_a == equipo:
                jugadores.append(away)
    
    return pd.Series(jugadores).value_counts()

def get_team_elo_average(df: pd.DataFrame, equipo: str) -> float:
    elos = []
    for _, row in df.iterrows():
        for g in row.get("games", []):
            if row["home_team"] == equipo and g.get("home_player"):
                p = g["home_player"]
                info = elo_df[elo_df["player"] == p]
                if not info.empty:
                    elos.append(info["elo"].iloc[0])
            
            if row["away_team"] == equipo and g.get("away_player"):
                p = g["away_player"]
                info = elo_df[elo_df["player"] == p]
                if not info.empty:
                    elos.append(info["elo"].iloc[0])
    
    return round(sum(elos) / len(elos), 1) if elos else 0.0

def get_team_sets_average_diff(df: pd.DataFrame, equipo: str) -> float:
    diffs = []
    for _, row in df.iterrows():
        for g in row.get("games", []):
            if row["home_team"] == equipo:
                diffs.append(sum([h - a for h, a in zip(g["home_sets"], g["away_sets"]) if h or a]))
            elif row["away_team"] == equipo:
                diffs.append(sum([a - h for h, a in zip(g["home_sets"], g["away_sets"]) if h or a]))
    return round(sum(diffs) / len(diffs), 2) if diffs else 0.0

def get_team_recent_form(df: pd.DataFrame, equipo: str) -> str:
    filas = df[(df["home_team"] == equipo) | (df["away_team"] == equipo)].tail(5)
    r = []
    for _, p in filas.iterrows():
        sh, sa = p.get("score_home"), p.get("score_away")
        if sh is None or sa is None:
            continue
        if (p["home_team"] == equipo and sh > sa) or (p["away_team"] == equipo and sa > sh):
            r.append("🟩")
        else:
            r.append("🟥")
    return "".join(r)

def get_team_opponents(df: pd.DataFrame, equipo: str) -> Set[str]:
    r = []
    for _, p in df.iterrows():
        if p["home_team"] == equipo:
            r.append(p["away_team"])
        elif p["away_team"] == equipo:
            r.append(p["home_team"])
    return set(r)

def get_h2h_matches(df: pd.DataFrame, j1: str, j2: str) -> List[str]:
    res = []
    for _, m in df.iterrows():
        for g in m.get("games", []):
            if g["home_player"] == j1 and g["away_player"] == j2:
                res.append(f"{j1} {g['home_score']} - {g['away_score']} {j2}")
            if g["home_player"] == j2 and g["away_player"] == j1:
                res.append(f"{j2} {g['home_score']} - {g['away_score']} {j1}")
    return res

def get_best_player(df: pd.DataFrame, equipo: str) -> Tuple[Optional[str], float]:
    jugadores = []
    for _, row in df.iterrows():
        for g in row.get("games", []):
            if row["home_team"] == equipo and g.get("home_player"):
                jugadores.append(g["home_player"])
            elif row["away_team"] == equipo and g.get("away_player"):
                jugadores.append(g["away_player"])
    
    if not jugadores:
        return None, 0.0
    
    tabla = elo_df[elo_df["player"].isin(jugadores)]
    if tabla.empty:
        return None, 0.0
    
    fila = tabla.sort_values("elo", ascending=False).iloc[0]
    return fila["player"], fila["elo"]

def build_team_comparison_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, player_row in df.iterrows():
        player = player_row["player"]
        elo = player_row["elo"]
        wins, losses = get_stats(player)
        total_matches = wins + losses
        win_rate = round(wins / total_matches * 100, 1) if total_matches > 0 else 0.0
        
        rows.append({
            "Jugador": player,
            "Elo": elo,
            "V": wins,
            "D": losses,
            "Total": total_matches,
            "Tasa": f"{win_rate}%"
        })
    
    result_df = pd.DataFrame(rows)
    if not result_df.empty:
        result_df = result_df.sort_values(by="Elo", ascending=False)
    return result_df

def get_global_leaderboard() -> pd.DataFrame:
    rows = []
    for _, player_row in elo_df.iterrows():
        player = player_row["player"]
        elo = player_row["elo"]
        club = player_row["club"]
        wins, losses = get_stats(player)
        total_matches = wins + losses
        win_rate = round(wins / total_matches * 100, 1) if total_matches > 0 else 0.0
        
        rows.append({
            "Ranking": None,
            "Jugador": player,
            "Equipo": club,
            "Elo": elo,
            "V": wins,
            "D": losses,
            "Total": total_matches,
            "% Victoria": f"{win_rate}%"
        })
    
    result_df = pd.DataFrame(rows).sort_values(by="Elo", ascending=False).reset_index(drop=True)
    result_df["Ranking"] = range(1, len(result_df) + 1)
    return result_df[["Ranking", "Jugador", "Equipo", "Elo", "V", "D", "Total", "% Victoria"]]

def get_team_recent_form_trend(df: pd.DataFrame, equipo: str, last_n: int = 10) -> List[int]:
    filas = df[(df["home_team"] == equipo) | (df["away_team"] == equipo)]
    trend = []
    
    for _, p in filas.iterrows():
        try:
            games = p["games"]
            if not isinstance(games, list) or len(games) == 0:
                continue
            sh = p["score_home"]
            sa = p["score_away"]
            if sh is None or sa is None or (sh == 0 and sa == 0):
                continue
            if (p["home_team"] == equipo and sh > sa) or (p["away_team"] == equipo and sa > sh):
                trend.append(1)
            else:
                trend.append(0)
        except (KeyError, TypeError):
            continue
    
    return trend[-last_n:] if trend else []

def get_team_win_rate(df: pd.DataFrame, equipo: str, last_n: int = 10) -> float:
    trend = get_team_recent_form_trend(df, equipo, last_n)
    if not trend:
        return 0.0
    return round(sum(trend) / len(trend) * 100, 1)

def get_team_strengths_weaknesses(df: pd.DataFrame, team1: str, team2: str) -> Dict[str, List[str]]:
    team1_stats = get_team_sets_stats(df, team1)
    team2_stats = get_team_sets_stats(df, team2)
    
    team1_elo_avg = get_team_elo_average(df, team1)
    team2_elo_avg = get_team_elo_average(df, team2)
    
    team1_trend = get_team_recent_form_trend(df, team1, 10)
    team2_trend = get_team_recent_form_trend(df, team2, 10)
    
    team1_win_rate = round(sum(team1_trend) / len(team1_trend) * 100, 1) if team1_trend else 0.0
    team2_win_rate = round(sum(team2_trend) / len(team2_trend) * 100, 1) if team2_trend else 0.0
    
    team1_form = get_team_recent_form_trend(df, team1, 5)
    team2_form = get_team_recent_form_trend(df, team2, 5)
    
    strengths_1 = []
    weaknesses_1 = []
    strengths_2 = []
    weaknesses_2 = []
    
    if team1_elo_avg > team2_elo_avg:
        strengths_1.append(f"Plantilla más fuerte (Elo: {team1_elo_avg:.0f} vs {team2_elo_avg:.0f})")
    else:
        weaknesses_1.append(f"Plantilla más débil (Elo: {team1_elo_avg:.0f} vs {team2_elo_avg:.0f})")
    
    if team1_stats['avg_sets_won'] > team2_stats['avg_sets_won']:
        strengths_1.append(f"Mayor promedio de sets ganados ({team1_stats['avg_sets_won']:.2f} vs {team2_stats['avg_sets_won']:.2f})")
    else:
        weaknesses_1.append(f"Menor promedio de sets ganados ({team1_stats['avg_sets_won']:.2f} vs {team2_stats['avg_sets_won']:.2f})")
    
    if team1_win_rate > team2_win_rate:
        strengths_1.append(f"Mejor forma reciente ({team1_win_rate}% vs {team2_win_rate}%)")
    else:
        weaknesses_1.append(f"Peor forma reciente ({team1_win_rate}% vs {team2_win_rate}%)")
    
    if team2_elo_avg > team1_elo_avg:
        strengths_2.append(f"Plantilla más fuerte (Elo: {team2_elo_avg:.0f} vs {team1_elo_avg:.0f})")
    else:
        weaknesses_2.append(f"Plantilla más débil (Elo: {team2_elo_avg:.0f} vs {team1_elo_avg:.0f})")
    
    if team2_stats['avg_sets_won'] > team1_stats['avg_sets_won']:
        strengths_2.append(f"Mayor promedio de sets ganados ({team2_stats['avg_sets_won']:.2f} vs {team1_stats['avg_sets_won']:.2f})")
    else:
        weaknesses_2.append(f"Menor promedio de sets ganados ({team2_stats['avg_sets_won']:.2f} vs {team1_stats['avg_sets_won']:.2f})")
    
    if team2_win_rate > team1_win_rate:
        strengths_2.append(f"Mejor forma reciente ({team2_win_rate}% vs {team1_win_rate}%)")
    else:
        weaknesses_2.append(f"Peor forma reciente ({team2_win_rate}% vs {team1_win_rate}%)")
    
    return {
        f"{team1}_strengths": strengths_1,
        f"{team1}_weaknesses": weaknesses_1,
        f"{team2}_strengths": strengths_2,
        f"{team2}_weaknesses": weaknesses_2
    }

def get_player_vs_opponent_stats(player: str, opponent: str) -> Dict[str, Any]:
    duels = get_duels(player)
    matching_duels = [d for d in duels if d["rival"] == opponent]
    
    if not matching_duels:
        return {"matches": 0, "wins": 0, "losses": 0, "win_rate": 0.0}
    
    wins = sum(1 for d in matching_duels if d["resultado"] == RESULT_WIN)
    losses = len(matching_duels) - wins
    win_rate = round(wins / len(matching_duels) * 100, 1)
    
    return {
        "matches": len(matching_duels),
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate
    }

def build_h2h_matrix(df: pd.DataFrame) -> pd.DataFrame:
    all_players = sorted(elo_df["player"].unique())
    matrix = []
    
    for p1 in all_players:
        row = {"Jugador": p1}
        for p2 in all_players:
            if p1 == p2:
                row[p2] = "-"
            else:
                stats = get_player_vs_opponent_stats(p1, p2)
                if stats["matches"] > 0:
                    row[p2] = f"{stats['wins']}-{stats['losses']}"
                else:
                    row[p2] = ""
        matrix.append(row)
    
    return pd.DataFrame(matrix)

def get_best_worst_streaks(df: pd.DataFrame, equipo: str, window: int = 5) -> Tuple[str, str]:
    filas = df[(df["home_team"] == equipo) | (df["away_team"] == equipo)].tail(window)
    streak = get_team_recent_form_trend(df, equipo, window)
    
    if not streak:
        return "N/A", "N/A"
    
    recent_form = "".join(["🟩" if w else "🟥" for w in streak])
    avg_recent = round(sum(streak) / len(streak) * 100, 1) if streak else 0.0
    
    return recent_form, f"{avg_recent}%"

def get_team_vs_team_record(df: pd.DataFrame, team1: str, team2: str) -> Dict[str, int]:
    matches = df[
        ((df["home_team"] == team1) & (df["away_team"] == team2)) |
        ((df["home_team"] == team2) & (df["away_team"] == team1))
    ]
    
    team1_wins = 0
    team2_wins = 0
    
    for _, match in matches.iterrows():
        if match["home_team"] == team1 and match["score_home"] is not None:
            if match["score_home"] > match["score_away"]:
                team1_wins += 1
            else:
                team2_wins += 1
        elif match["home_team"] == team2 and match["score_home"] is not None:
            if match["score_away"] > match["score_home"]:
                team1_wins += 1
            else:
                team2_wins += 1
    
    return {"team1_wins": team1_wins, "team2_wins": team2_wins, "total": len(matches)}

def get_player_momentum(player: str, last_n: int = 5) -> Dict[str, Any]:
    duels = get_duels(player)
    recent_duels = duels[-last_n:]
    
    if not recent_duels:
        return {"wins": 0, "losses": 0, "momentum": 0.0, "streak": "N/A"}
    
    wins = sum(1 for d in recent_duels if d["resultado"] == RESULT_WIN)
    losses = len(recent_duels) - wins
    momentum = round(wins / len(recent_duels) * 100, 1)
    
    streak = ""
    for d in recent_duels:
        streak += "🟩" if d["resultado"] == RESULT_WIN else "🟥"
    
    return {
        "wins": wins,
        "losses": losses,
        "momentum": momentum,
        "streak": streak,
        "total": len(recent_duels)
    }

def get_team_momentum(df: pd.DataFrame, equipo: str, last_n: int = 5) -> Dict[str, Any]:
    filas = df[(df["home_team"] == equipo) | (df["away_team"] == equipo)].tail(last_n)
    trend = []
    
    for _, p in filas.iterrows():
        sh, sa = p.get("score_home"), p.get("score_away")
        if sh is None or sa is None:
            continue
        if (p["home_team"] == equipo and sh > sa) or (p["away_team"] == equipo and sa > sh):
            trend.append(1)
        else:
            trend.append(0)
    
    if not trend:
        return {"wins": 0, "losses": 0, "momentum": 0.0, "streak": "N/A"}
    
    wins = sum(trend)
    losses = len(trend) - wins
    momentum = round(wins / len(trend) * 100, 1)
    streak = "".join(["🟩" if w else "🟥" for w in trend])
    
    return {
        "wins": wins,
        "losses": losses,
        "momentum": momentum,
        "streak": streak,
        "total": len(trend)
    }

def get_player_sets_stats(player: str) -> Dict[str, float]:
    sets_won = 0
    sets_lost = 0
    matches_count = 0
    
    for match in matches:
        for g in match.get("games", []):
            if g.get("home_player") == player or g.get("away_player") == player:
                is_home = g["home_player"] == player
                h_sets = g.get("home_sets", [])
                a_sets = g.get("away_sets", [])
                
                if is_home:
                    sets_won += sum(1 for s in h_sets if s > 0)
                    sets_lost += sum(1 for s in a_sets if s > 0)
                else:
                    sets_won += sum(1 for s in a_sets if s > 0)
                    sets_lost += sum(1 for s in h_sets if s > 0)
                matches_count += 1
    
    avg_sets_won = round(sets_won / matches_count, 2) if matches_count > 0 else 0.0
    avg_sets_lost = round(sets_lost / matches_count, 2) if matches_count > 0 else 0.0
    
    return {
        "total_sets_won": sets_won,
        "total_sets_lost": sets_lost,
        "avg_sets_won": avg_sets_won,
        "avg_sets_lost": avg_sets_lost,
        "matches": matches_count
    }

def get_team_sets_stats(df: pd.DataFrame, equipo: str) -> Dict[str, float]:
    sets_won = 0
    sets_lost = 0
    matches_count = 0
    
    for _, row in df.iterrows():
        is_home = row["home_team"] == equipo
        is_away = row["away_team"] == equipo
        
        if not (is_home or is_away):
            continue
        
        for g in row.get("games", []):
            h_sets = g.get("home_sets", [])
            a_sets = g.get("away_sets", [])
            
            if is_home:
                for h, a in zip(h_sets, a_sets):
                    if h > 0 or a > 0:
                        if h > a:
                            sets_won += 1
                        else:
                            sets_lost += 1
            else:
                for h, a in zip(h_sets, a_sets):
                    if h > 0 or a > 0:
                        if a > h:
                            sets_won += 1
                        else:
                            sets_lost += 1
            matches_count += 1
    
    avg_sets_won = round(sets_won / matches_count, 2) if matches_count > 0 else 0.0
    avg_sets_lost = round(sets_lost / matches_count, 2) if matches_count > 0 else 0.0
    
    return {
        "total_sets_won": sets_won,
        "total_sets_lost": sets_lost,
        "avg_sets_won": avg_sets_won,
        "avg_sets_lost": avg_sets_lost,
        "matches": matches_count
    }

def get_player_recent_matches(player: str, last_n: int = 5) -> pd.DataFrame:
    duels = get_duels(player)
    recent_duels = duels[-last_n:]
    
    if not recent_duels:
        return pd.DataFrame(columns=["Casa/Away", "Rival", "Marcador", "Resultado"])
    
    results = []
    for d in recent_duels:
        results.append({
            "Casa/Away": d.get("casa_away", ""),
            "Rival": d["rival"],
            "Marcador": d["marcador"],
            "Resultado": d["resultado"]
        })
    
    return pd.DataFrame(results)

def get_team_recent_matches(df: pd.DataFrame, equipo: str, last_n: int = 5) -> pd.DataFrame:
    todas_filas = df[(df["home_team"] == equipo) | (df["away_team"] == equipo)]
    
    finalizadas = []
    for _, p in todas_filas.iterrows():
        games = p.get("games", None)
        if isinstance(games, list) and len(games) > 0:
            finalizadas.append(p)
    
    filas = finalizadas[-last_n:]
    
    results = []
    for p in filas:
        sh, sa = p.get("score_home"), p.get("score_away")
        if sh is None or sa is None:
            continue
        
        is_home = p["home_team"] == equipo
        opponent = p["away_team"] if is_home else p["home_team"]
        casa_away = "Casa" if is_home else "Away"
        
        team_score = sh if is_home else sa
        opponent_score = sa if is_home else sh
        won = team_score > opponent_score
        
        resultado = "Victoria" if won else "Derrota"
        results.append({
            "Casa/Away": casa_away,
            "Rival": opponent,
            "Marcador": f"{sh} - {sa}",
            "Resultado": resultado
        })
    
    return pd.DataFrame(results)

def get_team_matches_vs_opponent(df: pd.DataFrame, equipo: str, opponent: str) -> pd.DataFrame:
    matches = df[
        ((df["home_team"] == equipo) | (df["away_team"] == equipo)) &
        ((df["home_team"] == opponent) | (df["away_team"] == opponent)) &
        (df["status"] == "Finalizado")
    ]
    
    results = []
    for _, p in matches.iterrows():
        sh, sa = p.get("score_home"), p.get("score_away")
        if sh is None or sa is None:
            continue
        
        is_home = p["home_team"] == equipo
        casa_away = "Casa" if is_home else "Away"
        
        team_score = sh if is_home else sa
        opponent_score = sa if is_home else sh
        won = team_score > opponent_score
        
        resultado = "Victoria" if won else "Derrota"
        results.append({
            "Fecha": p.get("date", ""),
            "Casa/Away": casa_away,
            "Marcador": f"{sh} - {sa}",
            "Resultado": resultado
        })
    
    return pd.DataFrame(results)

def style_match_results(df: pd.DataFrame):
    def color_resultado(val):
        if val == "Victoria":
            return "background-color: #90EE90; color: black"
        elif val == "Derrota":
            return "background-color: #FF6B6B; color: white"
        return ""
    
    return df.style.map(color_resultado, subset=['Resultado'])

def display_match_duels_acta(games: list, home_team: str, away_team: str):
    regular_duels = [g for g in games if g.get('home_code') != "ABC" and g.get('away_code') != "XYZ"]
    
    if not regular_duels:
        st.info("No hay duelos para mostrar")
        return
    
    home_wins = sum(1 for g in regular_duels if g.get('home_score', 0) > g.get('away_score', 0))
    away_wins = sum(1 for g in regular_duels if g.get('away_score', 0) > g.get('home_score', 0))
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        st.markdown(f"### {home_team}")
    with col2:
        st.markdown(f"<div style='text-align: center;'><h3>{home_wins} - {away_wins}</h3></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div style='text-align: right;'><h3>{away_team}</h3></div>", unsafe_allow_html=True)
    
    st.divider()
    
    for idx, duel in enumerate(regular_duels, 1):
        home_player = duel['home_player']
        away_player = duel['away_player']
        home_code = duel['home_code']
        away_code = duel['away_code']
        home_sets = duel.get('home_sets', [])
        away_sets = duel.get('away_sets', [])
        
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 2])
            
            with col1:
                st.markdown(f"**{home_player}** ({home_code})")
            with col2:
                st.markdown(f"<div style='text-align: center; font-weight: bold;'>{idx}</div>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"<div style='text-align: right;'>**{away_player}** ({away_code})</div>", unsafe_allow_html=True)
            
            sets_display = []
            for i, (h, a) in enumerate(zip(home_sets, away_sets), 1):
                if h == 0 and a == 0:
                    continue
                h_style = "color: green; font-weight: bold;" if h > a else "color: gray;"
                a_style = "color: green; font-weight: bold;" if a > h else "color: gray;"
                sets_display.append(f"<span style='{h_style}'>{h}</span> - <span style='{a_style}'>{a}</span>")
            
            if sets_display:
                sets_str = " | ".join(sets_display)
                st.markdown(f"<div style='text-align: center; margin-top: 5px;'>{sets_str}</div>", unsafe_allow_html=True)
            
            st.divider()


elo_df = load_elo_data(ELO_FILE)
matches = load_matches(MATCHES_FILE)
df_grupo = load_matches_by_group(grupo)

for col in EXPECTED_COLS:
    if col not in df_grupo.columns:
        df_grupo[col] = None

vista = st.session_state.nav_vista
page_title = get_page_title()
st.title(f"🏓 {page_title}")

# 👤 Comparar jugadores
if vista == "Comparar jugadores":
    st.subheader("👤 Comparación entre dos jugadores")

    equipos = sorted(elo_df["club"].unique())
    col1, col2 = st.columns(2)

    with col1:
        equipo1 = st.selectbox("Equipo para Jugador 1", ["Todos"] + equipos, key="jugador1_equipo")
    with col2:
        equipo2 = st.selectbox("Equipo para Jugador 2", ["Todos"] + equipos, key="jugador2_equipo")

    jugadores1 = elo_df["player"].tolist() if equipo1 == "Todos" else elo_df[elo_df["club"] == equipo1]["player"].tolist()
    jugadores2 = elo_df["player"].tolist() if equipo2 == "Todos" else elo_df[elo_df["club"] == equipo2]["player"].tolist()

    col1, col2 = st.columns(2)
    with col1:
        jugador1 = st.selectbox("Jugador 1", jugadores1, key="jugador1")
    with col2:
        jugador2 = st.selectbox("Jugador 2", jugadores2, key="jugador2")

    def mostrar_ficha(jugador, col_key):
        info = elo_df[elo_df["player"] == jugador].iloc[0]
        wins, losses = get_stats(jugador)
        momentum = get_player_momentum(jugador, 5)
        sets_stats = get_player_sets_stats(jugador)
        st.markdown(f"### {jugador}")
        st.write(f"**Equipo** : {info['club']}")
        st.write(f"**Elo** : {info['elo']}")
        st.write(f"**Victorias** : {wins} | **Derrotas** : {losses}")
        recent_matches_df = get_player_recent_matches(jugador, 5)
        if not recent_matches_df.empty:
            st.subheader("📅 Últimos 5 partidos")
            st.dataframe(style_match_results(recent_matches_df), use_container_width=True, hide_index=True)
        st.write(f"**Sets**: Ø {sets_stats['avg_sets_won']} ganados / {sets_stats['avg_sets_lost']} perdidos")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button(f"📋 Perfil", key=f"profile_{col_key}"):
                navigate_to_player(jugador)
        with col_btn2:
            if st.button(f"⚽ Equipo", key=f"team_{col_key}"):
                navigate_to_team(info['club'])

    col1, col2 = st.columns(2)
    with col1:
        mostrar_ficha(jugador1, "j1")
    with col2:
        mostrar_ficha(jugador2, "j2")

    st.subheader("📈 Evolución Elo")
    fig, ax = plt.subplots()
    ax.plot(plot_elo(jugador1), label=jugador1)
    ax.plot(plot_elo(jugador2), label=jugador2)
    ax.set_ylabel("Elo")
    ax.set_xlabel("Partidos")
    ax.legend()
    st.pyplot(fig)

    st.subheader("🔁 Oponentes comunes")
    comunes = get_common_opponents(jugador1, jugador2)
    if comunes:
        for o in comunes:
            d1 = next((d for d in get_duels(jugador1) if d["rival"] == o), None)
            d2 = next((d for d in get_duels(jugador2) if d["rival"] == o), None)
            st.write(f"🆚 {o}")
            st.write(f"• {jugador1} : {d1['marcador']} ({d1['resultado']})")
            st.write(f"• {jugador2} : {d2['marcador']} ({d2['resultado']})")
    else:
        st.info("No hay oponentes comunes.")

# 👥 Comparar equipos
elif vista == "Comparar equipos":
    st.subheader("👥 Comparación entre dos equipos")
    equipos = sorted(elo_df["club"].unique())
    
    idx1 = 0
    idx2 = 1 if len(equipos) > 1 else 0
    
    if st.session_state.nav_equipo1 and st.session_state.nav_equipo1 in equipos:
        idx1 = equipos.index(st.session_state.nav_equipo1)
        st.session_state.nav_equipo1 = None
    
    if st.session_state.nav_equipo2 and st.session_state.nav_equipo2 in equipos:
        idx2 = equipos.index(st.session_state.nav_equipo2)
        st.session_state.nav_equipo2 = None
    
    col1, col2 = st.columns(2)
    with col1:
        equipo1 = st.selectbox("Equipo 1", equipos, index=idx1, key="equipo1")
    with col2:
        equipo2 = st.selectbox("Equipo 2", equipos, index=idx2, key="equipo2")

    df1 = elo_df[elo_df["club"] == equipo1]
    df2 = elo_df[elo_df["club"] == equipo2]

    momentum1 = get_team_momentum(df_grupo, equipo1, 5)
    momentum2 = get_team_momentum(df_grupo, equipo2, 5)
    sets1 = get_team_sets_stats(df_grupo, equipo1)
    sets2 = get_team_sets_stats(df_grupo, equipo2)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### {equipo1}")
        table1 = build_team_comparison_table(df1)
        st.dataframe(table1, use_container_width=True)
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Elo medio", round(df1["elo"].mean(), 1))
        with col_b:
            st.metric("Momentum", f"{momentum1['momentum']}%")
        with col_c:
            st.metric("Ø Sets", f"{sets1['avg_sets_won']}/{sets1['avg_sets_lost']}")
        recent1_df = get_team_recent_matches(df_grupo, equipo1, 5)
        if not recent1_df.empty:
            st.subheader("📅 Últimos 5 partidos")
            st.dataframe(style_match_results(recent1_df), use_container_width=True, hide_index=True)
        if st.button(f"📊 Dashboard {equipo1}", key="dash_equipo1"):
            navigate_to_team(equipo1)
    with col2:
        st.markdown(f"### {equipo2}")
        table2 = build_team_comparison_table(df2)
        st.dataframe(table2, use_container_width=True)
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Elo medio", round(df2["elo"].mean(), 1))
        with col_b:
            st.metric("Momentum", f"{momentum2['momentum']}%")
        with col_c:
            st.metric("Ø Sets", f"{sets2['avg_sets_won']}/{sets2['avg_sets_lost']}")
        recent2_df = get_team_recent_matches(df_grupo, equipo2, 5)
        if not recent2_df.empty:
            st.subheader("📅 Últimos 5 partidos")
            st.dataframe(style_match_results(recent2_df), use_container_width=True, hide_index=True)
        if st.button(f"📊 Dashboard {equipo2}", key="dash_equipo2"):
            navigate_to_team(equipo2)
elif vista == "Resumen por jugador":
    st.subheader("📋 Perfil detallado del jugador")

    jugadores = elo_df["player"].tolist()
    
    default_idx = 0
    if st.session_state.nav_jugador and st.session_state.nav_jugador in jugadores:
        default_idx = jugadores.index(st.session_state.nav_jugador)
        st.session_state.nav_jugador = None
    
    jugador = st.selectbox("Selecciona un jugador", jugadores, index=default_idx, key="perfil_jugador")

    info = elo_df[elo_df["player"] == jugador].iloc[0]
    wins, losses = get_stats(jugador)
    momentum = get_player_momentum(jugador, 5)
    sets_stats = get_player_sets_stats(jugador)

    st.markdown(f"### {jugador}")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**Equipo**: {info['club']}")
        st.write(f"**Elo actual**: {info['elo']}")
        st.write(f"**Victorias**: {wins}")
        st.write(f"**Derrotas**: {losses}")
    with col2:
        if st.button(f"📊 Ver equipo", key="team_button"):
            navigate_to_team(info['club'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Momentum (últimos 5)", f"{momentum['momentum']}%")
    with col2:
        st.metric("Partidos", len(get_duels(jugador)))
    with col3:
        st.metric("Ø Sets Ganados", sets_stats['avg_sets_won'])
    with col4:
        st.metric("Ø Sets Perdidos", sets_stats['avg_sets_lost'])
    
    recent_df = get_player_recent_matches(jugador, 5)
    if not recent_df.empty:
        st.subheader("📅 Últimos 5 partidos")
        st.dataframe(style_match_results(recent_df), use_container_width=True, hide_index=True)

    st.subheader("📈 Evolución Elo")
    fig, ax = plt.subplots()
    ax.plot(plot_elo(jugador), label=jugador, color="blue")
    ax.set_ylabel("Elo")
    ax.set_xlabel("Partidos")
    ax.legend()
    st.pyplot(fig)

    st.subheader("📊 Historial de partidos")

    historial = []
    for match in matches:
        for g in match.get("games", []):
            match_data = extract_player_match_data(g, match, jugador)
            if match_data:
                historial.append(match_data)




    df_historial = pd.DataFrame(historial)
    df_historial.index += 1
    st.write("📊 verde = ganado, rojo = perdido")
    st.write(df_historial.to_html(escape=False, index=True), unsafe_allow_html=True)
elif vista == "Ranking y H2H":
    st.header("🏆 Ranking Global del Grupo")
    
    leaderboard = get_global_leaderboard()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Jugadores", len(leaderboard))
    with col2:
        st.metric("Elo Promedio", round(elo_df["elo"].mean(), 1))
    with col3:
        st.metric("Máximo Elo", int(elo_df["elo"].max()))
    
    st.subheader("📊 Tabla de Posiciones")
    
    st.write("*Haz clic en un jugador para ver su perfil detallado*")
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 3, 2, 1, 1, 1, 2])
    with col1:
        st.write("**#**")
    with col2:
        st.write("**Jugador**")
    with col3:
        st.write("**Equipo**")
    with col4:
        st.write("**Elo**")
    with col5:
        st.write("**V**")
    with col6:
        st.write("**D**")
    with col7:
        st.write("**% Victoria**")
    
    st.divider()
    
    for idx, row in leaderboard.iterrows():
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 3, 2, 1, 1, 1, 2])
        with col1:
            st.write(f"**{row['Ranking']}**")
        with col2:
            if st.button(f"{row['Jugador']}", key=f"rank_player_{idx}"):
                navigate_to_player(row['Jugador'])
        with col3:
            st.write(row['Equipo'])
        with col4:
            st.write(f"{row['Elo']}")
        with col5:
            st.write(f"{row['V']}")
        with col6:
            st.write(f"{row['D']}")
        with col7:
            st.write(row['% Victoria'])
    
    st.subheader("🎯 Filtros")
    equipo_filter = st.selectbox("Filtrar por equipo", ["Todos"] + sorted(elo_df["club"].unique()), key="ranking_equipo")
    
    if equipo_filter != "Todos":
        filtered_lb = leaderboard[leaderboard["Equipo"] == equipo_filter]
        st.write(f"**Jugadores de {equipo_filter}:**")
        
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 3, 2, 1, 1, 1, 2])
        with col1:
            st.write("**#**")
        with col2:
            st.write("**Jugador**")
        with col3:
            st.write("**Equipo**")
        with col4:
            st.write("**Elo**")
        with col5:
            st.write("**V**")
        with col6:
            st.write("**D**")
        with col7:
            st.write("**% Victoria**")
        
        st.divider()
        
        for idx, row in filtered_lb.iterrows():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 3, 2, 1, 1, 1, 2])
            with col1:
                st.write(f"**{row['Ranking']}**")
            with col2:
                if st.button(f"{row['Jugador']}", key=f"filter_player_{idx}"):
                    navigate_to_player(row['Jugador'])
            with col3:
                st.write(row['Equipo'])
            with col4:
                st.write(f"{row['Elo']}")
            with col5:
                st.write(f"{row['V']}")
            with col6:
                st.write(f"{row['D']}")
            with col7:
                st.write(row['% Victoria'])

    st.divider()
    st.header("⚔️ Matriz Head-to-Head")
    
    st.info("Muestra el record de cada jugador vs otros jugadores. Formato: Victorias-Derrotas")
    
    h2h_df = build_h2h_matrix(df_all)
    
    st.subheader("Matriz Completa")
    st.dataframe(h2h_df, use_container_width=True)
    
    st.subheader("🔍 Análisis Individual")
    default_h2h_idx = 0
    if st.session_state.nav_jugador and st.session_state.nav_jugador in sorted(elo_df["player"].unique()):
        default_h2h_idx = sorted(elo_df["player"].unique()).index(st.session_state.nav_jugador)
        st.session_state.nav_jugador = None
    
    jugador = st.selectbox("Selecciona un jugador", sorted(elo_df["player"].unique()), index=default_h2h_idx, key="h2h_jugador")
    
    if jugador:
        duels = get_duels(jugador)
        rivals_data = []
        
        for d in duels:
            rival = d["rival"]
            opponent_info = elo_df[elo_df["player"] == rival]
            opponent_elo = opponent_info["elo"].iloc[0] if not opponent_info.empty else 0
            
            rivals_data.append({
                "Rival": rival,
                "Elo": opponent_elo,
                "Marcador": d["marcador"],
                "Resultado": d["resultado"]
            })
        
        if rivals_data:
            rivals_df = pd.DataFrame(rivals_data).sort_values("Elo", ascending=False)
            st.write("*Haz clic en un rival para ver su perfil*")
            for idx, row in rivals_df.iterrows():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                with col1:
                    if st.button(f"{row['Rival']}", key=f"rival_player_{idx}"):
                        navigate_to_player(row['Rival'])
                with col2:
                    st.write(f"{row['Elo']}")
                with col3:
                    st.write(f"{row['Marcador']}")
                with col4:
                    st.write(row['Resultado'])
                with col5:
                    pass

# 📅 Calendario de partidos
elif vista == "Calendario de partidos":
    st.header("📅 Calendario de partidos")

    if df_grupo.empty:
        st.warning("No hay datos disponibles.")
        st.stop()

    equipo_filtro = st.selectbox(
        "Filtrar calendario por equipo",
        ["Todos"] + sorted(set(m["home_team"] for m in matches) | set(m["away_team"] for m in matches)),
        key="filtro_equipo"
    )

    partidos = df_grupo.copy()

# --- Filtre par equipo ---
    if equipo_filtro != "Todos":
        partidos = partidos[
            (partidos["home_team"] == equipo_filtro) |
            (partidos["away_team"] == equipo_filtro)
        ]

    partidos = partidos[["match_id", "date", "home_team", "away_team"]].copy()

    # Label lisible
    partidos["label"] = partidos.apply(
        lambda r: f"{r['date']} – {r['home_team']} vs {r['away_team']}",
        axis=1
    )

    selected_label = st.selectbox("Selecciona un partido", partidos["label"].tolist())
    selected_match_id = partidos[partidos["label"] == selected_label].iloc[0]["match_id"]

    selected_match = df_grupo[df_grupo["match_id"] == selected_match_id].iloc[0]

    st.subheader("📌 Detalles del partido")

    st.write(f"**Fecha:** {selected_match['date']}")
    st.write(f"**Equipos:** {selected_match['home_team']} vs {selected_match['away_team']}")

    # MATCH FINALISÉ
    games = selected_match.get("games", None)

    if isinstance(games, list) and len(games) > 0:
        st.success(f"Acta disponible ({len(games)} duelos)")

        display_match_duels_acta(games, selected_match["home_team"], selected_match["away_team"])
        
        has_doble_home = any(g["home_code"] == "ABC" for g in games)
        has_doble_away = any(g["away_code"] == "XYZ" for g in games)
        
        if has_doble_home or has_doble_away:
            st.subheader("⚠️ Dobles en este partido")
            if has_doble_home:
                st.warning(f"{selected_match['home_team']} jugó doble (ABC).")
            if has_doble_away:
                st.warning(f"{selected_match['away_team']} jugó doble (XYZ).")

    else:
        st.header("🔮 Análisis de Partido Futuro")

        home = selected_match["home_team"]
        away = selected_match["away_team"]

        st.subheader("🔍 Análisis completo del partido")

        doble_home = any(
            g.get("home_code") in {"ABC"} for g in selected_match.get("games", [])
        )
        doble_away = any(
            g.get("away_code") in {"XYZ"} for g in selected_match.get("games", [])
        )

        if doble_home or doble_away:
            st.subheader("⚠️ Presencia de dobles")
            if doble_home:
                st.warning(f"{home} ha alineado doble en partidos anteriores.")
            if doble_away:
                st.warning(f"{away} ha alineado doble en partidos anteriores.")

        st.subheader("👥 Jugadores habituales")

        reg_home = get_team_regular_players(home).index.tolist()
        reg_away = get_team_regular_players(away).index.tolist()

        df_home_players = elo_df[elo_df["player"].isin(reg_home)]
        df_away_players = elo_df[elo_df["player"].isin(reg_away)]

        tabla_home = build_team_comparison_table(df_home_players)
        tabla_away = build_team_comparison_table(df_away_players)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### {home}")
            st.dataframe(tabla_home, use_container_width=True)

        with col2:
            st.markdown(f"### {away}")
            st.dataframe(tabla_away, use_container_width=True)



        diff_home = get_team_sets_average_diff(df_grupo, home)
        diff_away = get_team_sets_average_diff(df_grupo, away)

        st.subheader("📊 Estadísticas de Sets")
        col1, col2 = st.columns(2)

        home_sets_stats = get_team_sets_stats(df_grupo, home)
        away_sets_stats = get_team_sets_stats(df_grupo, away)

        with col1:
            st.markdown(f"### {home}")
            st.metric("Matchs jugados", home_sets_stats['matches'])
            st.metric("Sets ganados (promedio)", f"{home_sets_stats['avg_sets_won']:.2f}", 
                      delta=f"{home_sets_stats['total_sets_won']} sobre {home_sets_stats['total_sets_won'] + home_sets_stats['total_sets_lost']}")
            st.metric("Sets perdidos (promedio)", f"{home_sets_stats['avg_sets_lost']:.2f}",
                      delta=f"{home_sets_stats['total_sets_lost']} sobre {home_sets_stats['total_sets_won'] + home_sets_stats['total_sets_lost']}")

        with col2:
            st.markdown(f"### {away}")
            st.metric("Matchs jugados", away_sets_stats['matches'])
            st.metric("Sets ganados (promedio)", f"{away_sets_stats['avg_sets_won']:.2f}",
                      delta=f"{away_sets_stats['total_sets_won']} sobre {away_sets_stats['total_sets_won'] + away_sets_stats['total_sets_lost']}")
            st.metric("Sets perdidos (promedio)", f"{away_sets_stats['avg_sets_lost']:.2f}",
                      delta=f"{away_sets_stats['total_sets_lost']} sobre {away_sets_stats['total_sets_won'] + away_sets_stats['total_sets_lost']}")


        st.subheader("📈 Forma reciente (últimos 5)")
        col1, col2 = st.columns(2)
        
        home_recent_df = get_team_recent_matches(df_grupo, home, 5)
        away_recent_df = get_team_recent_matches(df_grupo, away, 5)
        
        with col1:
            st.markdown(f"**{home}**")
            if not home_recent_df.empty:
                st.dataframe(style_match_results(home_recent_df), use_container_width=True, hide_index=True)
            else:
                st.info("Sin partidos finalizados")
        
        with col2:
            st.markdown(f"**{away}**")
            if not away_recent_df.empty:
                st.dataframe(style_match_results(away_recent_df), use_container_width=True, hide_index=True)
            else:
                st.info("Sin partidos finalizados")

        st.subheader("📋 Tabla Comparativa")
        home_elo_avg = get_team_elo_average(df_grupo, home)
        away_elo_avg = get_team_elo_average(df_grupo, away)
        
        home_trend = get_team_recent_form_trend(df_grupo, home, 10)
        away_trend = get_team_recent_form_trend(df_grupo, away, 10)
        
        home_win_rate = round(sum(home_trend) / len(home_trend) * 100, 1) if home_trend else 0.0
        away_win_rate = round(sum(away_trend) / len(away_trend) * 100, 1) if away_trend else 0.0

        comparison_data = {
            "Métrica": ["Elo promedio", "Sets ganados (prom)", "Sets perdidos (prom)", "Win Rate (últimos 10)", "Matchs jugados"],
            home: [
                f"{home_elo_avg:.0f}",
                f"{home_sets_stats['avg_sets_won']:.2f}",
                f"{home_sets_stats['avg_sets_lost']:.2f}",
                f"{home_win_rate}%",
                home_sets_stats['matches']
            ],
            away: [
                f"{away_elo_avg:.0f}",
                f"{away_sets_stats['avg_sets_won']:.2f}",
                f"{away_sets_stats['avg_sets_lost']:.2f}",
                f"{away_win_rate}%",
                away_sets_stats['matches']
            ]
        }

        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

        st.subheader("💡 Análisis de Fuerzas y Debilidades")
        analysis = get_team_strengths_weaknesses(df_grupo, home, away)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### 💪 {home}")
            st.markdown("**Fortalezas:**")
            for strength in analysis[f"{home}_strengths"]:
                st.markdown(f"- {strength}")
            st.markdown("**Debilidades:**")
            for weakness in analysis[f"{home}_weaknesses"]:
                st.markdown(f"- {weakness}")

        with col2:
            st.markdown(f"### 💪 {away}")
            st.markdown("**Fortalezas:**")
            for strength in analysis[f"{away}_strengths"]:
                st.markdown(f"- {strength}")
            st.markdown("**Debilidades:**")
            for weakness in analysis[f"{away}_weaknesses"]:
                st.markdown(f"- {weakness}")

        comunes = get_team_opponents(df_grupo, home).intersection(get_team_opponents(df_grupo, away))

        st.subheader("🤝 Rivales comunes")
        if comunes:
            st.write(comunes)
        else:
            st.write("Ninguno")

        st.subheader("📂 Partidos finalizados contra rivales comunes")

        df_home_f = df_grupo[
            ((df_grupo["home_team"] == home) | (df_grupo["away_team"] == home)) &
            (df_grupo["status"] == "Finalizado")
        ]

        df_away_f = df_grupo[
            ((df_grupo["home_team"] == away) | (df_grupo["away_team"] == away)) &
            (df_grupo["status"] == "Finalizado")
        ]

        def adversarios(df: pd.DataFrame, equipo: str) -> Set[str]:
            r = []
            for _, p in df.iterrows():
                if p["home_team"] == equipo:
                    r.append(p["away_team"])
                else:
                    r.append(p["home_team"])
            return set(r)

        adv_home = adversarios(df_home_f, home)
        adv_away = adversarios(df_away_f, away)

        comunes = adv_home.intersection(adv_away)

        if not comunes:
            st.write("No hay rivales comunes.")
        else:
            for rival in sorted(comunes):
                st.markdown(f"### 🤝 Rival común: **{rival}**")

                col1, col2 = st.columns(2)
                
                home_matches_df = get_team_matches_vs_opponent(df_grupo, home, rival)
                away_matches_df = get_team_matches_vs_opponent(df_grupo, away, rival)

                with col1:
                    st.markdown(f"**{home}** vs {rival}")
                    if not home_matches_df.empty:
                        st.dataframe(style_match_results(home_matches_df), use_container_width=True, hide_index=True)
                    else:
                        st.info("Sin partidos")

                with col2:
                    st.markdown(f"**{away}** vs {rival}")
                    if not away_matches_df.empty:
                        st.dataframe(style_match_results(away_matches_df), use_container_width=True, hide_index=True)
                    else:
                        st.info("Sin partidos")

                st.markdown("---")

        st.subheader("⚔️ Enfrentamientos directos entre jugadores")

        jugadores_H = get_team_regular_players(home).head(3).index.tolist()
        jugadores_A = get_team_regular_players(away).head(3).index.tolist()

        for j1 in jugadores_H:
            for j2 in jugadores_A:
                duelos = get_h2h_matches(df_grupo, j1, j2)
                if duelos:
                    st.markdown(f"**{j1} vs {j2}**")
                    for d in duelos:
                        st.write("• " + d)


        st.subheader("🔮 Predicción (basada en Elo promedio)")

        elo_home = get_team_elo_average(df_grupo, home)
        elo_away = get_team_elo_average(df_grupo, away)
        if elo_home == 0 or elo_away == 0:
            st.info("No hay datos suficientes de Elo para calcular una predicción.")
        else:
            if elo_home > elo_away:
                st.success(f"📌 **Predicción**: {home} es favorito ({elo_home} > {elo_away})")
            elif elo_home < elo_away:
                st.success(f"📌 **Predicción**: {away} es favorito ({elo_away} > {elo_home})")
            else:
                st.warning("📌 Predicción: Iguales, partido muy equilibrado.")

        st.subheader("🌟 Jugadores destacados")

        reg_home = get_team_regular_players(home)
        reg_away = get_team_regular_players(away)

        if not reg_home.empty:
            home_players_elo = elo_df[elo_df["player"].isin(reg_home.index)]
            if not home_players_elo.empty:
                best_home = home_players_elo.sort_values("elo", ascending=False).iloc[0]
                st.write(f"⭐ Mejor jugador de **{home}**: {best_home['player']} (Elo {best_home['elo']})")

        if not reg_away.empty:
            away_players_elo = elo_df[elo_df["player"].isin(reg_away.index)]
            if not away_players_elo.empty:
                best_away = away_players_elo.sort_values("elo", ascending=False).iloc[0]
                st.write(f"⭐ Mejor jugador de **{away}**: {best_away['player']} (Elo {best_away['elo']})")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Comparación Completa de Equipos", use_container_width=True):
                st.session_state.nav_vista = "Comparar equipos"
                st.session_state.nav_equipo1 = home
                st.session_state.nav_equipo2 = away
                st.rerun()
        with col2:
            st.write("Haz clic para ver un análisis completo con estadísticas detalladas")

elif vista == "Dashboard Equipo":
    st.header("📈 Dashboard del Equipo")
    
    equipos_list = sorted(set(m["home_team"] for m in matches) | set(m["away_team"] for m in matches))
    default_equipo_idx = 0
    
    if st.session_state.nav_equipo and st.session_state.nav_equipo in equipos_list:
        default_equipo_idx = equipos_list.index(st.session_state.nav_equipo)
        st.session_state.nav_equipo = None
    
    equipo = st.selectbox("Selecciona un equipo", equipos_list, index=default_equipo_idx)
    
    team_players = elo_df[elo_df["club"] == equipo]
    momentum = get_team_momentum(df_grupo, equipo, 5)
    sets_stats = get_team_sets_stats(df_grupo, equipo)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Jugadores", len(team_players))
    with col2:
        st.metric("Elo Promedio", round(team_players["elo"].mean(), 1))
    with col3:
        st.metric("Momentum", f"{momentum['momentum']}%")
    with col4:
        st.metric("Ø Sets", f"{sets_stats['avg_sets_won']}/{sets_stats['avg_sets_lost']}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Elo Máximo", int(team_players["elo"].max()))
    with col2:
        pass
    with col3:
        pass
    
    recent_df = get_team_recent_matches(df_grupo, equipo, 5)
    if not recent_df.empty:
        st.subheader("📅 Últimos 5 partidos")
        st.dataframe(style_match_results(recent_df), use_container_width=True, hide_index=True)
    
    st.subheader("👥 Jugadores del Equipo")
    st.write("*Haz clic en un jugador para ver su perfil detallado*")
    team_table = build_team_comparison_table(team_players)
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 3, 1, 1, 1, 1, 2])
    with col1:
        st.write("**#**")
    with col2:
        st.write("**Jugador**")
    with col3:
        st.write("**Elo**")
    with col4:
        st.write("**V**")
    with col5:
        st.write("**D**")
    with col6:
        st.write("**Total**")
    with col7:
        st.write("**Tasa**")
    
    st.divider()
    
    for idx, row in team_table.iterrows():
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 3, 1, 1, 1, 1, 2])
        with col1:
            st.write(f"**{idx + 1}**")
        with col2:
            if st.button(f"{row['Jugador']}", key=f"team_player_{idx}"):
                navigate_to_player(row['Jugador'])
        with col3:
            st.write(f"{row['Elo']}")
        with col4:
            st.write(f"{row['V']}")
        with col5:
            st.write(f"{row['D']}")
        with col6:
            st.write(f"{row['Total']}")
        with col7:
            st.write(row['Tasa'])
    
    st.subheader("📥 Descargar Reporte")
    csv = team_table.to_csv(index=False)
    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name=f"reporte_{equipo}.csv",
        mime="text/csv"
    )
    
    st.subheader("📉 Evolución Elo (Top 3)")
    top_3 = team_table.head(3)["Jugador"].tolist()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    for player in top_3:
        ax.plot(plot_elo(player), label=player, marker='o')
    ax.set_ylabel("Elo")
    ax.set_xlabel("Partidos")
    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

elif vista == "Análisis Jugador Avanzado":
    st.header("🔬 Análisis Avanzado del Jugador")
    
    jugador = st.selectbox("Selecciona un jugador", sorted(elo_df["player"].unique()), key="advanced_jugador")
    
    if jugador:
        info = elo_df[elo_df["player"] == jugador].iloc[0]
        wins, losses = get_stats(jugador)
        total = wins + losses
        win_rate = round(wins / total * 100, 1) if total > 0 else 0
        momentum = get_player_momentum(jugador, 5)
        sets_stats = get_player_sets_stats(jugador)
        
        st.subheader(f"📋 {jugador}")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Equipo", info["club"])
        with col2:
            st.metric("Elo", info["elo"])
        with col3:
            st.metric("Victorias", wins)
        with col4:
            st.metric("Derrotas", losses)
        with col5:
            st.metric("% Victoria", f"{win_rate}%")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📈 Momentum (últimos 5)", f"{momentum['momentum']}%")
        with col2:
            st.metric("Partidos", len(get_duels(jugador)))
        with col3:
            st.metric("Ø Sets Ganados", sets_stats['avg_sets_won'])
        with col4:
            st.metric("Ø Sets Perdidos", sets_stats['avg_sets_lost'])
        
        recent_df = get_player_recent_matches(jugador, 5)
        if not recent_df.empty:
            st.subheader("📅 Últimos 5 partidos")
            st.dataframe(style_match_results(recent_df), use_container_width=True, hide_index=True)
        
        st.subheader("📈 Evolución Elo")
        fig, ax = plt.subplots(figsize=(12, 5))
        elo_history = plot_elo(jugador)
        ax.plot(elo_history, marker='o', linewidth=2, color='steelblue')
        ax.fill_between(range(len(elo_history)), elo_history, alpha=0.3)
        ax.set_ylabel("Elo Rating")
        ax.set_xlabel("Partidos")
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        
        st.subheader("🆚 Performance vs Niveles")
        duels = get_duels(jugador)
        
        top_tier = []
        mid_tier = []
        low_tier = []
        
        for d in duels:
            rival = d["rival"]
            opponent_info = elo_df[elo_df["player"] == rival]
            if not opponent_info.empty:
                opponent_elo = opponent_info["elo"].iloc[0]
                is_win = d["resultado"] == RESULT_WIN
                
                if opponent_elo >= 1600:
                    top_tier.append(is_win)
                elif opponent_elo >= 1400:
                    mid_tier.append(is_win)
                else:
                    low_tier.append(is_win)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            top_wr = round(sum(top_tier) / len(top_tier) * 100, 1) if top_tier else 0
            st.metric("vs Top (1600+)", f"{top_wr}% ({len(top_tier)} duelos)")
        with col2:
            mid_wr = round(sum(mid_tier) / len(mid_tier) * 100, 1) if mid_tier else 0
            st.metric("vs Mid (1400-1600)", f"{mid_wr}% ({len(mid_tier)} duelos)")
        with col3:
            low_wr = round(sum(low_tier) / len(low_tier) * 100, 1) if low_tier else 0
            st.metric("vs Low (<1400)", f"{low_wr}% ({len(low_tier)} duelos)")

elif vista == "Clasificación":
    st.header("🏆 Clasificación de Equipos")
    
    standings_df = load_standings(grupo_id)
    
    if standings_df.empty:
        st.warning(f"No hay datos de clasificación para {grupo}")
    else:
        st.subheader(f"📊 {grupo}")
        
        display_cols = ["position", "team", "matches", "wins", "losses", "points_for", "points_against", "points_diff", "points"]
        display_df = standings_df[display_cols].copy()
        display_df.columns = ["Pos", "Equipo", "J", "G", "P", "PF", "PC", "PD", "Pts"]
        display_df.index = display_df.index + 1
        
        st.dataframe(display_df, use_container_width=True)
        
        st.subheader("📈 Estadísticas del Grupo")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Equipos", len(standings_df))
        with col2:
            st.metric("Promedio Puntos", round(standings_df["points"].mean(), 1))
        with col3:
            st.metric("Promedio Matches", round(standings_df["matches"].mean(), 1))
        with col4:
            st.metric("Máxima Diferencia", max(standings_df["points_diff"]) if len(standings_df) > 0 else 0)
        
        st.subheader("🔝 Top 3 Equipos")
        top_3 = standings_df.head(3)
        for idx, (_, row) in enumerate(top_3.iterrows(), 1):
            st.write(f"**{idx}. {row['team']}** - {row['points']} puntos ({row['wins']}V-{row['losses']}P)")
        
        st.subheader("📊 Diferencia de Puntos por Equipo")
        fig, ax = plt.subplots(figsize=(12, 6))
        teams = standings_df["team"].tolist()
        diffs = standings_df["points_diff"].tolist()
        colors = ["green" if d >= 0 else "red" for d in diffs]
        ax.barh(teams, diffs, color=colors)
        ax.set_xlabel("Diferencia de Puntos (PF - PC)")
        ax.set_title(f"Diferencia de Puntos - {grupo}")
        st.pyplot(fig)
