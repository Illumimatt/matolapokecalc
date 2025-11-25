from src.api import get_pokemon_data
from src.calculations import calculate_stat

poke = get_pokemon_data("pikachu")

if poke:
    print(f"Nome: {poke['name']}")
    print(f"Base Speed: {poke['stats']['spe']}") # Deve ser 90
    
    speed_calc = calculate_stat(
        base=poke['stats']['spe'], 
        iv=31, 
        ev=252, 
        level=50, 
        nature_mod=1.0, 
        is_hp=False
    )
    print(f"Speed: {speed_calc}") #Deve ser 142
else:
    print("erro")