from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.http import HttpResponse,JsonResponse
# Create your views here.
def home(req):
    return render(req,'home.html')
def courses(req):
    return render(req,"courses.html")
def about_us(req):
    return render(req,"about_us.html")
def contact(req):

    if req.method == "POST":

        name = req.POST.get("name")
        email = req.POST.get("email")
        subject = req.POST.get("subject")
        message = req.POST.get("message")

        email_message = f"""
                Name: {name}

                Email: {email}

                Subject: {subject}

                Message:

                {message}
                """

        send_mail(
            subject=f"LearnHub Contact: {subject}",
            message=email_message,
            from_email="srikalabondugula08@gmail.com",
            recipient_list=["srikalabondugula08@gmail.com"],
            fail_silently=True
        )


        return redirect("contact")

    return render(req, "contact.html")

