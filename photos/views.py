
from django.views.generic.list import ListView

from django.views.generic import  DetailView

from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin

from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404, redirect
from .forms import PhotoUploadForm
from events.models import Event
from photos.models import Photo

# Create your views here.


class PhotosView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'photos/photos.html'
    context_object_name = 'events'
    paginate_by = 8

    def get_queryset(self):
        return Event.objects.all().order_by('-start_date')







class PhotoAddView(LoginRequiredMixin, FormView):
    template_name = 'photos/photos-detail.html'
    form_class = PhotoUploadForm

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=self.kwargs['event_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        context['photos'] = self.event.user_photos.select_related('user__profile').all()
        return context

    def post(self, request, *args, **kwargs):
        # We'll handle multiple files manually here
        self.event = get_object_or_404(Event, pk=self.kwargs['event_id'])
        files = request.FILES.getlist('images')
        error = None

        if not files:
            error = "You must select at least one image."
        else:
            for f in files:
                form = PhotoUploadForm(request.POST, {'image': f})
                if not form.is_valid():
                    error = form.errors.get('image', ["Invalid file"])[0]
                    break
                # Create each photo
                photo = Photo(
                    event=self.event,
                    user=request.user,
                    image=f
                )
                photo.save()

        if error:
            context = self.get_context_data(form=PhotoUploadForm(), form_error=error)
            return self.render_to_response(context)
        return redirect(self.request.path)



class PhotoDetailView(LoginRequiredMixin,PermissionRequiredMixin,DetailView):
    model = Photo
    template_name = 'photos/photos-detail.html'
    context_object_name = 'photo'

class PhotoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Photo
    template_name = 'photos/photos-delete.html'

    def test_func(self):
        photo = self.get_object()
        user = self.request.user
        return photo.user == user or user.has_perm('photos.delete_photo')

    def get_success_url(self):
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse_lazy('photos-detail', kwargs={'event_id': self.object.event.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.object.event
        return context