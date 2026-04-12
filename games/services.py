import os
import requests
from .models import Game, Genre, Shop, Availability, Platform

RAWG_API_KEY = '0c2a9ea573034836b3c0de9916085843'

# Mapa storeID → nombre de plataforma real
STORE_PLATFORM_MAP = {
    '1':  'Steam',
    '2':  'GamersGate',
    '3':  'GreenManGaming',
    '7':  'GOG',
    '8':  'EA App (Origin)',
    '11': 'Humble Store',
    '13': 'Fanatical',
    '15': 'Gamesplanet',
    '21': 'WinGameStore',
    '23': 'GameBillet',
    '25': 'Voidu',
    '27': 'Epic Games',
    '28': 'Razer Game Store',
    '31': 'IndieGala',
}


def get_platform_name(store_id, steam_appid=None):
    """Devuelve el nombre de plataforma según la tienda."""
    store_id = str(store_id)
    if store_id == '1' or steam_appid:
        return 'Steam'
    return STORE_PLATFORM_MAP.get(store_id, 'Other')


def update_game_genres(game_obj):
    if game_obj.genres.exists():
        return

    # 1. STEAM — usando steam_appid si existe
    if game_obj.steam_appid:
        steam_url = f"https://store.steampowered.com/api/appdetails?appids={game_obj.steam_appid}&l=english"
        try:
            res = requests.get(steam_url, timeout=5).json()
            app_data = res.get(str(game_obj.steam_appid)) or res.get(game_obj.steam_appid)
            if app_data and app_data.get('success') and app_data.get('data'):
                genres_data = app_data['data'].get('genres', [])
                for g in genres_data:
                    genre_obj, _ = Genre.objects.get_or_create(name=g['description'])
                    game_obj.genres.add(genre_obj)
                if genres_data:
                    print(f"✅ STEAM GENRES: {game_obj.title}")
                    return
        except Exception as e:
            print(f"⚠️ Steam error for {game_obj.title}: {e}")

    # 2. RAWG — fallback si Steam no devuelve géneros
    if RAWG_API_KEY:
        clean_title = game_obj.title.split(' - ')[0].split(' (')[0]
        rawg_url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={clean_title}&page_size=1"
        try:
            res = requests.get(rawg_url, timeout=5).json()
            if res.get('results'):
                best_match = res['results'][0]
                for g in best_match.get('genres', []):
                    genre_obj, _ = Genre.objects.get_or_create(name=g['name'])
                    game_obj.genres.add(genre_obj)
                print(f"🌐 RAWG GENRES: {game_obj.title}")
        except Exception as e:
            print(f"⚠️ RAWG error for {game_obj.title}: {e}")


def fetch_cheapshark_deals():
    url = "https://www.cheapshark.com/api/1.0/deals?upperPrice=20&pageSize=60"
    try:
        deals = requests.get(url, timeout=10).json()
    except Exception as e:
        print(f"❌ Error fetching deals: {e}")
        return

    for item in deals:
        steam_appid = item.get('steamAppID') or None

        game, _ = Game.objects.update_or_create(
            api_ID=item['gameID'],
            defaults={
                'title': item['title'],
                'steam_appid': steam_appid,
                'score': int(item['metacriticScore']) if item.get('metacriticScore') and item['metacriticScore'] != "0" else 0,
                'cover_url': item['thumb'],
            }
        )

        # Plataforma basada en la tienda real
        platform_name = get_platform_name(item['storeID'], steam_appid)
        p_obj, _ = Platform.objects.get_or_create(name=platform_name)
        game.platforms.add(p_obj)

        update_game_genres(game)

        shop, _ = Shop.objects.get_or_create(
            api_ID=item['storeID'],
            defaults={
                'name': STORE_PLATFORM_MAP.get(str(item['storeID']), f"Store {item['storeID']}"),
                'logo_url': f"https://www.cheapshark.com/img/stores/logos/{item['storeID']}.png"
            }
        )

        Availability.objects.update_or_create(
            game=game, shop=shop,
            defaults={
                'current_price': item['salePrice'],
                'hist_min_price': item['normalPrice'],
                'offer_url': f"https://www.cheapshark.com/redirect?dealID={item['dealID']}"
            }
        )