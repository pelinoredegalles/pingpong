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

df_all = load_matches_data()

EXPECTED_COLS = ["match_id", "date", "home_team", "away_team", "games", "score_home", "score_away"]
for col in EXPECTED_COLS:
    if col not in df_all.columns:
        df_all[col] = None

data_dir = os.path.join(os.path.dirname(__file__), "data")
st.set_page_config(page_title="Comparador Elo", layout="wide")

if "nav_vista" not in st.session_state:
    st.session_state.nav_vista = "Comparar jugadores"
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

elo_df = load_elo_data(ELO_FILE)
matches = load_matches(MATCHES_FILE)

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
                duels.append({
                    "rival": opponent,
                    "marcador": f"{score} - {opp_score}",
                    "resultado": result
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
                result = score / (score + opp_score) if (score + opp_score) > 0 else 0.5
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
        sh, sa = p["score_home"], p["score_away"]
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
            if row["away_team"] == equipo and g.get("away_player"):
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
    filas = df[(df["home_team"] == equipo) | (df["away_team"] == equipo)].tail(last_n)
    trend = []
    for _, p in filas.iterrows():
        sh, sa = p["score_home"], p["score_away"]
        if sh is None or sa is None:
            continue
        if (p["home_team"] == equipo and sh > sa) or (p["away_team"] == equipo and sa > sh):
            trend.append(1)
        else:
            trend.append(0)
    return trend

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
        st.markdown(f"### {jugador}")
        st.write(f"**Equipo** : {info['club']}")
        st.write(f"**Elo** : {info['elo']}")
        st.write(f"**Victorias** : {wins}")
        st.write(f"**Derrotas** : {losses}")
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

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"### {equipo1}")
        table1 = build_team_comparison_table(df1)
        st.dataframe(table1, use_container_width=True)
        st.metric("Elo medio", round(df1["elo"].mean(), 1))
        if st.button(f"📊 Dashboard {equipo1}", key="dash_equipo1"):
            navigate_to_team(equipo1)
    with col2:
        st.markdown(f"### {equipo2}")
        table2 = build_team_comparison_table(df2)
        st.dataframe(table2, use_container_width=True)
        st.metric("Elo medio", round(df2["elo"].mean(), 1))
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

    st.subheader("📈 Evolución Elo")
    fig, ax = plt.subplots()
    ax.plot(plot_elo(jugador), label=jugador, color="blue")
    ax.set_ylabel("Elo")
    ax.set_xlabel("Partidos")
    ax.legend()
    st.pyplot(fig)

    st.subheader("📊 Historial de partidos")

    historial = []
    for match in partidos_filtrados:
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

    if df_all.empty:
        st.warning("No hay datos disponibles.")
        st.stop()

    equipo_filtro = st.selectbox(
        "Filtrar calendario por equipo",
        ["Todos"] + sorted(set(m["home_team"] for m in matches) | set(m["away_team"] for m in matches)),
        key="filtro_equipo"
    )

    # Créer liste compacte
    partidos = df_all.copy()

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

    selected_match = df_all[df_all["match_id"] == selected_match_id].iloc[0]

    st.subheader("📌 Detalles del partido")

    st.write(f"**Fecha:** {selected_match['date']}")
    st.write(f"**Equipos:** {selected_match['home_team']} vs {selected_match['away_team']}")

    # MATCH FINALISÉ
    games = selected_match.get("games", None)

    if isinstance(games, list) and len(games) > 0:
        st.success(f"Acta disponible ({len(games)} duelos)")

        for duel in games:
            st.write(f"🎾 **{duel['home_player']} ({duel['home_code']})** "
                     f"vs **{duel['away_player']} ({duel['away_code']})**")
            st.write(f"Sets: {duel['home_sets']} – {duel['away_sets']}")
            st.write("---")
        
        st.subheader("⚠️ Dobles en este partido")

        if any(g["home_code"] == "ABC" for g in games):
            st.warning(f"{selected_match['home_team']} jugó doble (ABC).")

        if any(g["away_code"] == "XYZ" for g in games):
            st.warning(f"{selected_match['away_team']} jugó doble (XYZ).")

        if not any(g["home_code"] == "ABC" for g in games) and \
           not any(g["away_code"] == "XYZ" for g in games):
            st.info("No hubo dobles en este partido.")

    else:
        st.header("🔮 Análisis de Partido Futuro")

        home = selected_match["home_team"]
        away = selected_match["away_team"]

        st.subheader("🔍 Análisis completo del partido")

        st.subheader("⚠️ Presencia de dobles")

        doble_home = any(
            g.get("home_code") in {"ABC"} for g in selected_match.get("games", [])
        )
        doble_away = any(
            g.get("away_code") in {"XYZ"} for g in selected_match.get("games", [])
        )

        if doble_home:
            st.warning(f"{home} ha alineado doble en partidos anteriores.")
        if doble_away:
            st.warning(f"{away} ha alineado doble en partidos anteriores.")

        if not doble_home and not doble_away:
            st.info("Ninguno de los equipos ha alineado dobles recientemente.")

        st.subheader("👥 Jugadores habituales")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(get_team_regular_players(home).head(5))
        with col2:
            st.write(get_team_regular_players(away).head(5))


        diff_home = get_team_sets_average_diff(df_all, home)
        diff_away = get_team_sets_average_diff(df_all, away)

        st.subheader("➗ Diferencia promedio de sets")
        col1, col2 = st.columns(2)
        col1.metric(home, diff_home)
        col2.metric(away, diff_away)


        st.subheader("📈 Forma reciente (últimos 5)")
        st.write(f"{home}: {get_team_recent_form(df_all, home)}")
        st.write(f"{away}: {get_team_recent_form(df_all, away)}")

        comunes = get_team_opponents(df_all, home).intersection(get_team_opponents(df_all, away))

        st.subheader("🤝 Rivales comunes")
        if comunes:
            st.write(comunes)
        else:
            st.write("Ninguno")

        st.subheader("📂 Partidos finalizados contra rivales comunes")

        df_home_f = df_all[
            ((df_all["home_team"] == home) | (df_all["away_team"] == home)) &
            (df_all["status"] == "Finalizado")
        ]

        df_away_f = df_all[
            ((df_all["home_team"] == away) | (df_all["away_team"] == away)) &
            (df_all["status"] == "Finalizado")
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
            for rival in comunes:
                st.markdown(f"### 🤝 Rival común: **{rival}**")

                mH = df_home_f[
                    (df_home_f["home_team"] == home) & (df_home_f["away_team"] == rival)
                    | (df_home_f["away_team"] == home) & (df_home_f["home_team"] == rival)
                ]

                mA = df_away_f[
                    (df_away_f["home_team"] == away) & (df_away_f["away_team"] == rival)
                    | (df_away_f["away_team"] == away) & (df_away_f["home_team"] == rival)
                ]

                if not mH.empty:
                    for _, p in mH.iterrows():
                        st.write(
                            f"{home} **{p['score_home']}–{p['score_away']}** {rival}"
                            if p['home_team'] == home
                            else f"{home} **{p['score_away']}–{p['score_home']}** {rival}"
                        )

                if not mA.empty:
                    for _, p in mA.iterrows():
                        st.write(
                            f"{away} **{p['score_home']}–{p['score_away']}** {rival}"
                            if p['home_team'] == away
                            else f"{away} **{p['score_away']}–{p['score_home']}** {rival}"
                        )

                st.markdown("---")

        st.subheader("⚔️ Enfrentamientos directos entre jugadores")

        jugadores_H = get_team_regular_players(home).head(3).index.tolist()
        jugadores_A = get_team_regular_players(away).head(3).index.tolist()

        for j1 in jugadores_H:
            for j2 in jugadores_A:
                duelos = get_h2h_matches(df_all, j1, j2)
                if duelos:
                    st.markdown(f"**{j1} vs {j2}**")
                    for d in duelos:
                        st.write("• " + d)


        st.subheader("🔮 Predicción (basada en Elo promedio)")

        elo_home = get_team_elo_average(df_all, home)
        elo_away = get_team_elo_average(df_all, away)
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

        bh, elo_h = get_best_player(df_all, home)
        ba, elo_a = get_best_player(df_all, away)

        if bh:
            st.write(f"⭐ Mejor jugador de **{home}**: {bh} (Elo {elo_h})")

        if ba:
            st.write(f"⭐ Mejor jugador de **{away}**: {ba} (Elo {elo_a})")
        
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
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Jugadores", len(team_players))
    with col2:
        st.metric("Elo Promedio", round(team_players["elo"].mean(), 1))
    with col3:
        st.metric("Elo Máximo", int(team_players["elo"].max()))
    with col4:
        recent, pct = get_best_worst_streaks(df_all, equipo, 5)
        st.metric("Forma Reciente", recent)
    
    st.subheader("👥 Jugadores del Equipo")
    st.write("*Haz clic en un jugador para ver su perfil detallado*")
    team_table = build_team_comparison_table(team_players)
    
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
