from django.urls import path,include
from . import views

urlpatterns = [
   path('',views.home,name="home"),
   path('courses/',views.courses,name="courses"),
   path('about_us/',views.about_us,name="about_us"),
   path('contact/',views.contact,name="contact")
]