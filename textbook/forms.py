from django import forms
from .models import Textbook

class TextbookForm(forms.ModelForm):
    class Meta:
        model = Textbook
        fields = ['student', 'issue_date', 'book_name', 'price']