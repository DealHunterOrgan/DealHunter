import requests
from .models import Game, Genre, Shop, Availability

# Consigue una gratis en https://rawg.io/apidocs
RAWG_API_KEY = "TU_API_KEY_AQUI"


def update_game_genres(game_obj):
    if game_obj.genres.exists():
        return

    # Caso 1: Steam
    if game_obj.steam_appid:
        steam_url = f"https://store.steampowered.com/api/appdetails?appids={game_obj.steam_appid}&l=spanish"
        try:
            res = requests.get(steam_url).json()
            if res.get(game_obj.steam_appid) and res[game_obj.steam_appid]['success']:
                data = res[game_obj.steam_appid]['data']
                for g in data.get('genres', []):
                    genre_obj, _ = Genre.objects.get_or_create(name=g['description'])
                    game_obj.genres.add(genre_obj)
                return
        except:
            pass

    # Caso 2: RAWG
    rawg_url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={game_obj.title}&page_size=1"
    try:
        res = requests.get(rawg_url).json()
        if res.get('results'):
            for g in res['results'][0].get('genres', []):
                genre_obj, _ = Genre.objects.get_or_create(name=g['name'])
                game_obj.genres.add(genre_obj)
    except:
        pass


def fetch_cheapshark_deals():
    url = "https://www.cheapshark.com/api/1.0/deals?upperPrice=15"
    deals = requests.get(url).json()

    for item in deals:
        game, _ = Game.objects.update_or_create(
            api_ID=item['gameID'],
            defaults={
                'title': item['title'],
                'steam_appid': item.get('steamAppID'),
                'score': item['metacriticScore'] if item['metacriticScore'] != "0" else 0,
                'cover_url': item['thumb'],
            }
        )
        update_game_genres(game)

        shop, _ = Shop.objects.get_or_create(
            api_ID=item['storeID'],
            defaults={'name': f"Tienda {item['storeID']}", 'logo_url': ''}
        )

        Availability.objects.update_or_create(
            game=game,
            shop=shop,
            defaults={
                'current_price': item['salePrice'],
                'hist_min_price': item['normalPrice'],
                'offer_url': f"https://www.cheapshark.com/redirect?dealID={item['dealID']}"
            }
        )