from datetime import date

from django.test import TestCase
from django.urls import reverse

from .models import Game


class GameSearchTests(TestCase):
    def setUp(self):
        Game.objects.create(
            title='Elden Ring',
            api_ID='elden-ring',
            score='9.50',
            launch_date=date(2022, 2, 25),
            cover_url='https://example.com/elden-ring.jpg',
        )
        Game.objects.create(
            title='Celeste',
            api_ID='celeste',
            score='9.10',
            launch_date=date(2018, 1, 25),
            cover_url='https://example.com/celeste.jpg',
        )

    def test_search_filters_games_by_title(self):
        response = self.client.get(reverse('games:home'), {'q': 'elden'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Elden Ring')
        self.assertNotContains(response, 'Celeste')
        self.assertEqual(response.context['search_query'], 'elden')

    def test_empty_search_shows_all_games(self):
        response = self.client.get(reverse('games:home'), {'q': ''})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Elden Ring')
        self.assertContains(response, 'Celeste')
        self.assertEqual(response.context['search_query'], '')
        self.assertFalse(response.context['is_paginated'])
