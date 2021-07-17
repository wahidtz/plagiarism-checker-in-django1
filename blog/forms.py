from django import forms

from blog.models import Document


class DocumentForm(forms.ModelForm):
    # document= forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    class Meta:
        model = Document
        fields = ('document',)
