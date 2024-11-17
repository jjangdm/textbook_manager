from django import forms
from .models import Book
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field


class TextbookForm(forms.ModelForm):
    book_name = forms.CharField(
        label='교재명',
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'id': 'book_select',  # id 변경
            'aria-label': '교재명'  # 접근성 레이블 추가
        })
    )
    
    price = forms.DecimalField(
        label='가격',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'price_input',  # id 변경
            'aria-label': '가격',  # 접근성 레이블 추가
            'inputmode': 'numeric'
        })
    )
    
    issue_date = forms.DateField(
        label='지급일',
        widget=forms.DateInput(attrs={
            'class': 'form-control flatpickr-date',
            'id': 'issue_date',  # id 변경
            'aria-label': '지급일',  # 접근성 레이블 추가
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = Book
        fields = ['book_name', 'price', 'issue_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'issueBookForm'
        self.helper.form_class = 'form'
        self.helper.label_class = 'form-label'  # 레이블 클래스 추가
        
        # Layout 업데이트
        self.helper.layout = Layout(
            Field('book_name', wrapper_class='mb-3'),
            Field('price', wrapper_class='mb-3'),
            Field('issue_date', wrapper_class='mb-3'),
        )

        # 각 필드의 label_for 설정을 명시적으로 지정
        self.fields['book_name'].label_attrs = {'for': 'book_select'}
        self.fields['price'].label_attrs = {'for': 'price_input'}
        self.fields['issue_date'].label_attrs = {'for': 'issue_date'}