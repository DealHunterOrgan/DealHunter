import os
import requests
from .models import Game, Genre, Shop, Availability, Platform

RAWG_API_KEY = os.getenv('RAWG_API_KEY')


def update_game_genres(game_obj):
    if game_obj.genres.exists():
        return

    # 1. STEAM
    if game_obj.steam_appid:
        steam_url = f"https://store.steampowered.com/api/appdetails?appids={game_obj.steam_appid}&l=spanish"
        try:
            res = requests.get(steam_url, timeout=5).json()
            if res.get(game_obj.steam_appid) and res[game_obj.steam_appid]['success']:
                genres_data = res[game_obj.steam_appid]['data'].get('genres', [])
                for g in genres_data:
                    genre_obj, _ = Genre.objects.get_or_create(name=g['description'])
                    game_obj.genres.add(genre_obj)
                print(f"✅ STEAM GENRES: {game_obj.title}")
                return
        except Exception:
            pass

    # 2. RAWG
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
        except Exception:
            pass


def fetch_cheapshark_deals():
    url = "https://www.cheapshark.com/api/1.0/deals?upperPrice=20"
    try:
        deals = requests.get(url, timeout=10).json()
    except:
        return

    for item in deals:
        game, _ = Game.objects.update_or_create(
            api_ID=item['gameID'],
            defaults={
                'title': item['title'],
                'steam_appid': item.get('steamAppID'),
                'score': int(item['metacriticScore']) if item['metacriticScore'] != "0" else 0,
                'cover_url': item['thumb'],
            }
        )

        # ASIGNACIÓN DE PLATAFORMAS
        if item.get('steamAppID'):
            p_obj, _ = Platform.objects.get_or_create(name="Steam")
            game.platforms.add(p_obj)
        else:
            p_obj, _ = Platform.objects.get_or_create(name="PC Digital")
            game.platforms.add(p_obj)

        update_game_genres(game)

        shop, _ = Shop.objects.get_or_create(
            api_ID=item['storeID'],
            defaults={'name': f"Tienda {item['storeID']}",
                      'logo_url': f"https://www.cheapshark.com/img/stores/logos/{item['storeID']}.png"}
        )

        Availability.objects.update_or_create(
            game=game, shop=shop,
            defaults={'current_price': item['salePrice'], 'hist_min_price': item['normalPrice'],
                      'offer_url': f"https://www.cheapshark.com/redirect?dealID={item['dealID']}"}
        )