from django.db import models
from django.contrib.auth.models import User
from django.db.models import ManyToManyField

# Create your models here.

class Game(models.Model):
    title = models.CharField(max_length=100)
    api_ID = models.CharField(max_length=50, unique=True)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    launch_date = models.DateField()
    cover_url = models.URLField()

    genres = ManyToManyField('Genre', related_name="games")
    platforms = ManyToManyField('Platform', related_name="games")

    def __str__(self):
        return self.title


class Genre(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Platform(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


# User already imported


class Shop (models.Model):
    name = models.CharField(max_length=50)
    api_ID = models.CharField(max_length=50, unique=True)
    service_state = models.BooleanField(default=True)
    logo_url = models.URLField()

    def __str__(self):
        return self.name


class Availability(models.Model):   # Game - Shop relationship
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    current_price = models.DecimalField(max_digits=8, decimal_places=2)
    hist_min_price = models.DecimalField(max_digits=8, decimal_places=2)
    offer_url = models.URLField()

    class Meta:
        unique_together = ('game', 'shop')

    def __str__(self):
        return f"{self.game.title} costs {self.shop.name}: {self.current_price}€"


class Wishlist(models.Model):  # Game - User relationship
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    desired_price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ('game', 'user')

    def __str__(self):
        return f"{self.user.username} wants {self.game.title}"


###############################################################################################
