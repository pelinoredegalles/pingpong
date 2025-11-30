import asyncio
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

MIN_DATE = datetime(2024, 9, 1)
MAX_DATE = datetime(2025, 7, 31)
BASE_URL = "https://competicion.fatm.eu"

month_map = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
    'Ene': 1, 'Abr': 4, 'Ago': 8, 'Dic': 12,
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
    'Febrero': 2, 'Enero': 1, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6,
    'Julio': 7, 'Agosto': 8, 'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
}

def parse_date(date_str: str):
    if not date_str:
        return None
    date_str = date_str.strip()
    try:
        parts = date_str.split()
        if len(parts) >= 3:
            day = int(parts[0])
            month_str = parts[1]
            year_str = parts[2]
            month = month_map.get(month_str) or month_map.get(month_str.lower())
            if month:
                year = int(year_str)
                if year < 100:
                    year = 2000 + year if year < 50 else 1900 + year
                hour = minute = 0
                if len(parts) >= 4:
                    time_parts = parts[3].split(':')
                    if len(time_parts) >= 2:
                        hour, minute = int(time_parts[0]), int(time_parts[1])
                return datetime(year, month, day, hour, minute)
    except:
        pass
    return None

def is_date_in_range(date_str: str) -> bool:
    date_obj = parse_date(date_str)
    return MIN_DATE <= date_obj <= MAX_DATE if date_obj else False

def clean_player_name(name: str) -> str:
    return re.sub(r'^0\.\s+', '', name).strip()

def extract_matches_from_html(html_content: str):
    soup = BeautifulSoup(html_content, "html.parser")
    matches = []
    
    fixture_tables = soup.find_all("table", class_="fixture")
    
    for table in fixture_tables:
        fixture_rows = table.find_all("tr", class_="fixture-undefined")
        
        for row in fixture_rows:
            try:
                metadata_table = row.find("table", class_="fixture-metadata")
                if not metadata_table:
                    continue
                
                tds = metadata_table.find_all("td")
                if len(tds) < 3:
                    continue
                
                date_time_str = tds[2].get_text(strip=True)
                if not date_time_str or not is_date_in_range(date_time_str):
                    continue
                
                result_td = row.find("td", class_="result")
                local_td = row.find("td", class_="local")
                away_td = row.find("td", class_="away")
                
                if not all([result_td, local_td, away_td]):
                    continue
                
                home_span = local_td.find("span", class_="venue-team-name")
                away_span = away_td.find("span", class_="venue-team-name")
                
                home_player = home_span.get_text(strip=True) if home_span else "Unknown"
                away_player = away_span.get_text(strip=True) if away_span else "Unknown"
                
                match_score = re.search(r'(\d+)\s*-\s*(\d+)', result_td.get_text())
                if match_score:
                    home_score = int(match_score.group(1))
                    away_score = int(match_score.group(2))
                else:
                    home_score = away_score = 0
                
                if home_score == 0 and away_score == 0:
                    continue
                
                league_td = tds[1] if len(tds) > 1 else None
                strong_tag = league_td.find("strong") if league_td else None
                league = strong_tag.get_text(strip=True) if strong_tag else (league_td.get_text(strip=True) if league_td else "Unknown")
                
                match_id = ""
                data_href = row.get("data-href", "")
                if data_href:
                    m = re.search(r'/matches/view/(\d+)/', data_href)
                    if m:
                        match_id = m.group(1)
                
                matches.append({
                    "date": date_time_str,
                    "match_id": match_id,
                    "home_player": home_player,
                    "away_player": away_player,
                    "home_score": home_score,
                    "away_score": away_score,
                    "league": league
                })
            except:
                continue
    
    return matches

async def extract_teams():
    """STEP 1: Extract all team URLs from team/view/61461"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto("https://competicion.fatm.eu/es/team/view/61366", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)
        
        content = await page.content()
        await browser.close()
        
        soup = BeautifulSoup(content, "html.parser")
        text_clamps = soup.find_all("div", class_="text-clamp")
        
        teams = []
        for elem in text_clamps:
            link = elem.find("a")
            if link:
                href = link.get('href', '')
                if href and '/team/view/' in href:
                    match = re.search(r'/team/view/(\d+)-', href)
                    if match:
                        team_id = match.group(1)
                        team_name = link.get_text(strip=True)
                        teams.append({
                            'id': team_id,
                            'name': team_name,
                            'url': f"https://competicion.fatm.eu/es/team/view/{team_id}"
                        })
        
        print(f"Found {len(teams)} teams")
        return teams

async def extract_players_from_team(team_url):
    """Extract all players from a team page"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(team_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)
        
        content = await page.content()
        await browser.close()
        
        soup = BeautifulSoup(content, "html.parser")
        member_items = soup.find_all("div", class_="member-item")
        
        players = []
        for item in member_items:
            onclick = item.get('onclick', '')
            if onclick and 'profile/view' in onclick:
                match = re.search(r'/profile/view/(\d+)-', onclick)
                if match:
                    player_id = match.group(1)
                    player_name = item.get_text(strip=True)
                    players.append({
                        'id': player_id,
                        'name': player_name
                    })
        
        return players

async def fetch_player_matches(player_id: str):
    """STEP 3: Fetch and extract matches for a player"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            profile_url = f"{BASE_URL}/es/profile/view/{player_id}"
            
            await page.goto(profile_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1000)
            
            content = await page.content()
            await browser.close()
            
            matches = extract_matches_from_html(content)
            return matches
    except Exception as e:
        print(f"[ERROR] Failed to fetch player {player_id}: {e}")
        return []

def determine_result(home_player: str, away_player: str, home_score: int, away_score: int, player_name: str) -> str:
    """Determine if player won, lost, or drew"""
    clean_player = clean_player_name(player_name)
    clean_home = clean_player_name(home_player)
    clean_away = clean_player_name(away_player)
    
    is_home = clean_player == clean_home
    is_away = clean_player == clean_away
    
    if not (is_home or is_away):
        return "unknown"
    
    if is_home:
        if home_score > away_score:
            return "won"
        elif home_score < away_score:
            return "lost"
        else:
            return "draw"
    else:
        if away_score > home_score:
            return "won"
        elif away_score < home_score:
            return "lost"
        else:
            return "draw"

async def main():
    print("=" * 60)
    print("STEP 1: Extracting teams from team/view/61461...")
    print("=" * 60)
    
    teams = await extract_teams()
    
    print("\nTeams found:")
    for team in teams:
        print(f"  {team['id']}: {team['name']}")
    
    print("\n" + "=" * 60)
    print("STEP 2: Extracting players from each team...")
    print("=" * 60)
    
    all_players = {}
    players_list = []
    
    for team in teams:
        print(f"\nFetching players from {team['name']}...")
        players = await extract_players_from_team(team['url'])
        all_players[team['id']] = {
            'team_name': team['name'],
            'players': players,
            'count': len(players)
        }
        for player in players:
            players_list.append({
                'team_id': team['id'],
                'team_name': team['name'],
                'player_id': player['id'],
                'player_name': player['name']
            })
        print(f"  Found {len(players)} players")
    
    print("\n" + "=" * 60)
    print("STEP 3: Fetching historical matches for all players...")
    print("=" * 60)
    
    all_matches = []
    total_players = len(players_list)
    
    for idx, player in enumerate(players_list, 1):
        print(f"[{idx}/{total_players}] Fetching matches for {player['player_name']} ({player['player_id']})...")
        matches = await fetch_player_matches(player['player_id'])
        
        for match in matches:
            clean_name = clean_player_name(player['player_name'])
            result = determine_result(match['home_player'], match['away_player'], match['home_score'], match['away_score'], player['player_name'])
            
            match['player_id'] = player['player_id']
            match['player_name'] = clean_name
            match['team_id'] = player['team_id']
            match['team_name'] = player['team_name']
            match['result'] = result
            all_matches.append(match)
        
        print(f"  Found {len(matches)} matches")
    
    with open("historique_grupo7_complete.json", "w", encoding="utf-8") as f:
        json.dump(all_matches, f, ensure_ascii=False, indent=2)
    
    with open("grupo7_players_by_team.json", "w", encoding="utf-8") as f:
        json.dump(all_players, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for team_id, data in all_players.items():
        print(f"{data['team_name']}: {data['count']} players")
    
    total_players_count = sum(data['count'] for data in all_players.values())
    print(f"\nTotal players: {total_players_count}")
    print(f"Total matches found: {len(all_matches)}")
    print(f"\nResults saved to:")
    print(f"  - historique_grupo7_complete.json (all matches)")
    print(f"  - grupo7_players_by_team.json (players by team)")

if __name__ == "__main__":
    asyncio.run(main())
