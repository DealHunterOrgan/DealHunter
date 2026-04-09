from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Game

# Create your views here.

'''def home(request):  # Home page of the web
    games = Game.objects.all()

    return render(request, 'games/home.html', {'games': games})'''

class GameListView(ListView):
    model = Game
    template_name = 'games/home.html'
    context_object_name = 'games'

class GameDetailView(DetailView):
    model = Game
    template_name = 'games/detail.html'
    context_object_name = 'game'
