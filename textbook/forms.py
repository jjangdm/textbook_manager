from django import forms
from textbook.models import Book


class TextbookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['student', 'input_date', 'book_name', 'price']
