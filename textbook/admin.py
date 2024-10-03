from django.contrib import admin
from django.utils.html import format_html
from django.contrib.humanize.templatetags.humanize import intcomma
from .models import Student, Book
from django.utils import timezone

class BookInline(admin.TabularInline):
    model = Book
    extra = 1
    fields = ['book_name', 'price', 'checking', 'payment_date']

class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'books_count', 'total_price_display')
    search_fields = ['name']
    inlines = [BookInline]

    def books_count(self, obj):
        return obj.books.count()
    books_count.short_description = '미납상태인 교재 수'

    def total_price_display(self, obj):
        total = sum(book.price for book in obj.books.all())
        return format_html('<div style="text-align: right;">{}</div>', intcomma(total))
    total_price_display.short_description = '합계'

class BookAdmin(admin.ModelAdmin):
    list_display = ('student', 'book_name', 'input_date', 'price_display', 'checking', 'payment_status')
    list_filter = ('student', 'checking',)
    search_fields = ['book_name', 'student__name']
    date_hierarchy = 'input_date'
    actions = ['mark_as_paid']

    def price_display(self, obj):
        return format_html('<div style="text-align: right;">{}</div>', intcomma(obj.price))
    price_display.short_description = '가격'

    def payment_status(self, obj):
        if obj.payment_date:
            return obj.payment_date
        return format_html('<span style="color: red;">미납</span>')
    payment_status.short_description = '수납일'

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(payment_date=timezone.now(), checking=True)
        self.message_user(request, f'{updated}개의 교재가 수납 완료로 표시되었습니다.')
    mark_as_paid.short_description = '선택된 교재를 수납 완료로 표시'

admin.site.register(Student, StudentAdmin)
admin.site.register(Book, BookAdmin)