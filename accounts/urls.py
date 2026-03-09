from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.urls import include, path

from accounts import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name='register'),

    path(
        "activation-email-sent/",
        views.ActivationEmailSentView.as_view(),
        name="activation-email-sent",
    ),
    path(
        "activate/<uidb64>/<token>/",
        views.ActivateAccountView.as_view(),
        name="activate-account",
    ),

    path("login/", views.CustomLoginView.as_view(), name='login'),
    path("logout/", LogoutView.as_view(), name='logout'),

    path(
        "password-reset/",
        views.CustomPasswordResetView.as_view(),
        name='password_reset',
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name='profiles/password_reset_done.html'
        ),
        name='password_reset_done',
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.CustomPasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name='profiles/password_reset_complete.html'
        ),
        name='password_reset_complete',
    ),

    path('password-change/', views.ChangePasswordView.as_view(), name='password-change'),
    path('password-change/done/', views.ChangePasswordDoneView.as_view(), name='password-change-done'),

    path("profile/<int:pk>/", include([
        path('', views.ProfileDetailView.as_view(), name='profile-details'),
        path('edit/', views.ProfileEditView.as_view(), name='edit-profile'),
        path('delete/', views.ProfileDeleteView.as_view(), name='delete-profile'),
    ])),
]