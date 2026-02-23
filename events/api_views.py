from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone

from rest_framework import generics, permissions, status
from .models import EventPost, EventLike, Event, PostLike
from .serializers import EventPostSerializer, EventLikeSerializer
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from django.db.models import Q
from .models import Event
from .serializers import EventSerializer


class PastEventsAPIPagination(PageNumberPagination):
    page_size = 8

class PastEventsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        queryset = Event.objects.filter(start_date__lt=today).order_by('-start_date')

        query = request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(location__icontains=query))

        paginator = PastEventsAPIPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = EventSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)



class EventPostListCreateView(generics.ListCreateAPIView):
    serializer_class = EventPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]



    def get_queryset(self):
        event_id = self.kwargs['event_id']
        return EventPost.objects.filter(event_id=event_id).order_by('-created_at')

    def perform_create(self, serializer):
        event = get_object_or_404(Event, pk=self.kwargs['event_id'])
        serializer.save(user=self.request.user, event=event)

    def post(self, request, *args, **kwargs):
        """Custom POST to support JSON response for AJAX"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = get_object_or_404(Event, pk=self.kwargs['event_id'])
        serializer.save(user=request.user, event=event)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class EventLikeToggleView(generics.GenericAPIView):
    serializer_class = EventLikeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        like, created = EventLike.objects.get_or_create(event=event, user=request.user)
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        count = EventLike.objects.filter(event=event).count()
        return Response({'liked': liked, 'likes_count': count})


class PostLikeToggleView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, post_id):
        post = get_object_or_404(EventPost, pk=post_id)
        like, created = PostLike.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        count = post.likes.count()
        return Response({'liked': liked, 'likes_count': count})


class EditEventPostView(APIView):
    permission_classes = [permissions.IsAuthenticated] # correct

    def post(self, request, post_id):
        post = get_object_or_404(EventPost, id=post_id)

        if post.user != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        new_text = request.data.get('text', '').strip()
        if not new_text:
            return Response({'error': 'Text cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        post.text = new_text
        post.save()

        return Response({
            'message': 'Post updated successfully',
            'text': post.text,
            'updated_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })


class DeleteEventPostView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(EventPost, id=post_id)

        if post.user != request.user and not request.user.has_perm('events.delete_eventpost'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        post.delete()
        return Response({'message': 'Post deleted successfully'})


class AllEventsAPIView(ListAPIView):
    queryset = Event.objects.all().order_by('-start_date')
    serializer_class = EventSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(location__icontains=query)
            )
        return queryset
