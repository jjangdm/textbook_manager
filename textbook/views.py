from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Student, Textbook
from .forms import TextbookForm

def student_search(request):
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        student = get_object_or_404(Student, name=student_name)
        textbooks = student.textbooks.all().order_by('issue_date')
        return render(request, 'textbooks/student_search.html', {'student': student, 'textbooks': textbooks})
    return render(request, 'textbooks/student_search.html')

def mark_as_paid(request, textbook_id):
    textbook = get_object_or_404(Textbook, id=textbook_id)
    textbook.is_paid = True
    textbook.save()
    return JsonResponse({'status': 'success'})

def mark_all_as_paid(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    student.textbooks.update(is_paid=True)
    return JsonResponse({'status': 'success'})

def new_textbook(request):
    if request.method == 'POST':
        form = TextbookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('student_search')
    else:
        form = TextbookForm()
    return render(request, 'textbooks/new_textbook.html', {'form': form})