from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='학생')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'student'
        ordering = ['name']
        verbose_name = '학생'
        verbose_name_plural = '학생'

class Book(models.Model):
    input_date = models.DateField(verbose_name='지급일')
    book_name = models.CharField(max_length=255, verbose_name='교재')
    price = models.IntegerField(verbose_name='가격')
    checking = models.BooleanField(default=False, verbose_name='상태')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='books', verbose_name='학생')
    payment_date = models.DateField(null=True, blank=True, verbose_name='수납일')

    def __str__(self):
        return f"{self.book_name} ({self.student.name})"

    class Meta:
        db_table = 'book'
        ordering = ['-input_date']
        verbose_name = '교재'
        verbose_name_plural = '교재'

