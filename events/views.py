from profile import Profile

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.db.models.query_utils import Q
from django.shortcuts import redirect

from accounts.models import Profile

from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.utils import timezone

from common.models import EventParticipation

from events.forms import CreateEventForm,  EditEventForm
from events.models import Event, EventPost, EventLike, PostLike
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin



class NewEventView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'events/new-events.html'
    context_object_name = 'new_events'
    paginate_by = 8

    def get_queryset(self):
        today = timezone.localtime().date()
        return Event.objects.filter(start_date__gte=today).order_by('start_date')


class PastEventView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'events/past-event.html'
    context_object_name = 'past_events'
    paginate_by = 8

    def get_queryset(self):
        today = timezone.now().date()
        queryset = Event.objects.filter(start_date__lt=today).order_by('-start_date')

        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(location__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '').strip()
        return context


class CreateEventView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Event
    template_name = 'events/create-event.html'
    success_url = reverse_lazy('new-events')
    form_class = CreateEventForm
    permission_required = 'events.add_event'

    def form_valid(self, form):
        form.instance.creator = self.request.user
        response = super().form_valid(form)
        # Add creator as participant with "Will go" status
        EventParticipation.objects.get_or_create(
            event=self.object,
            user=self.request.user,
            defaults={'status': 'Will go'}
        )
        return response


class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event
    template_name = 'events/events-details.html'
    context_object_name = 'event'
    pk_url_kwarg = 'event_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object


        participants = EventParticipation.objects.filter(event=event, status='Will go').select_related('user')


        profiles = Profile.objects.filter(user__in=[p.user for p in participants])

        creator_profile = getattr(getattr(event, 'creator', None), 'profile', None)

        posts = EventPost.objects.filter(event=event).select_related('user').order_by('created_at')
        likes_count = EventLike.objects.filter(event=event).count()
        liked_by_me = EventLike.objects.filter(event=event, user=self.request.user).exists()

        for post in posts:
            post.liked_by_me = PostLike.objects.filter(post=post, user=self.request.user).exists()

        context.update({
            'participants': profiles,
            'will_go_count': participants.count(),
            'creator_profile': creator_profile,
            'event_posts': posts,
            'likes_count': likes_count,
            'liked_by_me': liked_by_me,
        })




        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        content = request.POST.get('text', '').strip()
        if content:
            EventPost.objects.create(
                event=self.object,
                user=request.user,
                text=content
            )
        return redirect('event-details', event_id=self.object.id)


class EditEventView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Event
    form_class = EditEventForm
    template_name = 'events/change-event.html'
    context_object_name = 'event'
    permission_required = 'events.change_event'

    def get_object(self, queryset=None):
        return get_object_or_404(Event, id=self.kwargs['event_id'])

    def get_success_url(self):
        return reverse_lazy('event-details', kwargs={'event_id': self.object.id})

    def test_func(self):
        return self.get_object().creator == self.request.user

    def form_valid(self, form):
        original = self.get_object()   # ⬅️ КЛЮЧОВИЯ РЕД
        event = form.instance

        if 'image1' not in self.request.FILES:
            event.image1 = original.image1

        if 'image2' not in self.request.FILES:
            event.image2 = original.image2

        if 'image3' not in self.request.FILES:
            event.image3 = original.image3

        return super().form_valid(form)



class DeleteEventView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView, ):
    model = Event
    template_name = 'events/event-delete.html'
    context_object_name = 'event'
    permission_required = 'events.delete_event'

    def get_object(self, queryset=None):
        event_id = self.kwargs['event_id']
        return get_object_or_404(Event, id=event_id)

    def get_success_url(self):
        return reverse_lazy('new-events')

    def test_func(self):
        event = self.get_object()
        return event.creator == self.request.user
