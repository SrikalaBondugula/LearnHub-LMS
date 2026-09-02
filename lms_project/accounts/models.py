from django.db import models

# Create your models here.
class register_tb(models.Model):
    username=models.CharField(max_length=100)
    email=models.CharField(max_length=100)
    phoneNumber=models.CharField(max_length=10,)
    password=models.CharField(max_length=100)
    role_choices=(("student","Student"),("instructor","Instructor"))
    role=models.CharField(max_length=20,choices=role_choices,default="student")
    def __str__(self):
            return self.username

class PasswordResetToken(models.Model):
     user=models.ForeignKey(register_tb,on_delete=models.CASCADE)
     token=models.CharField(max_length=100,unique=True)
     expiry=models.DateTimeField()

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(
        register_tb,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_setup_complete=models.BooleanField(default=False)

    def __str__(self):
        return self.title 

    
class Assignment_details(models.Model):
    title=models.CharField(max_length=100)
    description=models.TextField()
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    instructer_id=models.ForeignKey(register_tb,on_delete=models.CASCADE)


class Quiz_model(models.Model):
     q_title=models.CharField(max_length=100)
     course=models.ForeignKey(Course,on_delete=models.CASCADE)
     total_questions=models.IntegerField(default=1)
     instructer_id=models.ForeignKey(register_tb,on_delete=models.CASCADE)


     



     
class questions_model(models.Model):
    quiz_id=models.ForeignKey(Quiz_model,on_delete=models.CASCADE)
    question=models.TextField()
    option1=models.CharField(max_length=255,)
    option2=models.CharField(max_length=255,)
    option3=models.CharField(max_length=255,)
    option4=models.CharField(max_length=255,)
    option_choices=(("A","Option A"),("B","Option B"),("C","Option C"),("D","Option D"))
    answer=models.CharField(max_length=1,choices=option_choices,default="A")




class Enrolled_courses_model(models.Model):
     user_id=models.ForeignKey(register_tb,on_delete=models.CASCADE)
     course_id=models.ForeignKey(Course,on_delete=models.CASCADE)




class submitted_assignments_model(models.Model):
     user_id = models.ForeignKey( register_tb,on_delete=models.CASCADE)

     assignment_id = models.ForeignKey(Assignment_details,on_delete=models.CASCADE)
     

     submitted_file_url = models.URLField()

class created_modules_model(models.Model):
     instructor_id=models.IntegerField()
     course_id=models.IntegerField()
     module_title=models.CharField(max_length=500)
     module_description=models.CharField(max_length=500)
     pdf_url=models.URLField()
     quiz_id=models.IntegerField()

class completed_quiz_model(models.Model):
     quiz_id=models.IntegerField()
     score=models.IntegerField()
     user_id=models.IntegerField()

