from django.urls import path
from . import views

app_name = 'textbook'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('student/<int:student_id>/', views.student_detail, name='student_detail'),
    path('book/<int:book_id>/mark-as-paid/', views.mark_as_paid, name='mark_as_paid'),
]