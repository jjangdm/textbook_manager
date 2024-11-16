# views.py

from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
# from .forms import TextbookForm
from .models import Student, Book
from django.db.models import Sum, Q
from datetime import date
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def dashboard(request):
    search_query = request.GET.get('search', '').strip()
    
    # 기본 쿼리셋 생성
    students = Student.objects.annotate(
        unpaid_amount=Sum(
            'books__price',
            filter=Q(books__payment_date__isnull=True)
        )
    )
    
    # 검색 적용
    if search_query:
        students = students.filter(name__icontains=search_query)
    
    students = students.order_by('name')
    
    # 전체 통계 계산 (페이지네이션 적용 전)
    total_students = students.count()
    total_unpaid = sum(student.unpaid_amount or 0 for student in students)
    
    # 페이지네이션 적용
    paginator = Paginator(students, 20)  # 한 페이지당 20명
    page = request.GET.get('page')
    
    try:
        students_page = paginator.page(page)
    except PageNotAnInteger:
        students_page = paginator.page(1)
    except EmptyPage:
        students_page = paginator.page(paginator.num_pages)
    
    # 현재 페이지 범위 계산
    current_page = students_page.number
    total_pages = paginator.num_pages
    
    # 표시할 페이지 범위 (현재 페이지 앞뒤로 2페이지씩)
    page_range = range(max(1, current_page - 2), 
                      min(total_pages + 1, current_page + 3))
    
    context = {
        'students': students_page,
        'search_query': search_query,
        'total_students': total_students,
        'total_unpaid': total_unpaid,
        'page_range': page_range,
        'total_pages': total_pages,
        'current_page': current_page
    }
    return render(request, 'textbook/dashboard.html', context)


def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    unpaid_books = student.books.filter(payment_date__isnull=True)
    paid_books = student.books.filter(payment_date__isnull=False)
    
    total_unpaid = unpaid_books.aggregate(total=Sum('price'))['total'] or 0
    total_paid = paid_books.aggregate(total=Sum('price'))['total'] or 0
    
    context = {
        'student': student,
        'unpaid_books': unpaid_books,
        'paid_books': paid_books,
        'total_unpaid': total_unpaid,
        'total_paid': total_paid,
        'today' : date.today(),
    }
    return render(request, 'textbook/student_detail.html', context)


def mark_as_paid(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    
    if request.method == 'POST':
        payment_date_str = request.POST.get('payment_date')
        try:
            payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
            book.payment_date = payment_date
            book.save()
            messages.success(request, f'{book.book_name} 교재가 납부 완료되었습니다.')
        except (ValueError, TypeError):
            messages.error(request, '올바른 날짜 형식을 입력해주세요.')
    
    return redirect('textbook:student_detail', student_id=book.student.id)

# def search_students(request):
#     if request.method == 'POST':
#         student_name = request.POST.get('student_name')
#         student = get_object_or_404(Student, name=student_name)
#         textbooks = student.books.all().order_by('input_date')
#         return render(request, 'students_search.html', {'student': student, 'textbooks': textbooks})
#     return render(request, 'students_search.html')

# def dashboard(request):
#     students = Book.objects.annotate(total_unpaid_price=models.Sum('price', filter=models.Q(checking=False))).order_by('-total_unpaid_price')
#     return render(request, 'dashboard.html', {'students': students})

# def mark_as_paid(request, textbook_id):
#     # Use a form or service layer to handle payments
#     book = get_object_or_404(Book, id=textbook_id)
#     book.is_paid = True
#     book.save()
#     return JsonResponse({'status': 'success'})

# def mark_all_as_paid(request, student_id):
#     # Consider using a loop or batch process instead of updating all books at once
#     student = get_object_or_404(Student, id=student_id)
#     for book in student.books.all():
#         book.is_paid = True
#         book.save()
#     return JsonResponse({'status': 'success'})

# def new_textbook(request):
#     if request.method == 'POST':
#         form = TextbookForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('search_students')
#     else:
#         form = TextbookForm()
#     return render(request, 'new_textbook.html', {'form': form})

