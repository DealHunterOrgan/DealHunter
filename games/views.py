from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView, TemplateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.models import User

from .forms import CustomUserCreationForm
from .models import Game

# ... (Tus vistas GameListView, GameDetailView, CustomLoginView y SignUpView se mantienen igual) ...

class GameListView(ListView):
    model = Game
    template_name = 'games/home.html'
    context_object_name = 'games'

    def get_queryset(self):
        queryset = Game.objects.all().prefetch_related('platforms', 'availability_set').order_by('title')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(title__icontains=query)
        return queryset

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

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('games:home')

# --- NUEVAS VISTAS ---

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = ""
        return context

class DeleteAccountView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'registration/delete_confirm.html'
    success_url = reverse_lazy('games:home')

    def get_object(self, queryset=None):
        return self.request.user