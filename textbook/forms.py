from django import forms
from .models import Book
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field


class TextbookForm(forms.ModelForm):
    book_name = forms.CharField(
        label='교재명',
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'id': 'book_select',
        })
    )
    
    price = forms.IntegerField(
        label='가격',
        required=True,
        widget=forms.TextInput(attrs={  # NumberInput에서 TextInput으로 변경
            'class': 'form-control',
            'id': 'price_input',
        })
    )
    
    issue_date = forms.DateField(
        label='지급일',
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control flatpickr-date',
            'id': 'issue_date',
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = Book
        fields = ['book_name', 'price']

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if isinstance(price, str):
            # 쉼표 제거 및 숫자만 추출
            price = int(''.join(filter(str.isdigit, price)))
        return price

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'issueBookForm'
        self.helper.layout = Layout(
            Field('book_name', wrapper_class='mb-3'),
            Field('price', wrapper_class='mb-3'),
            Field('issue_date', wrapper_class='mb-3'),
        )