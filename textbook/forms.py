from django import forms
from .models import Book
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field

class TextbookForm(forms.ModelForm):
    book_name = forms.CharField(
        label='교재명',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_book_name',
            'name': 'book_name'
        })
    )
    
    price = forms.DecimalField(
        label='가격',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_price',
            'name': 'price'
        })
    )
    
    issue_date = forms.DateField(
        label='지급일',
        widget=forms.DateInput(attrs={
            'class': 'form-control flatpickr-date',
            'id': 'id_issue_date',
            'name': 'issue_date'
        })
    )

    class Meta:
        model = Book
        fields = ['book_name', 'price', 'issue_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # crispy forms 설정
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'textbook_form'
        self.helper.form_class = 'form'
        
        # 각 필드에 대한 crispy forms 레이아웃 설정
        self.helper.layout = Layout(
            Field('book_name', css_class='form-control'),
            Field('price', css_class='form-control'),
            Field('issue_date', css_class='form-control flatpickr-date'),
        )