import requests
from datetime import datetime
from django.core.management.base import BaseCommand

from games.models import Game, Shop, Availability, Platform
from games.services import get_platform_name, update_game_genres

class Command(BaseCommand):
    help = 'Loads games and deals from CheapShark API'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Initializing data load from CheapShark API..."))

        # 1. Cargar tiendas
        shops_url = 'https://www.cheapshark.com/api/1.0/stores'
        shop_json = requests.get(shops_url).json()

        for shop in shop_json:
            logo = f"https://www.cheapshark.com{shop['images']['logo']}"
            Shop.objects.update_or_create(
                api_ID=shop['storeID'],
                defaults={
                    'name': shop['storeName'],
                    'service_state': shop['isActive'],
                    'logo_url': logo
                }
            )
        self.stdout.write(f"  ✅ {len(shop_json)} shops loaded")

        # 2. Cargar ofertas
        PAGES_TO_DOWNLOAD = 8

        total_games = 0
        for page in range(PAGES_TO_DOWNLOAD):
            offers_url = f'https://www.cheapshark.com/api/1.0/deals?pageNumber={page}'
            offers_json = requests.get(offers_url).json()

            for offer in offers_json:
                # Fecha de lanzamiento
                if offer.get('releaseDate') and offer['releaseDate'] > 0:
                    correct_date = datetime.fromtimestamp(offer['releaseDate'])
                else:
                    correct_date = datetime(2000, 1, 1)

                score_val = offer.get('metacriticScore', 0)
                if not score_val or score_val == "0":
                    score_val = 0

                steam_appid = offer.get('steamAppID') or None

                game_obj, _ = Game.objects.update_or_create(
                    api_ID=offer['gameID'],
                    defaults={
                        'title': offer['title'],
                        'score': float(score_val),
                        'launch_date': correct_date,
                        'cover_url': offer['thumb'],
                        'steam_appid': steam_appid,
                    }
                )

                # Asignar plataforma correcta según tienda
                platform_name = get_platform_name(offer['storeID'], steam_appid)
                p_obj, _ = Platform.objects.get_or_create(name=platform_name)
                game_obj.platforms.add(p_obj)

                # Géneros
                update_game_genres(game_obj)

                try:
                    shop_obj = Shop.objects.get(api_ID=offer['storeID'])
                    offer_link = f"https://www.cheapshark.com/redirect?dealID={offer['dealID']}"
                    Availability.objects.update_or_create(
                        game=game_obj, shop=shop_obj,
                        defaults={
                            'current_price': offer['salePrice'],
                            'hist_min_price': offer['salePrice'],
                            'offer_url': offer_link
                        }
                    )
                except Shop.DoesNotExist:
                    continue

                total_games += 1

            self.stdout.write(f"  Page {page + 1}/{PAGES_TO_DOWNLOAD} done")

        self.stdout.write(self.style.SUCCESS(f"✅ {total_games} games loaded successfully"))