
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from accounts import views
from accounts.forms import CustomSetPasswordForm
from accounts.views import CustomLoginView, CustomPasswordResetConfirmView

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name='register'),
    path("login/", CustomLoginView.as_view(), name='login'),
    path("logout/", LogoutView.as_view(), name='logout'),

    # Forgot password
    path("password-reset/", auth_views.PasswordResetView.as_view(
        template_name='profiles/password_reset.html'
    ), name='password_reset'),

    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name='profiles/password_reset_done.html'
    ), name='password_reset_done'),

    path("reset/<uidb64>/<token>/", CustomPasswordResetConfirmView.as_view(
        form_class=CustomSetPasswordForm,
        template_name='profiles/password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name='profiles/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Change password
    path('password-change/', views.ChangePasswordView.as_view(), name='password-change'),
    path('password-change/done/', views.ChangePasswordDoneView.as_view(), name='password-change-done'),


    path("profile/<int:pk>/", include([
        path('', views.ProfileDetailView.as_view(), name='profile-details'),
        path('edit/', views.ProfileEditView.as_view(), name='edit-profile'),
        path('delete/', views.ProfileDeleteView.as_view(), name='delete-profile'),
    ])),
]
