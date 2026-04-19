from django.core.management.base import BaseCommand
from games.services import fetch_cheapshark_deals

class Command(BaseCommand):
    help = 'Actualiza ofertas desde CheapShark y clasifica géneros'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando actualización...")
        fetch_cheapshark_deals()
        self.stdout.write(self.style.SUCCESS("Base de datos actualizada con géneros"))