from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=100)
    student_id = models.IntegerField(unique=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'student'  # 새로운 테이블을 생성하거나, 기존 student 테이블과 연결
        verbose_name = '학생'
        verbose_name_plural = '학생'

class Textbook(models.Model):
    student_name = models.CharField(max_length=100, verbose_name="학생")  # ForeignKey 대신 CharField 사용
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, related_name='textbooks')
    input_date = models.DateField(verbose_name="지급일")
    book_name = models.CharField(max_length=200, verbose_name="교재명")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="가격")
    checking = models.BooleanField(default=False, verbose_name="납부 상황")
    payment_date = models.DateField(null=True, verbose_name="납부일")

    def __str__(self):
        return f"{self.book_name} - {self.student_name}"
    
    class Meta:
        db_table = 'book'
        verbose_name = '교재'
        verbose_name_plural = '교재'