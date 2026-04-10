from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView

from .forms import CustomUserCreationForm
from .models import Game

class GameListView(ListView):
    model = Game
    template_name = 'games/home.html'
    context_object_name = 'games'

    def get_queryset(self):
        queryset = (
            Game.objects.all()
            .prefetch_related('platforms', 'availability_set')
            .order_by('title')
        )
        query = self.request.GET.get('q', '').strip()

        if query:
            queryset = queryset.filter(title__icontains=query)

        return queryset

    def get_paginate_by(self, queryset):
        query = self.request.GET.get('q', '').strip()
        return 12 if query else None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        return context

class GameDetailView(DetailView):
    model = Game
    template_name = 'games/detail.html'
    context_object_name = 'game'


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = ""
        return context


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('games:home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = ""
        return context
