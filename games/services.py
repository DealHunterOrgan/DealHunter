import os
import requests
from .models import Game, Genre, Shop, Availability, Platform

RAWG_API_KEY = os.getenv('RAWG_API_KEY')

STORE_PLATFORM_MAP = {
    '1': 'Steam',
    '2': 'GamersGate',
    '3': 'GreenManGaming',
    '7': 'GOG',
    '8': 'EA App (Origin)',
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
    store_id = str(store_id)
    if store_id == '1' or steam_appid:
        return 'Steam'
    return STORE_PLATFORM_MAP.get(store_id, 'Other')


def _rawg_url(path, **params):
    if not RAWG_API_KEY:
        return None
    query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
    suffix = f"&{query}" if query else ""
    return f"https://api.rawg.io/api/{path}?key={RAWG_API_KEY}{suffix}"


def get_rawg_id_by_title(title):
    """Busca en RAWG el ID interno usando el nombre limpio."""
    clean_title = title.split(' - ')[0].split(' (')[0]
    url = _rawg_url("games", search=clean_title, page_size=1)
    if not url:
        return None
    try:
        res = requests.get(url, timeout=5).json()
        if res.get('results'):
            return res['results'][0]['id']
    except Exception as e:
        print(f"Error RAWG ID: {e}")
    return None


def get_game_media(game_title):
    """Obtiene descripción, capturas y tráilers."""
    if not RAWG_API_KEY:
        return {'screenshots': [], 'trailer': None, 'description': "No description available."}

    rawg_id = get_rawg_id_by_title(game_title)
    media = {'screenshots': [], 'trailer': None, 'description': "No description available."}

    if not rawg_id:
        return media

    try:
        det_url = _rawg_url(f"games/{rawg_id}")
        res_det = requests.get(det_url, timeout=5).json()
        media['description'] = res_det.get('description_raw') or res_det.get('description')
    except:
        pass

    try:
        ss_url = _rawg_url(f"games/{rawg_id}/screenshots")
        res_ss = requests.get(ss_url, timeout=5).json()
        media['screenshots'] = [s['image'] for s in res_ss.get('results', [])[:4]]
    except:
        pass

    try:
        mov_url = _rawg_url(f"games/{rawg_id}/movies")
        res_mov = requests.get(mov_url, timeout=5).json()
        results = res_mov.get('results', [])
        if results:
            media['trailer'] = results[0].get('data', {}).get('max')
    except:
        pass

    return media


def update_game_genres(game_obj):
    if game_obj.genres.exists():
        return
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
                return
        except:
            pass


def fetch_cheapshark_deals():
    url = "https://www.cheapshark.com/api/1.0/deals?upperPrice=20&pageSize=60"
    try:
        deals = requests.get(url, timeout=10).json()
    except:
        return

    for item in deals:
        steam_appid = item.get('steamAppID') or None
        game, _ = Game.objects.update_or_create(
            api_ID=item['gameID'],
            defaults={
                'title': item['title'],
                'steam_appid': steam_appid,
                'score': int(item['metacriticScore']) if item.get('metacriticScore') and item[
                    'metacriticScore'] != "0" else 0,
                'cover_url': item['thumb'],
            }
        )
        p_name = get_platform_name(item['storeID'], steam_appid)
        p_obj, _ = Platform.objects.get_or_create(name=p_name)
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
