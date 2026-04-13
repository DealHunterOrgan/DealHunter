from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)


class EditProfileForm(forms.ModelForm):
    AVATAR_CHOICES = [
        ('avatar1.png', 'Gamer 1'),
        ('avatar2.png', 'Gamer 2'),
        ('avatar3.png', 'Gamer 3'),
        ('avatar4.png', 'Gamer 4'),
        ('avatar5.png', 'Gamer 5'),
        ('avatar6.png', 'Gamer 6'),
    ]

    avatar = forms.ChoiceField(
        choices=AVATAR_CHOICES,
        widget=forms.RadioSelect,
        required=False,
        label="Selecciona tu Avatar"
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Dejar en blanco para no cambiar'}),
        required=False,
        label="Nueva Contraseña"
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        # Bloqueamos el email para que solo sea lectura
        self.fields['email'].disabled = True