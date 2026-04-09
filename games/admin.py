from django.contrib import admin
from .models import Game, Genre, Platform, Shop, Availability, Wishlist

# Register your models here.

admin.site.register(Game)
admin.site.register(Genre)
admin.site.register(Platform)
admin.site.register(Shop)
admin.site.register(Availability)
admin.site.register(Wishlist)
