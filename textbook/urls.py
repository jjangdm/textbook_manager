from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_search, name='student_search'),
    path('mark_as_paid/<int:textbook_id>/', views.mark_as_paid, name='mark_as_paid'),
    path('mark_all_as_paid/<int:student_id>/', views.mark_all_as_paid, name='mark_all_as_paid'),
    path('new_textbook/', views.new_textbook, name='new_textbook'),
]