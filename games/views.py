from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView, CreateView, TemplateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.db.models import Count, Min, F
from django.views import View
from django.utils import timezone

from .forms import CustomUserCreationForm, EditProfileForm
from .models import Game, Wishlist, Genre, Platform, Review, Profile
from .services import get_game_media  # Importamos la función de RAWG


# ========================
# 1. LISTADO PRINCIPAL (HOME)
# ========================
class GameListView(ListView):
    model = Game
    template_name = 'games/home.html'
    context_object_name = 'games'
    paginate_by = 30

    def get_queryset(self):
        qs = Game.objects.all().prefetch_related('platforms', 'availability_set', 'genres')

        q = self.request.GET.get('q', '').strip()
        genres = self.request.GET.getlist('genre')
        platforms = self.request.GET.getlist('platform')
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        sort = self.request.GET.get('sort')

        if q: qs = qs.filter(title__icontains=q)
        if genres: qs = qs.filter(genres__name__in=genres).distinct()
        if platforms: qs = qs.filter(platforms__name__in=platforms).distinct()

        if price_min:
            qs = qs.annotate(min_price=Min('availability__current_price')).filter(min_price__gte=price_min)
        if price_max:
            qs = qs.annotate(min_price=Min('availability__current_price')).filter(min_price__lte=price_max)

        if sort == 'price_asc':
            qs = qs.annotate(min_price=Min('availability__current_price')).order_by('min_price')
        elif sort == 'price_desc':
            qs = qs.annotate(min_price=Min('availability__current_price')).order_by('-min_price')
        elif sort == 'score':
            qs = qs.order_by('-score')
        elif sort == 'newest':
            qs = qs.order_by('-launch_date')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_genres'] = Genre.objects.all()
        context['all_platforms'] = Platform.objects.all()
        context['selected_genres'] = self.request.GET.getlist('genre')
        context['selected_platforms'] = self.request.GET.getlist('platform')
        context['search_query'] = self.request.GET.get('q', '')
        context['price_min'] = self.request.GET.get('price_min', '')
        context['price_max'] = self.request.GET.get('price_max', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        return context


# ========================
# 2. DETALLE DEL JUEGO (AQUÍ VA EXACTAMENTE)
# ========================
class GameDetailView(DetailView):
    model = Game
    template_name = 'games/detail.html'
    context_object_name = 'game'

    def get_queryset(self):
        # Optimizamos la consulta para traer tiendas y géneros de un golpe
        return Game.objects.all().prefetch_related('platforms', 'genres', 'availability_set__shop')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game = self.get_object()

        # Multimedia desde RAWG (Servicio)
        context['media'] = get_game_media(game.title)

        # Estado de Wishlist para el usuario actual
        if self.request.user.is_authenticated:
            context['is_wishlisted'] = Wishlist.objects.filter(
                user=self.request.user, game=game
            ).exists()
        else:
            context['is_wishlisted'] = False

        # Listado de reseñas del juego
        context['reviews'] = Review.objects.filter(game=game).select_related('user').order_by('-created_at')

        # Ofertas disponibles
        context['availabilities'] = game.availability_set.all().select_related('shop').order_by('current_price')

        return context


# ========================
# 3. CUENTAS Y PERFIL
# ========================
class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        Profile.objects.get_or_create(user=self.object)
        return response


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['wishlist_items'] = Wishlist.objects.filter(user=user).select_related('game')
        user_reviews = Review.objects.filter(user=user).select_related('game').order_by('-created_at')
        context['latest_reviews'] = user_reviews[:3]

        context['wish_count'] = context['wishlist_items'].count()
        context['review_count'] = user_reviews.count()

        profile, created = Profile.objects.get_or_create(user=user)
        context['profile'] = profile
        return context


class EditAccountView(LoginRequiredMixin, View):
    def get(self, request):
        form = EditProfileForm(instance=request.user)
        return render(request, 'registration/edit_account.html', {'form': form})

    def post(self, request):
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('games:profile')
        return render(request, 'registration/edit_account.html', {'form': form})


class DeleteAccountView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'games/delete_account_confirm.html'
    success_url = reverse_lazy('games:home')

    def get_object(self, queryset=None):
        return self.request.user


# ========================
# 4. ACCIONES (WISHLIST Y REVIEWS)
# ========================
class ToggleWishlistView(LoginRequiredMixin, View):
    def post(self, request, pk):
        game = get_object_or_404(Game, pk=pk)
        wish = Wishlist.objects.filter(user=request.user, game=game).first()
        if wish:
            wish.delete()
        else:
            Wishlist.objects.create(user=request.user, game=game, desired_price=0)

        referer = request.META.get('HTTP_REFERER', 'games:home')
        return redirect(referer)


class AddReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        game = get_object_or_404(Game, pk=pk)
        content = request.POST.get('content', '').strip()
        if content:
            Review.objects.create(
                game=game, user=request.user, content=content,
                rating=int(request.POST.get('rating', 5))
            )
        return redirect('games:detail', pk=pk)


class EditReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk, user=request.user)
        review.content = request.POST.get('content', review.content).strip()
        review.rating = request.POST.get('rating', review.rating)
        review.save()

        referer = request.META.get('HTTP_REFERER', '')
        if 'profile' in referer:
            return redirect('games:profile')
        return redirect('games:detail', pk=review.game.id)


class DeleteReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk, user=request.user)
        game_id = review.game.id
        review.delete()

        referer = request.META.get('HTTP_REFERER', '')
        if 'profile' in referer:
            return redirect('games:profile')
        return redirect('games:detail', pk=game_id)
