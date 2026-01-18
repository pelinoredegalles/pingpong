from bs4 import BeautifulSoup

with open(r'data\standings_html\standings_14110.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), "html.parser")

group_divs = soup.find_all("div", class_="standings-groups")
for group_div in group_divs:
    h4 = group_div.find("h4", class_="standings-groups-title")
    if not h4:
        continue
    
    group_text = h4.get_text(strip=True)
    if group_text != "Grupo 6":
        continue
    
    print(f"Found {group_text}")
    table = group_div.find("table", class_="standings-table")
    if not table:
        print("Table not found")
        continue
    
    rows = table.find_all("tr")[1:]
    print(f"Found {len(rows)} rows")
    
    for i, row in enumerate(rows[:3], 1):
        cells = row.find_all(["td", "th"])
        print(f"\nRow {i}: {len(cells)} cells")
        
        pos_span = cells[0].find("span")
        position = int(pos_span.get_text(strip=True)) if pos_span else 0
        
        team_link = cells[1].find("a")
        team_name = team_link.find("span").get_text(strip=True) if team_link else ""
        
        matches = int(cells[2].get_text(strip=True))
        wins = int(cells[3].get_text(strip=True))
        losses = int(cells[4].get_text(strip=True))
        
        print(f"  Position: {position}")
        print(f"  Team: {team_name}")
        print(f"  Matches: {matches}, Wins: {wins}, Losses: {losses}")
