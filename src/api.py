import requests
from io import BytesIO
from PIL import Image
from typing import Optional, Dict, Any

BASE_URL = "https://pokeapi.co/api/v2/pokemon/"

def get_pokemon_data(pokemon_name: str) -> Optional[Dict[str, Any]]:
    clean_name = pokemon_name.strip().lower()
    try:
        response = requests.get(f"{BASE_URL}{clean_name}")
        response.raise_for_status()
        data = response.json()
        
        stats = {}
        for item in data['stats']:
            stat_name = item['stat']['name']
            base_value = item['base_stat']
            name_map = {
                'hp': 'hp', 'attack': 'atk', 'defense': 'def',
                'special-attack': 'spa', 'special-defense': 'spd', 'speed': 'spe'
            }
            stats[name_map.get(stat_name, stat_name)] = base_value

        img_url = data['sprites']['front_default']
        
        if not img_url:
             img_url = data['sprites']['other']['official-artwork']['front_default']
             
        image = _download_image(img_url)

        return {
            "id": data['id'],
            "name": data['name'].capitalize(),
            "stats": stats,
            "image": image,
            "types": [t['type']['name'] for t in data['types']]
        }
    except requests.exceptions.RequestException:
        print(f"Erro de conexão ao buscar {clean_name}")
        return None
    except Exception as e:
        print(f"Erro ao processar dados de {clean_name}: {e}")
        return None

def _download_image(url: str) -> Optional[Image.Image]:
    if not url: return None
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        img_data = BytesIO(response.content)
        return Image.open(img_data)
    except Exception as e:
        print(f"Erro ao baixar imagem: {e}")
        return None

def get_all_names_list() -> list:
    url = "https://pokeapi.co/api/v2/pokemon?limit=10000"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [p['name'] for p in data['results']]
        return []
    except Exception as e:
        print(f"Erro ao baixar lista de nomes: {e}")
        return []