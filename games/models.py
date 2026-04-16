from django.db import models
from django.contrib.auth.models import User

class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class Platform(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name

class Game(models.Model):
    title = models.CharField(max_length=100)
    api_ID = models.CharField(max_length=50, unique=True)
    steam_appid = models.CharField(max_length=20, null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    launch_date = models.DateField(null=True, blank=True)
    cover_url = models.URLField()

    genres = models.ManyToManyField(Genre, related_name="games")
    platforms = models.ManyToManyField(Platform, related_name="games")

    def __str__(self):
        return self.title

    def get_best_price(self):
        best = self.availability_set.order_by('current_price').first()
        return best.current_price if best else None

    def get_best_discount(self):
        best = self.availability_set.order_by('current_price').first()
        if best and best.hist_min_price and best.hist_min_price > 0:
            return int((1 - (best.current_price / best.hist_min_price)) * 100)
        return 0

class Shop(models.Model):
    name = models.CharField(max_length=50)
    api_ID = models.CharField(max_length=50, unique=True)
    service_state = models.BooleanField(default=True)
    logo_url = models.URLField()

    def __str__(self):
        return self.name

class Availability(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    current_price = models.DecimalField(max_digits=8, decimal_places=2)
    hist_min_price = models.DecimalField(max_digits=8, decimal_places=2)
    offer_url = models.URLField()

    class Meta:
        unique_together = ('game', 'shop')

    def __str__(self):
        return f"{self.game.title} en {self.shop.name}"

class Wishlist(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    desired_price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ('game', 'user')

    def __str__(self):
        return f"{self.user.username} wants {self.game.title}"

class Review(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=1000)
    rating = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.username} on {self.game.title}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar_url = models.CharField(max_length=255, default='avatar1.png')

    def __str__(self):
        return self.user.username
