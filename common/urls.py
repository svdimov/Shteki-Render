from django.urls.conf import path

from common import views, api_views
from common.views import ContactSuccessView

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('about/', views.AboutAs.as_view(), name='about'),
    path('api/events/<int:pk>/status/', api_views.EventStatusAPI.as_view(), name='api-event-status'),
    path('contact/', views.ContactView.as_view(), name='contacts'),
    path('contact/success/', ContactSuccessView.as_view(), name='contact-success'),

]
