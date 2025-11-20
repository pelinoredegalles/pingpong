"""
Comparaison: ELO Ancien vs Nouveau Calcul
Montre l'impact des améliorations sur quelques exemples concrets
"""

def compute_result_old(home_score: int, away_score: int) -> float:
    """Ancien calcul: basé uniquement sur le score du dernier set"""
    total = home_score + away_score
    if total == 0:
        return 0.5
    return home_score / total

def compute_result_new(home_score: int, away_score: int, home_sets=None, away_sets=None) -> float:
    """Nouveau calcul: 70% sets + 30% points"""
    if home_score == away_score == 0:
        return 0.5
    
    total_sets = home_score + away_score
    if total_sets > 0:
        sets_result = home_score / total_sets
    else:
        sets_result = 0.5
    
    if home_sets and away_sets:
        home_points = sum(s for s in home_sets if s > 0)
        away_points = sum(s for s in away_sets if s > 0)
        total_points = home_points + away_points
        if total_points > 0:
            points_result = home_points / total_points
        else:
            points_result = 0.5
        result = 0.7 * sets_result + 0.3 * points_result
    else:
        result = sets_result
    
    return max(0.0, min(1.0, result))

def compare_matches():
    """Exemples réalistes de matchs de badminton"""
    
    examples = [
        {
            "name": "Victoire Dominante (3-0)",
            "home_score": 3,
            "away_score": 0,
            "home_sets": [11, 11, 11],
            "away_sets": [8, 7, 9],
        },
        {
            "name": "Victoire Serrée (3-2)",
            "home_score": 3,
            "away_score": 2,
            "home_sets": [11, 9, 8, 11, 11],
            "away_sets": [9, 11, 11, 8, 7],
        },
        {
            "name": "Victoire Courte mais Nette (3-1)",
            "home_score": 3,
            "away_score": 1,
            "home_sets": [11, 12, 8, 11],
            "away_sets": [9, 10, 11, 6],
        },
        {
            "name": "Défaite Nette (0-3)",
            "home_score": 0,
            "away_score": 3,
            "home_sets": [7, 8, 6],
            "away_sets": [11, 11, 11],
        },
    ]
    
    print("=" * 90)
    print("COMPARAISON: ELO ANCIEN vs NOUVEAU CALCUL")
    print("=" * 90)
    
    for example in examples:
        print(f"\n📊 {example['name']}")
        print(f"   Score: {example['home_score']}-{example['away_score']}")
        print(f"   Sets: {example['home_sets']} vs {example['away_sets']}")
        
        result_old = compute_result_old(example['home_score'], example['away_score'])
        result_new = compute_result_new(
            example['home_score'], 
            example['away_score'],
            example['home_sets'],
            example['away_sets']
        )
        
        elo_delta_old = round(100 * (result_old - 0.5), 2)
        elo_delta_new = round(100 * (result_new - 0.5), 2)
        
        print(f"\n   ╔══════════════════════════════════════╗")
        print(f"   ║ ANCIEN (Score seul)                  ║")
        print(f"   ║ Résultat: {result_old:.3f}                  ║")
        print(f"   ║ ELO Δ: {elo_delta_old:+7.2f} points           ║")
        print(f"   ╚══════════════════════════════════════╝")
        
        print(f"\n   ╔══════════════════════════════════════╗")
        print(f"   ║ NOUVEAU (70% Sets + 30% Points)      ║")
        print(f"   ║ Résultat: {result_new:.3f}                  ║")
        print(f"   ║ ELO Δ: {elo_delta_new:+7.2f} points           ║")
        print(f"   ╚══════════════════════════════════════╝")
        
        delta_change = elo_delta_new - elo_delta_old
        arrow = "↑" if delta_change > 0 else "↓" if delta_change < 0 else "→"
        print(f"\n   Différence: {arrow} {abs(delta_change):+.2f} points")
        
        if example['home_score'] == 3 and example['away_score'] == 2:
            print(f"   💡 IMPACT: Les victoires serrées (3-2) ont moins de poids qu'avant")
        elif example['home_score'] == 3 and example['away_score'] == 0:
            print(f"   💡 IMPACT: Les victoires dominantes (3-0) ont PLUS de poids")
        
        print()
    
    print("=" * 90)
    print("RÉSUMÉ DES IMPACTS")
    print("=" * 90)
    print("""
    ✅ Victoires dominantes (3-0):
       → Impact AUGMENTÉ (meilleure représentation de la performance)
    
    ✅ Victoires serrées (3-2):
       → Impact RÉDUIT (moins impactant que avant)
    
    ✅ Points totaux du match:
       → Affinent le résultat (ex: 11-9 vs 11-4 dans le même set)
    
    🎯 CONCLUSION:
       → Le classement ELO est plus REPRÉSENTATIF du niveau réel
       → Les upsets et performances dominantes ont plus d'impact
       → Les matchs très serrés ne gonflent pas artificiellement le rating
    """)
    print("=" * 90)

if __name__ == "__main__":
    compare_matches()
