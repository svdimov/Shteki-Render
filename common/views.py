from django.urls.base import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from accounts.models import Profile
from django.views.generic import FormView
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from common.forms import ContactForm


# Create your views here.

from django.shortcuts import render


def custom_404(request, exception):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)

class HomePageView(TemplateView):
    template_name = 'index.html'


class AboutAs(LoginRequiredMixin, ListView):
    model = Profile
    template_name = 'members.html'
    context_object_name = 'profiles'
    paginate_by = 6

    #
    def get_queryset(self):
        return Profile.objects.select_related('user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_profiles'] = Profile.objects.count()
        context['administrator_count'] = Profile.objects.filter(user__groups__name='Administrators').distinct().count()
        context['moderator_count'] = Profile.objects.filter(user__groups__name='Moderators').distinct().count()
        context['collaborator_count'] = Profile.objects.filter(user__groups__name='Collaborators').distinct().count()
        return context


from django.core.mail import EmailMessage
from django.conf import settings


from django.views.generic import FormView
from django.urls import reverse_lazy
from django.conf import settings

from common.brevo_email import send_brevo_contact_email
from .forms import ContactForm


class ContactView(FormView):
    template_name = 'contacts/contacts.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact-success')

    def form_valid(self, form):
        subject = f"[Contact] {form.cleaned_data['name']} <{form.cleaned_data['email']}>"
        body = (
            f"From: {form.cleaned_data['name']} <{form.cleaned_data['email']}>\n\n"
            f"{form.cleaned_data['message']}"
        )

        send_brevo_contact_email(
            subject=subject,
            body=body,
            reply_to=form.cleaned_data["email"],
        )

        return super().form_valid(form)


class ContactSuccessView(TemplateView):
    template_name = 'contacts/contact-success.html'
