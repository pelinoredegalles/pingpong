import os
import re
import json
import asyncio
import logging
import requests
from typing import Dict, List, Tuple, Optional, Any
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm_asyncio
from asyncio import Semaphore
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

COMPETITIONS: Dict[int, str] = {
    14110: "Grupo 6",
    14109: "Grupo 7"
}

TARGET_GROUPS: Dict[int, str] = {
    14110: "Grupo 6",
    14109: "Grupo 7"
}
BASE_URL: str = "https://competicion.fatm.eu"
NETWORK_TIMEOUT: int = 30
MAX_MATCHES_PER_REQUEST: int = 2000
SEMAPHORE_LIMIT: int = 4
MAX_SETS: int = 5
MIN_GAMES_FOR_VALID_MATCH: int = 6
TOTAL_GAMES_WITH_DOUBLE: int = 7
DOUBLE_GAME_INDEX: int = 6

ABC_CODES: set = {"A", "B", "C", "ABC"}
XYZ_CODES: set = {"X", "Y", "Z", "XYZ"}

OUT_DIR: str = os.path.join(os.path.dirname(__file__), "data")
HTML_DIR: str = os.path.join(OUT_DIR, "actas_html")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)

def strip_html(s: Optional[str]) -> str:
    return re.sub(r'<[^>]+>', '', s or '').strip()

def get_global_score(result_html: str) -> Tuple[int, int]:
    try:
        mH = re.search(r'scoreHome" value="(\d+)', result_html)
        mA = re.search(r'scoreAway" value="(\d+)', result_html)
        if mH and mA:
            return int(mH.group(1)), int(mA.group(1))
        m = re.search(r'>(\d+)\s*-\s*(\d+)<', result_html)
        if m:
            return int(m.group(1)), int(m.group(2))
    except ValueError as e:
        logger.warning(f"Error parsing score: {e}")
    return 0, 0

def get_matches_json(competition_id: int) -> Dict[str, Any]:
    try:
        r = requests.post(
            f"{BASE_URL}/es/competition/loadMatchesDatatable/{competition_id}",
            headers={"User-Agent": "Mozilla/5.0"},
            data={"start": 0, "length": MAX_MATCHES_PER_REQUEST},
            timeout=NETWORK_TIMEOUT
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        logger.warning(f"Network error for competition {competition_id}: {e}")
        return {"aaData": []}

def get_all_group_matches(json_data: Dict[str, Any], competition_id: int, target_group: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for m in json_data.get("aaData", []):
        if m.get("groupround") != target_group:
            continue
        scores = get_global_score(m.get("result", ""))
        out.append({
            "match_id": m.get("row_id"),
            "competition": competition_id,
            "group": m.get("groupround"),
            "date": m.get("date"),
            "time": m.get("time"),
            "venue": strip_html(m.get("venue")),
            "home_team": strip_html(m.get("home")),
            "away_team": strip_html(m.get("away")),
            "score_home": scores[0],
            "score_away": scores[1],
            "result": strip_html(m.get("result")),
            "status": m.get("status"),
            "games": []
        })
    return out

def get_standings(html_content: Optional[str], competition_id: int) -> Dict[str, Any]:
    if not html_content:
        logger.warning(f"No HTML content provided for competition {competition_id}")
        return {}
    
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        target_group = TARGET_GROUPS.get(competition_id, "")
        
        standings: Dict[str, List[Dict[str, Any]]] = {}
        
        group_divs = soup.find_all("div", class_="standings-groups")
        for group_div in group_divs:
            h4 = group_div.find("h4", class_="standings-groups-title")
            if not h4:
                continue
            
            group_text = h4.get_text(strip=True)
            if group_text != target_group:
                continue
            
            table = group_div.find("table", class_="standings-table")
            if not table:
                logger.warning(f"Table not found for {group_text}")
                continue
            
            teams: List[Dict[str, Any]] = []
            rows = table.find_all("tr")[1:]
            logger.info(f"Found {len(rows)} team rows in {group_text}")
            
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) < 11:
                    continue
                
                try:
                    pos_span = cells[0].find("span")
                    position = int(pos_span.get_text(strip=True)) if pos_span else 0
                    
                    team_link = cells[1].find("a")
                    team_name = team_link.find("span").get_text(strip=True) if team_link else ""
                    
                    matches = int(cells[2].get_text(strip=True))
                    wins = int(cells[3].get_text(strip=True))
                    losses = int(cells[4].get_text(strip=True))
                    points_for = int(cells[5].get_text(strip=True))
                    points_against = int(cells[6].get_text(strip=True))
                    points_diff = int(cells[7].get_text(strip=True))
                    
                    points_strong = cells[-1].find("strong")
                    points = int(points_strong.get_text(strip=True)) if points_strong else 0
                    
                    teams.append({
                        "position": position,
                        "team": team_name,
                        "matches": matches,
                        "wins": wins,
                        "losses": losses,
                        "points_for": points_for,
                        "points_against": points_against,
                        "points_diff": points_diff,
                        "points": points
                    })
                except (ValueError, IndexError, AttributeError) as e:
                    logger.debug(f"Error parsing team row: {e}")
                    continue
            
            if teams:
                standings[group_text] = teams
                logger.info(f"✅ Parsed {len(teams)} teams for {group_text}")
        
        return standings
    
    except Exception as e:
        logger.error(f"Error parsing standings for competition {competition_id}: {e}")
        return {}

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

STANDINGS_DIR: str = os.path.join(OUT_DIR, "standings_html")
os.makedirs(STANDINGS_DIR, exist_ok=True)

sem: Semaphore = Semaphore(SEMAPHORE_LIMIT)

async def limited_fetch(playwright: Any, match_id: str, competition_id: int) -> None:
    async with sem:
        await fetch_acta_html(playwright, match_id, competition_id)
        await asyncio.sleep(1)

async def fetch_standings_html(playwright: Any, competition_id: int) -> Optional[str]:
    html_path = os.path.join(STANDINGS_DIR, f"standings_{competition_id}.html")
    if os.path.exists(html_path):
        logger.info(f"⏩ Standings HTML already present for competition {competition_id}, skipping download.")
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()

    try:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        url = f"{BASE_URL}/es/competition/view/{competition_id}#standings"
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_selector("div.standings-results", timeout=20000)

        standings_container = await page.query_selector("div.standings-results")
        if standings_container:
            html = await standings_container.inner_html()
        else:
            logger.warning(f"Standings container not found for competition {competition_id}")
            html = None
        
        if html:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            logger.info(f"💾 Standings file saved: {html_path}")

        await browser.close()
        return html

    except Exception as e:
        logger.error(f"Error fetching standings for competition {competition_id}: {e}")
        return None

async def fetch_acta_html(playwright: Any, match_id: str, competition_id: int) -> None:
    html_path = os.path.join(HTML_DIR, f"debug_li_summary_{match_id}.html")
    if os.path.exists(html_path):
        logger.info(f"⏩ HTML already present for match {match_id}, skipping download.")
        return

    try:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        url = f"{BASE_URL}/es/matches/view/{match_id}/c-{competition_id}"
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("domcontentloaded")

        tab = await page.query_selector("a[data-content='summary']")
        if not tab:
            logger.warning(f"Acta tab not found for match {match_id}")
            await browser.close()
            return

        await tab.click()
        await page.wait_for_selector("li[data-content='summary'] table", timeout=20000)

        li_html = await page.eval_on_selector(
            "li[data-content='summary']",
            "el => el.innerHTML"
        )

        if li_html:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(li_html)
            logger.info(f"💾 File saved: {html_path}")

        await browser.close()

    except Exception as e:
        logger.error(f"Error for match {match_id}: {e}")

def parse_acta_file(filepath: str, match: Dict[str, Any]) -> List[Dict[str, Any]]:
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("div#sub-matches-container table") or soup.select_one("table")
    if not table:
        logger.warning(f"Table not found in {filepath}")
        return []

    rows = table.select("tr")
    games: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    for tr in rows:
        tds = tr.find_all("td")
        if not tds:
            continue

        text_cells = [td.get_text(strip=True) for td in tds if td.get_text(strip=True)]
        if len(text_cells) < 3:
            continue

        code = text_cells[0]
        player = text_cells[1]
        digits = [int(x) for x in text_cells[2:] if x.isdigit()]
        sets = digits[:MAX_SETS] if len(digits) >= MAX_SETS else []
        score = digits[MAX_SETS] if len(digits) > MAX_SETS else 0

        if code in ABC_CODES:
            current = {
                "home_code": code,
                "home_player": player,
                "home_sets": sets,
                "home_score": score
            }
        elif current and code in XYZ_CODES:
            current.update({
                "away_code": code,
                "away_player": player,
                "away_sets": sets,
                "away_score": score
            })
            games.append(current)
            current = None

    if len(games) < TOTAL_GAMES_WITH_DOUBLE:
        return games[:MIN_GAMES_FOR_VALID_MATCH]

    if len(games) >= TOTAL_GAMES_WITH_DOUBLE:
        home_team = get_club_from_code(games[DOUBLE_GAME_INDEX].get("home_code"), match)
        away_team = get_club_from_code(games[DOUBLE_GAME_INDEX].get("away_code"), match)
        games[DOUBLE_GAME_INDEX]["home_player"] = f"Doble {home_team}"
        games[DOUBLE_GAME_INDEX]["away_player"] = f"Doble {away_team}"

    return games

async def process_competition(comp_id: int, group_name: str) -> None:
    safe_name = re.sub(r'[^A-Za-z0-9]', '', group_name)
    json_data = get_matches_json(comp_id)
    matches = get_all_group_matches(json_data, comp_id, group_name)
    logger.info(f"\n📦 {len(matches)} matches retrieved in {group_name}")

    raw_path = os.path.join(OUT_DIR, f"matches_{safe_name}.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)

    finalizados = [m for m in matches if m.get("status") == "Finalizado"]

    async with async_playwright() as p:
        tasks = [limited_fetch(p, m["match_id"], comp_id) for m in finalizados]
        if tasks:
            await tqdm_asyncio.gather(*tasks, desc=f"Downloading Actas {group_name}")

    for m in finalizados:
        html_file = os.path.join(HTML_DIR, f"debug_li_summary_{m['match_id']}.html")
        if os.path.exists(html_file):
            games = parse_acta_file(html_file, m)
            m["games"] = games

    enriched_path = os.path.join(OUT_DIR, f"matches_{safe_name}_enriched.json")
    with open(enriched_path, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ Enriched file saved: {enriched_path}")

    async with async_playwright() as p:
        standings_html = await fetch_standings_html(p, comp_id)
    
    standings = get_standings(standings_html, comp_id)
    if standings:
        standings_path = os.path.join(OUT_DIR, f"standings_{safe_name}.json")
        with open(standings_path, "w", encoding="utf-8") as f:
            json.dump(standings, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Standings file saved: {standings_path}")
    else:
        logger.warning(f"⚠️ No standings data retrieved for {group_name}")

async def main() -> None:
    for comp_id, group_name in COMPETITIONS.items():
        await process_competition(comp_id, group_name)

if __name__ == "__main__":
    asyncio.run(main())
