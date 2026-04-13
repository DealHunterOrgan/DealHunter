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


# ========================
# LISTADO PRINCIPAL
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

        if q:
            qs = qs.filter(title__icontains=q)
        if genres:
            qs = qs.filter(genres__name__in=genres)
        if platforms:
            normalized = []
            for p in platforms:
                normalized.append(p)
                if p == 'Steam':
                    normalized.append('Store 1')
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

        qs = qs.distinct()

        if sort == 'score':
            qs = qs.order_by(F('score').desc(nulls_last=True))
        elif sort == 'price_asc':
            qs = qs.annotate(min_price=Min('availability__current_price')).order_by('min_price')
        elif sort == 'price_desc':
            qs = qs.annotate(min_price=Min('availability__current_price')).order_by('-min_price')
        elif sort == 'newest':
            qs = qs.order_by(F('launch_date').desc(nulls_last=True))
        else:
            qs = qs.order_by('title')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['selected_genres'] = self.request.GET.getlist('genre')
        context['selected_platforms'] = self.request.GET.getlist('platform')
        context['price_min'] = self.request.GET.get('price_min', '')
        context['price_max'] = self.request.GET.get('price_max', '')
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


# ========================
# DETALLE DE JUEGO
# ========================
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
        context['reviews'] = Review.objects.filter(game=self.object).select_related('user').order_by('-created_at')
        return context


# ========================
# PERFIL
# ========================
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        sort = self.request.GET.get('sort', 'newest')

        wishlist_qs = Wishlist.objects.filter(user=user).select_related('game').prefetch_related(
            'game__availability_set')

        if sort == 'price_low':
            wishlist_qs = wishlist_qs.order_by('game__availability__current_price').distinct()
        elif sort == 'metacritic':
            wishlist_qs = wishlist_qs.order_by(F('game__score').desc(nulls_last=True))

        wishlist_items = list(wishlist_qs)

        context['wishlist_items'] = wishlist_items
        context['banner_games'] = [item.game for item in wishlist_items[:6]]

        profile, _ = Profile.objects.get_or_create(user=user)
        context['profile'] = profile

        reviews_qs = Review.objects.filter(user=user).select_related('game').order_by('-created_at')
        context['review_count'] = reviews_qs.count()
        context['latest_reviews'] = reviews_qs[:3]

        total_savings = 0
        for item in wishlist_items:
            best_offer = item.game.availability_set.aggregate(Min('current_price'))['current_price__min']
            base_price = getattr(item.game, 'base_price', getattr(item.game, 'price', None))
            if best_offer and base_price and base_price > best_offer:
                total_savings += (base_price - best_offer)

        context['total_savings'] = total_savings
        delta = timezone.now() - user.date_joined
        context['hunter_level'] = (context['review_count'] * 2) + (delta.days // 30) + 1
        return context


# ========================
# GESTIÓN DE CUENTAS
# ========================
class EditAccountView(LoginRequiredMixin, View):
    template_name = 'registration/edit_account.html'

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        form = EditProfileForm(instance=request.user, initial={'avatar': profile.avatar_url})
        return render(request, self.template_name, {'form': form, 'current_avatar': profile.avatar_url})

    def post(self, request):
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data.get('password'):
                user.set_password(form.cleaned_data['password'])
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.avatar_url = form.cleaned_data.get('avatar')
            profile.save()
            update_session_auth_hash(request, user)
            return redirect('games:profile')
        return render(request, self.template_name, {'form': form})


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('games:home')


class DeleteAccountView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'registration/delete_confirm.html'
    success_url = reverse_lazy('games:home')

    def get_object(self, queryset=None):
        return self.request.user


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'


# ========================
# WISHLIST
# ========================
class ToggleWishlistView(LoginRequiredMixin, View):
    def post(self, request, pk):
        game = get_object_or_404(Game, pk=pk)
        wish = Wishlist.objects.filter(user=request.user, game=game).first()
        if wish:
            wish.delete()
        else:
            Wishlist.objects.create(user=request.user, game=game, desired_price=0)
        return redirect(request.META.get('HTTP_REFERER', 'games:home'))


# ========================
# REVIEWS
# ========================
class AddReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        game = get_object_or_404(Game, pk=pk)
        content = request.POST.get('content', '').strip()
        if content:
            Review.objects.create(
                game=game,
                user=request.user,
                content=content,
                rating=int(request.POST.get('rating', 5))
            )
        return redirect('games:detail', pk=pk)


class EditReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk, user=request.user)
        review.content = request.POST.get('content', review.content).strip()
        review.rating = request.POST.get('rating', review.rating)
        review.save()
        return redirect('games:detail', pk=review.game.id)


class DeleteReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk, user=request.user)
        game_id = review.game.id
        review.delete()
        return redirect('games:detail', pk=game_id)