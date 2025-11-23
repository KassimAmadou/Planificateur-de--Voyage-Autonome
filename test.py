from core.tools import rechercher_vols

# Test avec 2 adultes + 1 enfant
print("=== TEST 1: Famille (2A + 1E) ===")
result = rechercher_vols(
    depart="Paris",
    arrivee="Bali",
    date_depart="du 15 au 30 décembre",
    adultes=2,
    enfants=1
)
print(result)
print("\n" + "="*80 + "\n")

# Test avec 1 adulte seul
print("=== TEST 2: Solo (1A) ===")
result2 = rechercher_vols(
    depart="Paris",
    arrivee="Bangkok",
    date_depart="du 10 au 20 mars",
    adultes=1,
    enfants=0
)
print(result2)