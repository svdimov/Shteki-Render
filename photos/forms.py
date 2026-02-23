from django import forms
from photos.models import Photo


class PhotoBaseForm(forms.ModelForm):
    class Meta:
        model = Photo
        exclude = ['user']





class PhotoUploadForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image']
