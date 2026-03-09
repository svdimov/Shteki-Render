from django.contrib.auth import views as auth_views
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.views import  LoginView, PasswordResetConfirmView

from django.shortcuts import get_object_or_404

from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, DetailView, DeleteView

from accounts.forms import AppUserCreationForm, ProfileEditForm, CustomAuthenticationForm, CustomChangePasswordForm
from accounts.models import Profile

from django.utils import timezone
from django.contrib.auth.forms import PasswordResetForm
from django.shortcuts import render

from accounts.utils import send_activation_email
from django.shortcuts import redirect

from django.views.generic import TemplateView


from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View

from accounts.tokens import account_activation_token

UserModel = get_user_model()


class RegisterView(CreateView):
    model = UserModel
    form_class = AppUserCreationForm
    template_name = 'profiles/register.html'
    success_url = reverse_lazy('activation-email-sent')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.is_active = False
        self.object.save()

        send_activation_email(self.request, self.object)

        return redirect(self.get_success_url())


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = 'profiles/login.html'

    max_attempts = 3
    ock_minutes = 15


    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            email = request.POST.get('username')
            try:
                user = UserModel.objects.get(email=email)
                if user.account_locked_until and user.account_locked_until > timezone.now():
                    return render(request, 'profiles/account-login.html')
            except UserModel.DoesNotExist:
                pass
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        user.failed_login_attempts = 0
        user.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        email = form.data.get('username')
        try:
            user = UserModel.objects.get(email=email)
            if user.is_locked:
                return render(self.request, 'profiles/account-login.html')

            user.failed_login_attempts += 1
            if user.failed_login_attempts >= self.max_attempts:
                user.is_locked = True
                user.failed_login_attempts = 0  # reset attempts
                reset_form = PasswordResetForm({'email': email})
                if reset_form.is_valid():
                    reset_form.save(
                        request=self.request,
                        email_template_name='profiles/password_reset_email.html',
                        subject_template_name='profiles/password_reset_subject.txt'
                    )
            user.save()
        except UserModel.DoesNotExist:
            pass

        return super().form_invalid(form)


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'profiles/profile-details.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        # We assume the Profile model has a field named 'user' that links to the UserModel.
        return get_object_or_404(Profile, user__pk=self.kwargs.get('pk'))


class ProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Profile
    form_class = ProfileEditForm
    template_name = 'profiles/edit-profile.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, user=self.request.user)

    def test_func(self):
        return self.request.user.pk == self.kwargs['pk']

    def get_success_url(self) -> str:
        return reverse('profile-details', kwargs={'pk': self.object.pk})


class ProfileDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = UserModel
    template_name = 'profiles/delete-profile.html'
    success_url = reverse_lazy('home')

    def test_func(self):
        # This ensures a user can only delete their own account.
        # self.get_object() safely retrieves the user instance from the URL's pk.
        return self.request.user == self.get_object()


class ChangePasswordView(auth_views.PasswordChangeView):
    template_name = 'profiles/change-password.html'
    success_url = reverse_lazy('password-change-done')
    form_class = CustomChangePasswordForm


class ChangePasswordDoneView(auth_views.PasswordChangeDoneView):
    template_name = 'profiles/change-password-done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.user
        user.is_locked = False
        user.failed_login_attempts = 0
        user.save()
        return response

#



class ActivationEmailSentView(TemplateView):
    template_name = 'profiles/activation-email-sent.html'









class ActivateAccountView(View):
    success_template_name = "profiles/activation-success.html"
    invalid_template_name = "profiles/activation-invalid.html"

    def get(self, request, uidb64, token, *args, **kwargs):
        user = None

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = UserModel.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            pass

        if user and account_activation_token.check_token(user, token):
            if not user.is_active:
                user.is_active = True
                user.save(update_fields=["is_active"])

            return render(
                request,
                self.success_template_name,
                {"activated_user": user},
            )

        return render(request, self.invalid_template_name)