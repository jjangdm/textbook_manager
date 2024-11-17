# views.py
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages

from textbook.forms import TextbookForm
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


def search_students(request):
    query = request.GET.get('query', '').strip()
    if query:
        students = Student.objects.filter(name__icontains=query).values('id', 'name')
        return JsonResponse(list(students), safe=False)
    return JsonResponse([], safe=False)


def get_books(request):
    query = request.GET.get('term', '')
    # values()로 가져온 후 파이썬에서 중복 제거
    books = Book.objects.filter(book_name__icontains=query)\
        .values('book_name', 'price')\
        .order_by('book_name')
    
    # 중복 제거를 위해 dictionary 사용
    unique_books = {}
    for book in books:
        book_name = book['book_name']
        if book_name not in unique_books:
            unique_books[book_name] = book
    
    return JsonResponse(list(unique_books.values()), safe=False)


def issue_book(request):
    student_id = request.GET.get('student_id')
    student = None
    
    if student_id:
        student = get_object_or_404(Student, pk=student_id)
        
    if request.method == 'POST':
        form = TextbookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            if student_id:
                book.student = student
            book.save()
            messages.success(request, f'{book.book_name} 교재가 {book.student.name} 학생에게 지급되었습니다.')
            return redirect('textbook:student_detail', student_id=book.student.id)
    else:
        initial_data = {}
        if student:
            initial_data['student'] = student.id
        form = TextbookForm(initial=initial_data)
        
        # 데이터베이스에서 모든 교재 정보를 가져옴
        books_queryset = Book.objects.all().values('book_name', 'price')
        # print(f"Books queryset: {books_queryset.query}")  # 디버깅용
        
        # 중복 제거를 위한 dictionary
        unique_books = {}
        for book in books_queryset:
            book_name = book['book_name']
            if book_name not in unique_books:
                unique_books[book_name] = {
                    'book_name': book_name,
                    'price': book['price']
                }
        
        initial_books = list(unique_books.values())
        # print(f"Initial books: {initial_books}")  # 디버깅용

    context = {
        'form': form,
        'initial_books': initial_books,
        'selected_student': student,
        'student_id': student_id
    }

    return render(request, 'textbook/issue_book.html', context)