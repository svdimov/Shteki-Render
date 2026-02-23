from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm, SetPasswordForm, \
    PasswordChangeForm
from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from django.utils.translation import gettext_lazy as _
from accounts.models import Profile

UserModel = get_user_model()

class AppUserCreationForm(UserCreationForm):
    class Meta:
        model = UserModel
        fields = ['email','password1','password2']


        labels = {
            'email': _('Email'),
            'password1': 'Password',
            'password2': 'Repeat Password'
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Премахваме default help_text за паролите
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''

        # Задаваме placeholder-и директно тук:
        self.fields['email'].widget.attrs.update({
            'placeholder': _('Enter your email')
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': _('Enter your password')
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': _('Repeat your password')
        })


class AppUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = UserModel


# accounts/forms.py


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].help_text = ''
        self.fields['new_password2'].help_text = ''


class CustomAdminAuthenticationForm(AdminAuthenticationForm):
    error_messages = {
        **AdminAuthenticationForm.error_messages,
        "locked": _("Your account is locked due to too many failed login attempts."),
    }

    def clean(self):
        # Check lock status before authenticating (username is your email)
        username = self.data.get("username")
        if username:
            User = get_user_model()
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                user = None
            if user and (getattr(user, "is_locked", False) or getattr(user, "failed_login_attempts", 0) >= 3):
                raise forms.ValidationError(self.error_messages["locked"], code="locked")
        # Fall back to normal auth flow
        return super().clean()

    def confirm_login_allowed(self, user):
        # Double guard for the case of correct password on a locked account
        if getattr(user, "is_locked", False) or getattr(user, "failed_login_attempts", 0) >= 3:
            raise forms.ValidationError(self.error_messages["locked"], code="locked")
        return super().confirm_login_allowed(user)








class ProfileBaseForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = "__all__"

class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': _('Please enter a correct %(username)s and password.'),

    }
    username = forms.EmailField(
        label=_('Email'),  # translatable label
        widget=forms.EmailInput(attrs={
            'placeholder': _('Enter your email'),
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        label=_('Password'),
        strip=False,  # keep spaces; same as AuthenticationForm default
        widget=forms.PasswordInput(attrs={
            'placeholder': _('Enter your password'),
            'autocomplete': 'current-password',
            'class': 'u-input u-input-rectangle u-white u-border-1 u-border-grey-30',
        })
    )


    def confirm_login_allowed(self, user):
        if getattr(user, 'is_locked', False) or getattr(user, 'failed_login_attempts', 0) >= 3:
            raise forms.ValidationError(
                'Your account is locked due to too many failed login attempts.',
                code='locked',
            )
        super().confirm_login_allowed(user)

class ProfileEditForm(ProfileBaseForm):
    class Meta:
        model = Profile
        exclude = ['user']

        widgets = {

            'profile_picture': forms.FileInput(attrs={'accept': 'image/*'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }



class ProfileCreateForm(ProfileBaseForm):

    ...

class ProfileDeleteForm(ProfileBaseForm):
    ...

class CustomChangePasswordForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['new_password2'].label = 'Repeat  New Password'


        self.fields['new_password1'].help_text = ''
        self.fields['new_password2'].help_text = ''


