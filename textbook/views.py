# views.py
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from textbook.forms import TextbookForm
# from .forms import TextbookForm
from .models import Student, Book
from django.db.models import Sum, Q
from datetime import date
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Frame, PageTemplate, BaseDocTemplate
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from django.conf import settings
import os


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("NotoSansKR", 9)
        
        # 페이지 번호 (우측)
        page = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(200*mm, 10*mm, page)
        
        # 학원명 (가운데 정렬)
        academy_name = "엠클래스수학과학전문학원"
        academy_name_width = self.stringWidth(academy_name, "NotoSansKR", 9)
        page_width = A4[0]  # A4 용지의 너비
        x_position = (page_width - academy_name_width) / 2
        self.drawString(x_position, 10*mm, academy_name)
        
        # 문서 작성 일시 (좌측)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.drawString(20*mm, A4[1] - 15*mm, f"작성일시: {now}")


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
        # Fix the syntax error in filter and values
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


# 한글 폰트 등록
def register_fonts():
    font_dir = os.path.join(settings.BASE_DIR, 'static', 'fonts')
    pdfmetrics.registerFont(TTFont('NotoSansKR', os.path.join(font_dir, 'NotoSansKR-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('NotoSansKR-Bold', os.path.join(font_dir, 'NotoSansKR-Bold.ttf')))

def generate_report(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    report_type = request.GET.get('type', 'all')  # 'all' or 'unpaid'
    
    all_books = student.books.all().order_by('input_date')
    unpaid_books = student.books.filter(payment_date__isnull=True)
    paid_books = student.books.filter(payment_date__isnull=False)
    
    # 통계 계산
    total_books = all_books.count()
    total_amount = all_books.aggregate(total=Sum('price'))['total'] or 0
    total_unpaid = unpaid_books.aggregate(total=Sum('price'))['total'] or 0

    # PDF 생성
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=30*mm,
        bottomMargin=20*mm
    )

    # 메타데이터 설정을 위한 클래스 정의
    class MetadataCanvas(NumberedCanvas):
        def __init__(self, *args, **kwargs):
            if 'student_name' in kwargs:
                self._student_name = kwargs.pop('student_name')
            super().__init__(*args, **kwargs)
            
        def showPage(self):
            try:
                self.setAuthor(self._student_name)
                self.setTitle(f"{self._student_name} 학생 교재 보고서")
                self.setSubject('교재 보고서')
                self.setCreator('교재 관리 시스템')
            except:
                pass
            super().showPage()

    # 메타데이터를 설정하기 위한 임시 캔버스 생성
    tmp_canvas = canvas.Canvas(buffer)
    tmp_canvas.setTitle(f"{student.name} 학생 {'미납' if report_type == 'unpaid' else '전체'} 교재 보고서")
    tmp_canvas.setAuthor(student.name)
    tmp_canvas.setSubject('교재 보고서')
    tmp_canvas.setCreator('교재 관리 시스템')
    tmp_canvas.save()
    
    # 버퍼 초기화
    buffer.seek(0)
    buffer.truncate(0)
    
    # 실제 문서 생성
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=30*mm,  # 상단 여백 증가
        bottomMargin=20*mm
    )

    # 폰트 등록
    register_fonts()

    # 스타일 정의
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Korean',
        fontName='NotoSansKR',
        fontSize=10,
        leading=14
    ))
    styles.add(ParagraphStyle(
        name='KoreanTitle',
        fontName='NotoSansKR-Bold',
        fontSize=16,
        leading=20,
        alignment=1
    ))

    # 표준 테이블 폭 설정
    TABLE_WIDTH = 170*mm  # A4 용지에 맞는 표준 폭
    
    elements = []
    
    # 제목 및 요약 정보
    title = f"{student.name} 학생 " + ("미납 교재 현황" if report_type == 'unpaid' else "교재 내역서")
    elements.append(Paragraph(title, styles['KoreanTitle']))
    elements.append(Spacer(1, 20))
    
    # 요약 정보
    summary_data = []
    if report_type == 'unpaid':
        summary_data = [
            ['미납된 교재 수:', f"{unpaid_books.count()}권"],  # 수정된 부분
            ['미납 금액:', f"{'{:,}'.format(total_unpaid)}원"],
        ]
    else:
        summary_data = [
            ['전체 교재 수:', f"{total_books}권"],
            ['총 금액:', f"{'{:,}'.format(total_amount)}원"],
            ['미납 금액:', f"{'{:,}'.format(total_unpaid)}원"],
        ]

    summary_table = Table(summary_data, colWidths=[TABLE_WIDTH/2]*2)
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'NotoSansKR'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # 미납 교재 목록
    if report_type == 'unpaid' or report_type == 'all':
        elements.append(Paragraph("미납 교재 목록", styles['KoreanTitle']))
        elements.append(Spacer(1, 10))
        
        unpaid_data = [['No.', '지급일', '교재명', '가격', '상태']]  # '��재명'을 '교재명'으로 수정
        for idx, book in enumerate(unpaid_books, 1):
            unpaid_data.append([
                str(idx),
                book.input_date.strftime('%Y-%m-%d'),
                book.book_name,
                f"{'{:,}'.format(book.price)}원",
                "확인" if book.checking else "미납"  # "미확인"을 "미납"으로 변경
            ])
        
        col_widths = [15*mm, 30*mm, 65*mm, 30*mm, 30*mm]
        unpaid_table = Table(unpaid_data, colWidths=col_widths)
        unpaid_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'NotoSansKR'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # 모든 헤더를 가운데 정렬
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # No. 열
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # 지급일 열
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),    # 교재명 열 내용만 왼쪽 정렬
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),   # ��격 열 내용만 오른쪽 정렬
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # 상태 열
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        elements.append(unpaid_table)  # 테이블 추가

    # 전체 교재 목록 (report_type이 'all'인 경우에만)
    if report_type == 'all':
        elements.append(PageBreak())
        elements.append(Paragraph("전체 교재 목록", styles['KoreanTitle']))
        elements.append(Spacer(1, 10))

        all_data = [['No.', '지급일', '교재명', '가격', '납부상태', '납부일']]
        for idx, book in enumerate(all_books, 1):
            all_data.append([
                str(idx),
                book.input_date.strftime('%Y-%m-%d'),
                book.book_name,
                f"{'{:,}'.format(book.price)}원",
                "납부완료" if book.payment_date else "미납",  # "미납" 텍스트 수정
                book.payment_date.strftime('%Y-%m-%d') if book.payment_date else "-"
            ])
        
        # TABLE_WIDTH를 기준으로 열 너비 비율 조정
        col_widths = [
            TABLE_WIDTH * 0.08,  # No.
            TABLE_WIDTH * 0.15,  # 지급일
            TABLE_WIDTH * 0.35,  # 교재명 (가장 넓게)
            TABLE_WIDTH * 0.15,  # 가격
            TABLE_WIDTH * 0.12,  # 납부상태
            TABLE_WIDTH * 0.15   # 납부일
        ]
        # 합계: 1.0 (100%)
        all_table = Table(all_data, colWidths=col_widths)
        all_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'NotoSansKR'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # 모든 헤더를 가운데 정렬
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # No. 열
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # 지급일 열
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),    # 교재명 열 내용만 왼쪽 정렬
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),   # 가격 열 내용만 오른쪽 정렬
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # 납부상태 열
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # 납부일 열
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        elements.append(all_table)  # 테이블 추가

    # PDF 생성을 위한 캔버스 메이커 함수 수정
    def canvas_maker(filename, pagesize, *args, **kwargs):
        return MetadataCanvas(filename, pagesize=pagesize, student_name=student.name)

    doc.build(elements, canvasmaker=canvas_maker)
    buffer.seek(0)
    
    # 파일명 설정
    report_name = "미납교재" if report_type == 'unpaid' else "전체교재"
    filename = f"{student.name}_{report_name}_보고서_{date.today()}.pdf"
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(buffer.getvalue())
    buffer.close()
    
    return response
