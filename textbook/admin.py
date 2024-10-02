from django.contrib import admin
from .models import Student, Textbook
from django.utils import timezone
from django.utils.html import format_html
from django.db import models


class TextbookInline(admin.TabularInline):
    model = Textbook
    extra = 0

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)

@admin.register(Textbook)
class TextbookAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'input_date', 'book_name', 'formatted_price', 'checking', 'payment_date')
    list_filter = ('student_name', 'checking', 'input_date',)
    search_fields = ('book_name', 'student_name')
    date_hierarchy = 'input_date'
    
    # 학생 이름으로 필터링하는 기능 추가
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        try:
            search_term_as_int = int(search_term)
        except ValueError:
            pass
        else:
            queryset |= self.model.objects.filter(student__student_id=search_term_as_int)
        return queryset, use_distinct
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['total_price'] = Textbook.objects.aggregate(total=models.Sum('price'))['total']
        return super().changelist_view(request, extra_context=extra_context)
    

    # 결제 처리를 위한 액션 추가
    actions = ['mark_as_paid']

    def mark_as_paid(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(checking=True, payment_date=timezone.now())
        self.message_user(request, f'{updated} 개의 교재가 결제 처리되었습니다.')
    mark_as_paid.short_description = "선택된 교재를 결제 처리"


    def formatted_price(self, obj):
        return format_html('<div style="text-align: right; white-space: nowrap;">{}</div>', '{:,}'.format(int(obj.price)))
    
    formatted_price.short_description = '가격'
    formatted_price.admin_order_field = 'price'