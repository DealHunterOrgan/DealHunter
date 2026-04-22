from behave import given, when, then
from django.contrib.auth.models import User
from games.models import Game, Review
from django.urls import reverse

@given('an existing user "{username}" with password "{password}"')
def step_create_user(context, username, password):
    if not User.objects.filter(username=username).exists():
        User.objects.create_user(username=username, password=password)

@given('an existing game titled "{title}"')
def step_create_game(context, title):
    context.game, _ = Game.objects.get_or_create(title=title, defaults={'score': 90})

@given('the user "{username}" has a review with content "{content}" and rating "{rating}" for "{title}"')
def step_create_review(context, username, content, rating, title):
    user = User.objects.get(username=username)
    game = Game.objects.get(title=title)
    context.review = Review.objects.create(user=user, game=game, content=content, rating=int(rating))

@given('I log in with username "{username}" and password "{password}"')
def step_login(context, username, password):
    login_url = reverse('games:login') + '?next=' + reverse('games:home')
    context.browser.visit(login_url)
    context.browser.fill('username', username)
    context.browser.fill('password', password)
    context.browser.find_by_css('.btn-submit').first.click()

@when('I view the game "{title}" details')
def step_view_game(context, title):
    game = Game.objects.get(title=title)
    context.browser.visit(reverse('games:detail', kwargs={'pk': game.id}))

@when('I fill in the add review form with "{content}" and rating "{rating}"')
def step_fill_review(context, content, rating):
    context.browser.find_by_css('textarea[name="content"]').first.fill(content)
    context.browser.select('rating', rating)

@when('I click the publish button')
def step_publish_review(context):
    context.browser.find_by_text('Post comment').first.click()

@when('I update my review to "{content}"')
def step_update_review(context, content):
    form_css = f'#review-edit-{context.review.id}'
    context.browser.find_by_css(f'{form_css} textarea[name="content"]').first.fill(content)
    context.browser.find_by_text('Save').first.click()

@when('I click the Delete button for my review')
def step_delete_review(context):
    context.browser.find_by_css('button[title="Eliminar comentario"]').first.click()

@then('I should see "{text}" in the reviews list')
def step_should_see(context, text):
    assert context.browser.is_text_present(text), f'Error: No s\'ha trobat el text "{text}"'

@then('I should not see "{text}" in the reviews list')
def step_should_not_see(context, text):
    assert context.browser.is_text_not_present(text), f'Error: El text "{text}" encara hi és!'

@then('I should not see the Edit or Delete buttons')
def step_should_not_see_buttons(context):
    assert context.browser.is_element_not_present_by_css('button[title="Eliminar comentario"]')
    assert context.browser.is_element_not_present_by_css('button[title="Editar comentario"]')