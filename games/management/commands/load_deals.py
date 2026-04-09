# Script to load all the data we need from the API

import requests
from datetime import datetime
from django.core.management.base import BaseCommand

from games.models import Game, Shop, Availability

class Command(BaseCommand):
    help = 'Loads the games and offers data from CheapSharkAPI'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Initializing data load from CheapSharkAPI..."))

        # Load shops
        shops_url = 'https://www.cheapshark.com/api/1.0/stores'
        shop_json = requests.get(shops_url).json()

        for shop in shop_json:  # StoreID, storeName, isActive... Are the params as the API serves them
            logo = f"https://www.cheapshark.com{shop['images']['logo']}"
            Shop.objects.update_or_create(api_ID=shop['storeID'], defaults={'name': shop['storeName'], 'service_state': shop['isActive'], 'logo_url': logo})

        # Load offers (Game + Availability)

        PAGES_TO_DOWNLOAD = 8   # Adjustable depending on how much data do we want

        for page in range(PAGES_TO_DOWNLOAD):

            offers_url = f'https://www.cheapshark.com/api/1.0/deals?pageNumber={page}'
            offers_json = requests.get(offers_url).json()

            for offer in offers_json:
                if offer['releaseDate'] > 0:
                    correct_date = datetime.fromtimestamp(offer['releaseDate'])
                else:
                    correct_date = datetime(2000,1,1) # If the game doesn't have a specified date

                score_val = offer.get('metacriticScore', 0)
                if score_val is None or score_val == "0":
                    score_val = 0   # Default value for non-existent scores

                game_obj, _ = Game.objects.update_or_create(api_ID=offer['gameID'], defaults={'title': offer['title'], 'score': float(score_val), 'launch_date': correct_date, 'cover_url': offer['thumb']})

                try:
                    shop_obj = Shop.objects.get(api_ID=offer['storeID'])
                    offer_link = f"https://www.cheapshark.com/redirect?dealID={offer['dealID']}"
                    Availability.objects.update_or_create(game=game_obj, shop=shop_obj, defaults={'current_price': offer['salePrice'], 'hist_min_price': offer['salePrice'], 'offer_url': offer_link})
                except Shop.DoesNotExist:   # Safety check
                    continue

        self.stdout.write(self.style.SUCCESS("Data loaded successfully"))