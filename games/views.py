from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, DetailView, CreateView, TemplateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.db.models import Count, Min, F
from django.views import View
from django.http import JsonResponse

from .forms import CustomUserCreationForm, EditProfileForm
from .models import Game, Wishlist, Genre, Platform, Review, Profile
from .services import get_game_media

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

        needs_price = price_min or price_max or sort in ('price_asc', 'price_desc')
        if needs_price:
            qs = qs.annotate(min_price=Min('availability__current_price'))
        if price_min:
            qs = qs.filter(min_price__gte=price_min)
        if price_max:
            qs = qs.filter(min_price__lte=price_max)
        if sort == 'price_asc':
            qs = qs.order_by('min_price')
        elif sort == 'price_desc':
            qs = qs.order_by('-min_price')
        elif sort == 'score':
            qs = qs.order_by('-score')
        elif sort == 'newest':
            qs = qs.order_by('-launch_date')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_genres'] = Genre.objects.annotate(game_count=Count('games')).order_by('name')
        context['all_platforms'] = Platform.objects.annotate(game_count=Count('games')).order_by('name')
        context['selected_genres'] = self.request.GET.getlist('genre')
        context['selected_platforms'] = self.request.GET.getlist('platform')
        context['search_query'] = self.request.GET.get('q', '')
        context['price_min'] = self.request.GET.get('price_min', '')
        context['price_max'] = self.request.GET.get('price_max', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        context['total_count'] = context['page_obj'].paginator.count
        context['sort_options'] = [
            ('price_asc', 'Price: Low to High'),
            ('price_desc', 'Price: High to Low'),
            ('score', 'Best Rated'),
            ('newest', 'Newest'),
        ]
        return context

class GameDetailView(DetailView):
    model = Game
    template_name = 'games/detail.html'
    context_object_name = 'game'

    def get_queryset(self):
        return Game.objects.all().prefetch_related('platforms', 'genres', 'availability_set__shop')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        game = self.object
        context['media'] = get_game_media(game.title)

        if self.request.user.is_authenticated:
            context['is_wishlisted'] = Wishlist.objects.filter(
                user=self.request.user, game=game
            ).exists()
        else:
            context['is_wishlisted'] = False

        context['reviews'] = Review.objects.filter(game=game).select_related('user').order_by('-created_at')
        context['availabilities'] = game.availability_set.all().select_related('shop').order_by('current_price')

        return context

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('games:home')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        Profile.objects.get_or_create(user=self.object)
        login(self.request, self.object)
        return redirect('games:home')

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

        total_savings = 0
        for item in context['wishlist_items']:
            best = item.game.availability_set.order_by('current_price').first()
            if best and best.hist_min_price and best.current_price:
                saving = float(best.hist_min_price) - float(best.current_price)
                if saving > 0:
                    total_savings += saving
        context['total_savings'] = total_savings

        activity = context['wish_count'] + context['review_count']
        if activity >= 20:
            hunter_level = 5
        elif activity >= 10:
            hunter_level = 4
        elif activity >= 5:
            hunter_level = 3
        elif activity >= 2:
            hunter_level = 2
        else:
            hunter_level = 1
        context['hunter_level'] = hunter_level

        return context

class EditAccountView(LoginRequiredMixin, View):
    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        form = EditProfileForm(
            instance=request.user,
            initial={'avatar': profile.avatar_url}
        )
        return render(request, 'registration/edit_account.html', {'form': form})

    def post(self, request):
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)

            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.save()
            update_session_auth_hash(request, user)

            profile, _ = Profile.objects.get_or_create(user=user)
            avatar = form.cleaned_data.get('avatar')
            if avatar:
                profile.avatar_url = avatar
                profile.save()

            return redirect('games:profile')
        return render(request, 'registration/edit_account.html', {'form': form})

class DeleteAccountView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'games/delete_account_confirm.html'
    success_url = reverse_lazy('games:home')

    def get_object(self, queryset=None):
        return self.request.user

class ToggleWishlistView(LoginRequiredMixin, View):
    def post(self, request, pk):
        game = get_object_or_404(Game, pk=pk)
        wish = Wishlist.objects.filter(user=request.user, game=game).first()
        if wish:
            wish.delete()
        else:
            Wishlist.objects.create(user=request.user, game=game, desired_price=0)

        next_url = request.GET.get('next')
        if next_url == 'profile':
            return redirect('games:profile')
        return redirect('games:detail', pk=pk)

class AddReviewView(LoginRequiredMixin, CreateView):
    model = Review
    fields = ['content', 'rating']

    def form_valid(self, form):
        form.instance.game = get_object_or_404(Game, pk=self.kwargs['pk'])
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('games:detail', kwargs={'pk': self.kwargs['pk']})

class EditReviewView(LoginRequiredMixin, UpdateView):
    model = Review
    fields = ['content', 'rating']

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

    def get_success_url(self):
        referer = self.request.META.get('HTTP_REFERER', '')
        if 'profile' in referer:
            return reverse_lazy('games:profile')
        return reverse_lazy('games:detail', kwargs={'pk': self.object.game.id})

class DeleteReviewView(LoginRequiredMixin, DeleteView):
    model = Review

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

    def get_success_url(self):
        referer = self.request.META.get('HTTP_REFERER', '')
        if 'profile' in referer:
            return reverse_lazy('games:profile')
        return reverse_lazy('games:detail', kwargs={'pk': self.object.game.id})

def game_autocomplete(request):
    query = request.GET.get('q', '').strip()
    results = []
    if len(query) > 1:
        games = Game.objects.filter(title__icontains=query)[:6]
        for g in games:
            results.append({
                'id': g.id,
                'title': g.title,
                'cover': g.cover_url
            })
    return JsonResponse({'results': results})