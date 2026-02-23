from django.urls.conf import path, include

from events import views
from events.api_views import PastEventsAPI, EventPostListCreateView, EventLikeToggleView, EditEventPostView, \
    DeleteEventPostView, AllEventsAPIView, PostLikeToggleView

urlpatterns = [
    path('new-events/', views.NewEventView.as_view(), name='new-events'),
    path('past-events/', views.PastEventView.as_view(), name='past-events'),
    path('api/past-events/', PastEventsAPI.as_view(), name='api-past-events'),
    path('api/events/', AllEventsAPIView.as_view(), name='api-events'),

    path('event/create/', views.CreateEventView.as_view(), name='create-event'),
    path('events/<int:event_id>/', include([
        path('', views.EventDetailView.as_view(), name='event-details'),
        path('edit/', views.EditEventView.as_view(), name='edit-event'),
        path('delete/', views.DeleteEventView.as_view(), name='delete-event'),
        path('posts/', EventPostListCreateView.as_view(), name='event-posts'),
        path('like/', EventLikeToggleView.as_view(), name='event-like'),

    ])),
    path('api/posts/<int:post_id>/like/', PostLikeToggleView.as_view(), name='post-like'),
    path('api/posts/<int:post_id>/edit/', EditEventPostView.as_view(), name='edit-event-post'),
    path('api/posts/<int:post_id>/delete/', DeleteEventPostView.as_view(), name='delete-event-post'),
]
