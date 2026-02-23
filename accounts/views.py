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

UserModel = get_user_model()


class RegisterView(CreateView):
    model = UserModel
    form_class = AppUserCreationForm
    template_name = 'profiles/register.html'

    # def form_valid(self, form):
    #     self.object = form.save()
    #
    #     return HttpResponseRedirect(self.get_success_url())
    def form_valid(self, form):
        response = super().form_valid(form)

        user = self.object
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(self.request, user)

        return response

    def get_success_url(self):
        return reverse('profile-details', kwargs={'pk': self.object.pk})

        # Note: Signal for profile creation


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
