from django import forms

from events.models import Event


class EventBaseForm(forms.ModelForm):
    class Meta:
        model = Event
        exclude = ['creator']

        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Event Name'}),
            'location': forms.TextInput(attrs={'placeholder': 'Event Location'}),
            'location_url': forms.URLInput(attrs={'placeholder': 'Event Location URL'}),
            'description': forms.Textarea(attrs={'placeholder': 'Event Description'}),
            'days': forms.NumberInput(attrs={'placeholder': 'Event Days'}),
            'start_date': forms.DateInput(attrs={'placeholder': 'Start Date', 'type': 'date'}),
            'city': forms.TextInput(attrs={'placeholder': 'Event City'}),
            'image1': forms.FileInput(attrs={'placeholder': 'Event Image 1'}),
            'image2': forms.FileInput(attrs={'placeholder': 'Event Image 2'}),
            'image3': forms.FileInput(attrs={'placeholder': 'Event Image 3'}),
            'status': forms.Select(attrs={'class': 'u-select-style'}),
        }


class CreateEventForm(EventBaseForm):
    pass


class DetailsEventForm(EventBaseForm):
    pass


class EditEventForm(EventBaseForm):
    pass


class DeleteEventForm(EventBaseForm):
    pass
