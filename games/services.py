import os
import requests
from .models import Game, Genre, Shop, Availability

# Carga la clave de RAWG de forma segura desde las variables de entorno (.env)
RAWG_API_KEY = os.getenv('RAWG_API_KEY')

def update_game_genres(game_obj):
    """
    Clasifica el juego consultando Steam o RAWG y guarda los resultados en la DB.
    Implementa el Paso 3 (Optimización) al no repetir consultas si ya existen géneros.
    """
    # Paso 3: Optimización - Si el juego ya tiene géneros asociados, no hacemos nada
    if game_obj.genres.exists():
        return

    # CASO 1: Intentar obtener géneros a través de la API de Steam si existe steam_appid
    if game_obj.steam_appid:
        steam_url = f"https://store.steampowered.com/api/appdetails?appids={game_obj.steam_appid}&l=spanish"
        try:
            res = requests.get(steam_url, timeout=5).json()
            if res.get(game_obj.steam_appid) and res[game_obj.steam_appid]['success']:
                data = res[game_obj.steam_appid]['data']
                genres_data = data.get('genres', [])
                for g in genres_data:
                    # Guardamos el género en nuestra base de datos para futuras consultas
                    genre_obj, _ = Genre.objects.get_or_create(name=g['description'])
                    game_obj.genres.add(genre_obj)
                return  # Si Steam tuvo éxito, terminamos aquí
        except Exception as e:
            print(f"Error en Steam API para {game_obj.title}: {e}")

    # CASO 2: Intentar con RAWG si no hay Steam ID o la consulta anterior falló
    if RAWG_API_KEY:
        # Limpiamos el título para mejorar la precisión de la búsqueda por texto
        clean_title = game_obj.title.split(' - ')[0].split(' (')[0]
        rawg_url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={clean_title}&page_size=1"
        try:
            res = requests.get(rawg_url, timeout=5).json()
            if res.get('results') and len(res['results']) > 0:
                best_match = res['results'][0]
                for g in best_match.get('genres', []):
                    genre_obj, _ = Genre.objects.get_or_create(name=g['name'])
                    game_obj.genres.add(genre_obj)
                print(f"Géneros de RAWG añadidos para: {game_obj.title}")
        except Exception as e:
            print(f"Error en RAWG API para {game_obj.title}: {e}")

def fetch_cheapshark_deals():
    """
    Descarga las últimas ofertas de CheapShark, sincroniza juegos, tiendas y disponibilidades.
    """
    url = "https://www.cheapshark.com/api/1.0/deals?upperPrice=15"
    try:
        deals = requests.get(url, timeout=10).json()
    except Exception as e:
        print(f"Error al conectar con CheapShark: {e}")
        return

    for item in deals:
        # 1. Crear o actualizar el registro del Juego
        game, created = Game.objects.update_or_create(
            api_ID=item['gameID'],
            defaults={
                'title': item['title'],
                'steam_appid': item.get('steamAppID'), # Almacenamos para el Caso 1
                'score': item['metacriticScore'] if item['metacriticScore'] != "0" else 0,
                'cover_url': item['thumb'],
            }
        )

        # 2. Llamar a la lógica de clasificación de géneros (Casos 1 y 2)
        update_game_genres(game)

        # 3. Asegurar que la Tienda existe en nuestra base de datos
        shop, _ = Shop.objects.get_or_create(
            api_ID=item['storeID'],
            defaults={
                'name': f"Tienda {item['storeID']}",
                'logo_url': f"https://www.cheapshark.com/img/stores/logos/{item['storeID']}.png"
            }
        )

        # 4. Actualizar la relación de disponibilidad (Precios y URL de oferta)
        Availability.objects.update_or_create(
            game=game,
            shop=shop,
            defaults={
                'current_price': item['salePrice'],
                'hist_min_price': item['normalPrice'],
                'offer_url': f"https://www.cheapshark.com/redirect?dealID={item['dealID']}"
            }
        )