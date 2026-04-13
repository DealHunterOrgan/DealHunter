from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, TemplateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.db.models import Count
from django.views import View

from .forms import CustomUserCreationForm
from .models import Game, Wishlist, Genre, Platform
from .models import Game, Wishlist, Genre, Platform, Review


class GameListView(ListView):
    model = Game
    template_name = 'games/home.html'
    context_object_name = 'games'
    paginate_by = 30

    def get_queryset(self):
        qs = Game.objects.all().prefetch_related('platforms', 'availability_set', 'genres')
        q = self.request.GET.get('q', '').strip()

        # Multi-select: getlist devuelve lista de valores
        genres = self.request.GET.getlist('genre')
        platforms = self.request.GET.getlist('platform')
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')

        if q:
            qs = qs.filter(title__icontains=q)

        # Filtrar por múltiples géneros (OR entre ellos)
        if genres:
            qs = qs.filter(genres__name__in=genres)

        # Filtrar por múltiples plataformas (OR entre ellas)
        # Normalizar "Steam" para incluir tanto "Steam" como "Store 1"
        if platforms:
            normalized = []
            for p in platforms:
                normalized.append(p)
                if p == 'Steam':
                    normalized.append('Store 1')  # datos viejos
            qs = qs.filter(platforms__name__in=normalized)

        if price_min:
            try:
                qs = qs.filter(availability__current_price__gte=float(price_min))
            except ValueError:
                pass
        if price_max:
            try:
                qs = qs.filter(availability__current_price__lte=float(price_max))
            except ValueError:
                pass

        return qs.distinct().order_by('title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['selected_genres'] = self.request.GET.getlist('genre')
        context['selected_platforms'] = self.request.GET.getlist('platform')
        context['price_min'] = self.request.GET.get('price_min', '')
        context['price_max'] = self.request.GET.get('price_max', '')

        # Géneros con conteo, solo los que tienen juegos
        context['all_genres'] = (
            Genre.objects
            .annotate(game_count=Count('games', distinct=True))
            .filter(game_count__gt=0)
            .order_by('name')
        )

        context['all_platforms'] = (
            Platform.objects
            .annotate(game_count=Count('games', distinct=True))
            .filter(game_count__gt=0)
            .exclude(name__startswith='Store ')
            .exclude(name='PC Digital')
            .order_by('name')
        )

        return context


class GameDetailView(DetailView):
    model = Game
    template_name = 'games/detail.html'
    context_object_name = 'game'

    def get_queryset(self):
        return Game.objects.all().prefetch_related('platforms', 'genres', 'availability_set__shop')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_wishlisted'] = Wishlist.objects.filter(
                user=self.request.user, game=self.object
            ).exists()
        else:
            context['is_wishlisted'] = False
        return context


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('games:home')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/profile.html'


class DeleteAccountView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'registration/delete_confirm.html'
    success_url = reverse_lazy('games:home')

    def get_object(self, queryset=None):
        return self.request.user


class ToggleWishlistView(LoginRequiredMixin, View):
    def post(self, request, pk):
        game = get_object_or_404(Game, pk=pk)
        wishlist_item = Wishlist.objects.filter(user=request.user, game=game).first()
        if wishlist_item:
            wishlist_item.delete()
        else:
            Wishlist.objects.create(user=request.user, game=game, desired_price=0.00)
        return redirect(request.META.get('HTTP_REFERER', 'games:home'))


class AddReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        game = get_object_or_404(Game, pk=pk)
        content = request.POST.get('content', '').strip()

        if content:
            Review.objects.create(
                game=game,
                user=request.user,
                content=content
            )
        return redirect('games:detail', pk=pk)