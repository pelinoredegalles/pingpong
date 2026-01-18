import re
with open(r'data\standings_html\standings_14110.html', 'r', encoding='utf-8') as f:
    content = f.read()
    groups = re.findall(r'standings-groups-title">([^<]+)<', content)
    for i, g in enumerate(groups, 1):
        print(f"{i}. {g.strip()}")
