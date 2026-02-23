from django.urls.conf import path


from photos.views import PhotoAddView, PhotoDeleteView, PhotosView, PhotoDetailView



urlpatterns = [
    path('', PhotosView.as_view(), name='photos'),
    path('<int:event_id>/photos/', PhotoAddView.as_view(), name='photos-detail'),
    path('photo/<int:pk>/', PhotoDetailView.as_view(), name='photo-detail'),
    path('photo/<int:pk>/delete/', PhotoDeleteView.as_view(), name='photo-delete'),
]