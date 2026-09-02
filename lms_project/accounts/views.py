from django.shortcuts import render,redirect
from django.http import HttpResponse,JsonResponse
from django.template.loader import render_to_string
from .models import register_tb,Course,Assignment_details,Quiz_model,Enrolled_courses_model,submitted_assignments_model,questions_model,created_modules_model,completed_quiz_model,PasswordResetToken
from django.contrib import messages
from . serializer import register_tb_serializer,Course_serializer,create_assignment_serializer,Quiz_serializer,Question_serializer,enrolled_courses_serializer,submitted_assignments_serializer,created_modules_serializer,complete_quiz_serializer
from . password import hash_password,check_password
import cloudinary
import cloudinary.uploader
from weasyprint import HTML
from django.conf import settings
from django.core.mail import send_mail,EmailMultiAlternatives
import secrets
from datetime import timedelta
from django.utils import timezone

# Create your views here.
def login_page(req):
    if req.method=="POST":
        input_data=req.POST.copy()
        if not register_tb.objects.filter(email=input_data["email"]):
            messages.error(req,"user not exist please login")
            return redirect("register")
        else:
            db_data=register_tb.objects.get(email=input_data["email"])
            if check_password(input_data["password"],db_data.password):
               if db_data.role=="student":
                     response=redirect("dashboard")
               else:
                    response=redirect("instructor_dashboard")
                   
               response.set_cookie(
                   key="login",
                   value=True
               )
               response.set_cookie(
                   key="username",
                   value=db_data.username
               )
               response.set_cookie(
                    key="id",
                    value=db_data.id
               )
               return response
            else: 
               messages.error( req, "Incorrect Email or password. Please try again." ) 
               return render( req, "login.html" )
    return render(req,"login.html")










def register_page(req):
    if req.method=="POST":
        input_data=req.POST.copy()
        if register_tb.objects.filter(email=input_data["email"]).exists() or register_tb.objects.filter(phoneNumber=input_data["phoneNumber"]).exists():
            messages.error(req,"user already exists")
            return render(req,"register.html",{"input_data":input_data})
        else:
            if input_data["password"]==input_data["confirmpassword"]:
                data=register_tb_serializer(data=input_data)
                if data.is_valid():
                    data.save()
                    return redirect("login")
                else:
                    for field, errors in data.errors.items():
                         for error in errors:
                              messages.error(req, str(error))

                    return render(req, "register.html", {"input_data": input_data})   
            else:
                messages.error(req,"passwords should match")
                return render(req,"register.html",{"input_data":input_data})

    return render(req,"register.html")








def dashboard_page(req):
    login_status=req.COOKIES.get("login")
    user=req.COOKIES.get("username")
    User_id=req.COOKIES.get("id")
    if login_status:
        total_courses=Course.objects.count()
        enrolled_courses=Enrolled_courses_model.objects.filter(user_id__id=User_id)
        enrolled_courses_count=enrolled_courses.count()
        course_completion=0
        for enrolled in enrolled_courses:
             if enrolled.course_id.is_setup_complete:
                  modules=created_modules_model.objects.filter(course_id=enrolled.course_id.id)
                  module_quiz_ids=[i.quiz_id for i in modules]
                  completed_modules=completed_quiz_model.objects.filter(user_id=User_id)
                  completed_quiz_ids=[i.quiz_id for i in completed_modules]
                  completion=True
                  for id in module_quiz_ids:
                       if id not in completed_quiz_ids:
                            completion=False
                            break
                  if completion:
                       course_completion+=1
                  

        return render(req,"dashboard.html",{"User":user,
                                            "total_courses":total_courses,
                                            "enrolled_courses":enrolled_courses_count,
                                            "completed_courses":course_completion})
    else:
        messages.error(req,"login first")
        return redirect("login")





def logout_page(req):
    response=redirect("login")
    response.delete_cookie("login")
    response.delete_cookie("username")
    response.delete_cookie("id")
    return response


def instructor_dashboard_page(req):

    login_status = req.COOKIES.get("login")
    user = req.COOKIES.get("username")
    user_id = req.COOKIES.get("id")

    if login_status:

        # Total courses created by this instructor
        total_courses = Course.objects.filter(
            instructor_id=user_id
        ).count()

        # Total assignments created by this instructor
        total_assignments = Assignment_details.objects.filter(
            instructer_id=user_id
        ).count()

        # Courses created by this instructor
        instructor_courses = Course.objects.filter(
            instructor_id=user_id
        )

        # Unique students enrolled in instructor's courses
        total_students = Enrolled_courses_model.objects.filter(
            course_id__in=instructor_courses
        ).values("user_id").distinct().count()

        return render(
            req,
            "instructor_dashboard.html",
            {
                "user": user,
                "total_courses": total_courses,
                "total_students": total_students,
                "total_assignments": total_assignments
            }
        )

    else:
        messages.error(req, "login first")
        return redirect("login")




def course_page(req):
         login_status=req.COOKIES.get("login")
         user_id=req.COOKIES.get("id")
         if login_status:
                if req.method=="POST":
                     course_data=req.POST.copy()
                     course_data["instructor"]=user_id
                     if Course.objects.filter(title=course_data["title"],instructor=user_id):
                          messages.error(req,"course already exist")
                          return redirect("course")
                     else:
                          course_obj=Course_serializer(data=course_data)
                          if course_obj.is_valid():
                               course_obj.save()
                               return redirect('my_courses')
                         

                          

                return render(req,"course.html")
         else:
                messages.error(req,"login first")
                return redirect("login")


def edit_course_page(req,course_id):

    login_status = req.COOKIES.get("login")
    user_id = req.COOKIES.get("id")

    if not login_status:
        return redirect("login")

    try:
        course = Course.objects.get(
            id=course_id,
            instructor_id=user_id
        )
    except Course.DoesNotExist:
        messages.error(req, "Course not found.")
        return redirect("my_courses")

    if req.method == "POST":

        data = {
            "title": req.POST.get("title"),
            "description": req.POST.get("description")
        }

        serializer = Course_serializer(
            course,
            data=data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            messages.success(
                req,
                "Course updated successfully."
            )

            return redirect("my_courses")

        else:

            return render(
                req,
                "edit_course.html",
                {
                    "course": course,
                    "errors": serializer.errors
                }
            )

    return render(
        req,
        "edit_course.html",
        {
            "course": course
        }
    )





def my_courses_page(req):
     login_status=req.COOKIES.get("login")
     user_id=req.COOKIES.get("id")
     if login_status:
          instructor_courses=Course.objects.filter(instructor=user_id)
          return render(req,"my_courses.html",{"courses":instructor_courses})
     else:
          messages.error(req,"login first")
          return redirect("login")




     
     
def assignment_page(req):
      login_status=req.COOKIES.get("login")
      user_id=req.COOKIES.get("id")
      if login_status:
           created_assignments=Assignment_details.objects.filter(instructer_id=user_id)
           return render(req,"assignment.html",{"assignments":created_assignments})    
      else:
                 messages.error(req,"login first")
                 return redirect("login")
      



def create_assignment_page(req):
      login_status=req.COOKIES.get("login")
      user_id=req.COOKIES.get("id")
      if login_status:
                if req.method=="POST":
                     course_input_data=req.POST.copy()
                     course_input_data["instructer_id"]=user_id
                     assignment_obj=create_assignment_serializer(data=course_input_data)
                   
                     if assignment_obj.is_valid():
                          assignment=assignment_obj.save()
                          created_assignments=Assignment_details.objects.filter(instructer_id=user_id)
                          return render(req,"assignment.html",{"assignments":created_assignments})

                else:  
                       created_courses=Course.objects.filter(instructor=user_id)   
                       created_assignments=Assignment_details.objects.filter(instructer_id=user_id)
                       return render(req,"create_assignment.html",{"courses":created_courses})
      else:
           messages.error(req,"login first")
           return redirect("login")


def view_assignment_page(req, assignment_id):

    login_status = req.COOKIES.get("login")
    user_id = req.COOKIES.get("id")

    if not login_status:
        return redirect("login")

    try:
        assignment = Assignment_details.objects.get(
            id=assignment_id,
            instructer_id=user_id
        )
    except Assignment_details.DoesNotExist:
        messages.error(req, "Assignment not found.")
        return redirect("assignment")

    return render(
        req,
        "view_assignment.html",
        {
            "assignment": assignment
        }
    )

def edit_assignment_page(req, assignment_id):

    login_status = req.COOKIES.get("login")
    user_id = req.COOKIES.get("id")

    if not login_status:
        return redirect("login")

    try:
        assignment = Assignment_details.objects.get(
            id=assignment_id,
            instructer_id=user_id
        )
    except Assignment_details.DoesNotExist:
        messages.error(req, "Assignment not found.")
        return redirect("assignment")

    if req.method == "POST":

        assignment.title = req.POST.get("title")
        assignment.description = req.POST.get("description")

        assignment.save()

        messages.success(
            req,
            "Assignment updated successfully."
        )

        return redirect("assignment")

    return render(
        req,
        "edit_assignment.html",
        {
            "assignment": assignment
        }
    )


def delete_assignment_page(req, assignment_id):

    login_status = req.COOKIES.get("login")
    user_id = req.COOKIES.get("id")

    if not login_status:
        return redirect("login")

    try:
        assignment = Assignment_details.objects.get(
            id=assignment_id,
            instructer_id=user_id
        )
    except Assignment_details.DoesNotExist:
        messages.error(req, "Assignment not found.")
        return redirect("assignment")

    if req.method == "POST":

        assignment.delete()

        messages.success(
            req,
            "Assignment deleted successfully."
        )

        return redirect("assignment")

    return render(
        req,
        "delete_assignment.html",
        {
            "assignment": assignment
        }
    )




def quiz_page(req):
     login_status=req.COOKIES.get("login")
     user_id=req.COOKIES.get("id")
     if login_status:
          created_quiz=Quiz_model.objects.filter(instructer_id=user_id)
          return render(req,"quiz.html",{"quizzes":created_quiz})
     else:
          messages.error(req,"login first")
          return redirect("login")
          
          
def view_quiz_page(req, quiz_id):

    login_status = req.COOKIES.get("login")
    user_id = req.COOKIES.get("id")

    if not login_status:
        return redirect("login")

    try:
        quiz = Quiz_model.objects.get(
            id=quiz_id,
            instructer_id=user_id
        )
    except Quiz_model.DoesNotExist:
        messages.error(req, "Quiz not found.")
        return redirect("quizzes")

    questions = questions_model.objects.filter(
        quiz_id=quiz
    )

    return render(
        req,
        "view_quiz.html",
        {
            "quiz": quiz,
            "questions": questions
        }
    )


def edit_quiz_page(req, quiz_id):

    login_status = req.COOKIES.get("login")
    user_id = req.COOKIES.get("id")

    if not login_status:
        return redirect("login")

    try:
        quiz = Quiz_model.objects.get(
            id=quiz_id,
            instructer_id=user_id
        )
    except Quiz_model.DoesNotExist:
        messages.error(req, "Quiz not found.")
        return redirect("quizzes")

    questions = questions_model.objects.filter(
        quiz_id=quiz
    ).order_by("id")

    if req.method == "POST":

        # Update quiz title
        quiz_title = req.POST.get("q_title")

        quiz.q_title = quiz_title
        quiz.save()

        # Update questions
        for question in questions:

            question.question = req.POST.get(
                f"question_{question.id}"
            )

            question.option1 = req.POST.get(
                f"option1_{question.id}"
            )

            question.option2 = req.POST.get(
                f"option2_{question.id}"
            )

            question.option3 = req.POST.get(
                f"option3_{question.id}"
            )

            question.option4 = req.POST.get(
                f"option4_{question.id}"
            )

            question.answer = req.POST.get(
                f"answer_{question.id}"
            )

            question.save()

        messages.success(
            req,
            "Quiz updated successfully."
        )

        return redirect("quiz")

    return render(
        req,
        "edit_quiz.html",
        {
            "quiz": quiz,
            "questions": questions
        }
    )   
     

def delete_quiz_page(req, quiz_id):

    login_status = req.COOKIES.get("login")
    user_id = req.COOKIES.get("id")

    if not login_status:
        return redirect("login")

    try:
        quiz = Quiz_model.objects.get(
            id=quiz_id,
            instructer_id=user_id
        )
    except Quiz_model.DoesNotExist:
        messages.error(req, "Quiz not found.")
        return redirect("quiz")

    # Check whether the quiz is used in any module
    module_exists = created_modules_model.objects.filter(
        quiz_id=quiz.id
    ).exists()

    if module_exists:

        messages.error(
            req,
            "This quiz cannot be deleted because it is already assigned to a module."
        )

        return redirect("quiz")

    # Show confirmation page
    if req.method == "POST":

        quiz.delete()

        messages.success(
            req,
            "Quiz deleted successfully."
        )

        return redirect("quiz")

    return render(
        req,
        "delete_quiz.html",
        {
            "quiz": quiz
        }
    )


def create_quiz_page(req):
      login_status=req.COOKIES.get("login")
      user_id=req.COOKIES.get("id")
      if login_status:
           if req.method=="POST":
                quiz_data=req.POST.copy()
                quiz_data["instructer_id"]=user_id
                quiz_obj=Quiz_serializer(data=quiz_data)
                if quiz_obj.is_valid():
                     saved_quiz=quiz_obj.save()
                     return redirect("questions",saved_quiz.id)
           else:
                 created_courses=Course.objects.filter(instructor=user_id)
                 return render(req,"create_quiz.html",{"courses":created_courses})   

      else:
                messages.error(req,"login first")
                return redirect("login")    
     


def questions_page(req,quiz_id):
     login_status=req.COOKIES.get("login")
     user_id=req.COOKIES.get("id")
     quiz=Quiz_model.objects.get(id=quiz_id)
     if login_status:
          if req.method=="POST":
               for i in range(1, quiz.total_questions + 1):

                        question_data = {}

                        question_data["quiz_id"] = quiz.id
                        question_data["question"] = req.POST.get(f"question{i}")
                        question_data["option1"] = req.POST.get(f"option1_{i}")
                        question_data["option2"] = req.POST.get(f"option2_{i}")
                        question_data["option3"] = req.POST.get(f"option3_{i}")
                        question_data["option4"] = req.POST.get(f"option4_{i}")
                        question_data["answer"] = req.POST.get(f"correct_answer{i}")
                       

                        question_obj = Question_serializer(data=question_data)

                        if question_obj.is_valid():
                            question_obj.save()
                        else:
                            print(question_obj.errors)
               return redirect("quiz")
          else:    
            num_of_questions=list(range(1,quiz.total_questions+1))
            return render(req,"questions.html",{"num_of_qns":num_of_questions})
     else:
        messages.error(req,"login first")
        return redirect("login")   



def instructor_profile_page(req):
       login_status=req.COOKIES.get("login")
       user_id=req.COOKIES.get("id")
       if login_status:
          instructor_detail=register_tb.objects.get(id=user_id)
          return render(req,"instructor_profile.html",{"instructor":instructor_detail})
       messages.error(req,"login first")
       return redirect("login") 


def edit_instructor_profile_page(req):

    login_status = req.COOKIES.get("login")
    user_id = req.COOKIES.get("id")

    if login_status:

        instructor = register_tb.objects.get(id=user_id)

        if req.method == "POST":

            input_data = req.POST.copy()

            data = register_tb_serializer(
                instructor,
                data=input_data,
                partial=True
            )

            if data.is_valid():
                data.save()

                messages.success(
                    req,
                    "Profile updated successfully."
                )

                return redirect("instructor_profile")

            else:

                for field, errors in data.errors.items():
                    for error in errors:
                        messages.error(req, str(error))

                return render(
                    req,
                    "edit_instructor_profile.html",
                    {
                        "instructor": instructor,
                        "input_data": input_data
                    }
                )

        return render(
            req,
            "edit_instructor_profile.html",
            {"instructor": instructor}
        )

    messages.error(req, "Login first")
    return redirect("login")



def available_courses_page(req):
     login_status=req.COOKIES.get("login")
     user_id=req.COOKIES.get("id")
     if login_status:
          courses=Course.objects.all()
          enrolled_courses=Enrolled_courses_model.objects.filter(user_id=user_id )
          enrolled_courses_ids=[enrolled_course.course_id.id for enrolled_course in enrolled_courses ]
          print(enrolled_courses_ids)
          return render(req,"available_courses.html",{"courses":courses,
                                                      "enrolled_courses":enrolled_courses_ids})
     messages.error(req,"login first")
     return redirect("login")



def enrolled_button(req,course_id):
     login_status=req.COOKIES.get("login")
     user_id=req.COOKIES.get("id")
     if login_status:
          input_data={
               "user_id":user_id,
               "course_id":course_id
          }
          obj=enrolled_courses_serializer(data=input_data)
          if obj.is_valid():
               obj.save()
          return redirect("enrolled_courses")
     
     messages.error(req,"login first")
     return redirect("login")






def enrolled_courses_page(req):
      login_status=req.COOKIES.get("login")
      User_id=req.COOKIES.get("id")
      if login_status:
         courses=Enrolled_courses_model.objects.filter(user_id=User_id)
         return render(req,"enrolled_courses.html",{"courses":courses})
         
          
           
           

      return render(req,"enrolled_courses.html")





def assignment_display_student_page(req):
      login_status=req.COOKIES.get("login")
      User_id=req.COOKIES.get("id")
      if login_status:
           submitted_assignments=submitted_assignments_model.objects.filter(user_id=User_id)
           submitted_assignment_ids=[assignment.assignment_id.id for assignment in submitted_assignments]
           enrolled_courses=Enrolled_courses_model.objects.filter(user_id=User_id )
           enrolled_courses_ids=[enrolled_course.course_id.id for enrolled_course in enrolled_courses ]
           created_assignments = Assignment_details.objects.filter(
            course_id__in=enrolled_courses_ids
        )

           return render(req,"assignment_display_student.html",{"assignments":created_assignments,
                                                                "submitted_assignment_ids":submitted_assignment_ids})






def submit_assignment_page(req,assignment_id):
     login_status=req.COOKIES.get("login")
     User_id=req.COOKIES.get("id")
     assignment_details=Assignment_details.objects.get(id=assignment_id)
     if login_status:
          if req.method=="POST":
               data_exists=submitted_assignments_model.objects.filter(user_id=User_id,assignment_id=assignment_id).first()
               if not data_exists:
                    input_data={
                                        "user_id":User_id,
                                        "assignment_id":assignment_id
                                   }
                    submitted_file=req.FILES.get("submitted_file")
                    url=cloudinary.uploader.upload(submitted_file,resource_type="raw")
                    input_data["submitted_file_url"]=url["secure_url"]
                    obj=submitted_assignments_serializer(data=input_data)
                    if obj.is_valid():
                        obj.save()
                        return redirect("assignment_display_student")
               else:
                    submitted_file=req.FILES.get("submitted_file")
                    url=cloudinary.uploader.upload(submitted_file,resource_type="raw")
                    input_data={"submitted_file_url":url["secure_url"]}
                    obj=submitted_assignments_serializer(instance=data_exists,data=input_data,partial=True) 
                    if obj.is_valid():
                        obj.save()
                        return redirect("assignment_display_student")            
          return render(req,"submit_assignment.html",{"assignment":assignment_details})
     messages.error(req,"login first")
     return redirect("login")



def quiz_display_student_page(req):
      login_status=req.COOKIES.get("login")
      User_id=req.COOKIES.get("id")
      if login_status:
           enrolled_courses=Enrolled_courses_model.objects.filter(user_id=User_id)
           enrolled_courses_list=[enrolled.course_id.id for enrolled in enrolled_courses]
           quizzes=Quiz_model.objects.filter(course__id__in= enrolled_courses_list)
           return render(req,"quiz_display_student.html",{"quizzes":quizzes})
      messages.error(req,"login first")
      return redirect("login")

def take_quiz_page(req,Quiz_id):
           
           login_status=req.COOKIES.get("login")
           User_id=req.COOKIES.get("id")

           if login_status:
               questions=questions_model.objects.filter(quiz_id__id=Quiz_id)


               if req.method=="POST":
                    count=0
                    score=0
                    for question in questions:
                         count+=1
                         student_answer=req.POST.get(f"question_{question.id}")
                         print(student_answer)
                         print(question.answer)
                         if student_answer==question.answer:
                              score+=1
                    input_data={
                         "quiz_id":Quiz_id,
                         "score":score,
                         "user_id":User_id

                    }
                    obj=complete_quiz_serializer(data=input_data)
                    if obj.is_valid():
                         obj.save()
                         return render(req,"result.html",
                                {
                                 "questions": questions,
                                 "score": score,
                                 "total_questions":count,
                                 "quiz_submitted": True})
                    else:
                         return render(req,"result.html",{"errors":obj.errors})


               return render(req,"take_quiz.html",{"questions":questions})
           messages.error(req,"login first")
           return redirect("login")

def add_module_page(req,course_id):
     login_status=req.COOKIES.get("login")
     User_id=req.COOKIES.get("id")
     if login_status:
          available_modules=created_modules_model.objects.filter(instructor_id=User_id,course_id=course_id)
          course=Course.objects.get(id=course_id)
          return render(req,"add_module.html",{"course":course,
                                               "modules":available_modules})

def create_module_form_page(req,course_id):
      
                login_status=req.COOKIES.get("login")
                User_id=req.COOKIES.get("id")
                if login_status:
                     if req.method=="POST":
                          input_data=req.POST.copy()
                          module_pdf=req.FILES.get("pdf_url")
                          url_pdf=cloudinary.uploader.upload(module_pdf,resource_type="raw",folder="instructor_modules_pdf")
                          input_data["pdf_url"]=url_pdf["secure_url"]
                          input_data["instructor_id"]=User_id
                          input_data["course_id"]=course_id
                          obj=created_modules_serializer(data=input_data)
                          if obj.is_valid():
                               obj.save()
                               return redirect("my_courses")
                          else:
                              return render(
                                   req,
                                   "create_module_form.html",
                                   {"errors": obj.errors}
                              )      
                               

                          
                     else:
                          
                          quiz_details=Quiz_model.objects.filter(instructer_id__id=User_id)
                          return render(req,"create_module_form.html",{"quizzes":quiz_details})
                else:  
                     messages.error(req,"login first")
                     return redirect("login")    



def finish_course_setup_page(req,course_id):
     login_status=req.COOKIES.get("login")
     User_id=req.COOKIES.get("id")
     if login_status:
          input_data=Course.objects.get(id=course_id)
          obj=Course_serializer(input_data,data={"is_setup_complete":True},partial=True)
          if obj.is_valid():
               obj.save()
               return redirect("my_courses")
          else:
               return render( req,"create_module_form.html",{"errors": obj.errors})
     else:
          messages.error(req,"login first")
          return redirect("login")  

def module_view_student_page(req,course_id):
     login_status=req.COOKIES.get("login")
     User_id=req.COOKIES.get("id")
     if login_status:
          modules=created_modules_model.objects.filter(course_id=course_id)
          completed_quizes=completed_quiz_model.objects.filter(user_id=User_id)
          quiz_ids=[quiz.quiz_id for quiz in completed_quizes]
          return render(req,"module_view_student.html",{"modules":modules,
                                                        "quizes":quiz_ids})
     else:
          messages.error(req,"login first")
          return redirect("login")  

     
def student_profile_page(req):
     login_status=req.COOKIES.get("login")
     User_id=req.COOKIES.get("id")
     if login_status:
          user_details=register_tb.objects.get(id=User_id)
          return render(req,"student_profile.html",{"student":user_details})
     else:
          messages.error(req,"login first")
          return redirect("login")

     
def edit_student_profile_page(req):
     login_status=req.COOKIES.get("login")
     User_id=req.COOKIES.get("id")
     if login_status:   
          user_details=register_tb.objects.get(id=User_id)
          if req.method=="POST":
               input_data=req.POST.copy()
               obj=register_tb_serializer(user_details,data=input_data,partial=True)
               if obj.is_valid():
                    obj.save()
                    return redirect("student_profile")
               else:
                    return render(req,"edit_student_profile.html",{"error":obj.errors,
                                                                   "user_details":user_details})
          else:          
              return render(req,"edit_student_profile.html",{"user_details":user_details})



def certificates_page(req):

    login_status = req.COOKIES.get("login")
    User_id = req.COOKIES.get("id")
    user=req.COOKIES.get("username")

    if login_status:

        enrolled_courses = Enrolled_courses_model.objects.filter(
            user_id__id=User_id
        )

        completed_course_names = []
        course_ids=[]

        for enrolled in enrolled_courses:

            course = enrolled.course_id

            # Course setup completed by instructor
            if course.is_setup_complete:

                modules = created_modules_model.objects.filter(
                    course_id=course.id
                )

                module_quiz_ids = [
                    module.quiz_id
                    for module in modules
                ]

                completed_modules = completed_quiz_model.objects.filter(
                    user_id=User_id
                )

                completed_quiz_ids = [
                    quiz.quiz_id
                    for quiz in completed_modules
                ]

                completion = True

                for quiz_id in module_quiz_ids:

                    if quiz_id not in completed_quiz_ids:
                        completion = False
                        break

                if completion:
                    completed_course_names.append(course.title)

        return render(req, "student_certificate.html", {
            "completed_courses": completed_course_names,
            "user":user

        })

    else:
        return redirect("login")  

def download_certificate_page(req,course_title):
          login_status = req.COOKIES.get("login")
          User_id = req.COOKIES.get("id")
          user=req.COOKIES.get("username")
          if login_status:
               html=render_to_string("download_certificate.html",{"user":user,
                                                                  "course":course_title})
               obj=HTML(string=html, base_url=req.build_absolute_uri("/"))
               pdf=obj.write_pdf()
               response=HttpResponse(pdf,content_type="application/pdf")
               return response
          else:
               return redirect("login")

def forget_password_page(req):
     if req.method=="POST":
          data=req.POST.copy()
          user_email=data["email"]
          user_obj=register_tb.objects.get(email=user_email)
          if user_obj:
               token=secrets.token_urlsafe(32)
               PasswordResetToken.objects.create(
                    user=user_obj,
                    token=token,
                    expiry=timezone.now()+timedelta(minutes=15)
               )
               reset_url=f"http://127.0.0.1:8000/reset_password/{token}/"

               html_msg=render_to_string("email_html.html",{"user_name":user_obj.username,
                                                            "reset_url":reset_url})
               send_mail(
                    subject="reset password",
                    message="this mail is for resetting your password",
                    from_email="srikalabondugula08@gmail.com",
                    recipient_list=[user_email],
                    fail_silently=True,
                    html_message=html_msg
               )
               messages.success(
                    req,
                    "Password reset link has been sent to your email. Please check your inbox."
                    )
               return render(req, "forget_password.html")
     else:
          return render(req,"forget_password.html")
def reset_password_page(req,token):
     print("TOKEN FROM URL:", token)

     reset_token = PasswordResetToken.objects.filter(
         token=token
    ).first()

     print("RESET TOKEN FROM DB:", reset_token)
     reset_token=PasswordResetToken.objects.filter(token=token).first()
     if not reset_token:
          return render(req,"forget_password.html",{"error":"Invalid Reset Link please try again"})
     elif reset_token.expiry<timezone.now():
          return render(req,"reset_password.html",{"error":"Reset Link has expired"})
     else:
       if req.method=="POST":
            input_data=req.POST.copy()
            new_password=input_data["password"]
            user=reset_token.user
            if input_data["password"] == input_data["confirm_password"]:

               data = register_tb_serializer(
                    user,
                    data={"password": input_data["password"]},
                    partial=True
               )

               if data.is_valid():
                    data.save()
                    reset_token.delete()
                    return redirect("login")

               else:
                    
                         for field, errors in data.errors.items():
                              for error in errors:
                                   messages.error(req, str(error))

                         return render(
                              req,
                              "reset_password.html",
                              {"input_data": input_data}
                         )
            else:
                    messages.error(req,"passwords should match")
                    return render(req,"reset_password.html",{"input_data":input_data})
       else:
            return render(req,"reset_password.html")

