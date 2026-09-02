from rest_framework import serializers
from . password import hash_password,check_password
import re
from .models import register_tb,Course,Assignment_details,Quiz_model,questions_model,Enrolled_courses_model,submitted_assignments_model,created_modules_model,completed_quiz_model
class register_tb_serializer(serializers.ModelSerializer):
    class Meta:
        model=register_tb
        fields="__all__"
    def validate_email(self, value):
        query = register_tb.objects.filter(email=value)

        if self.instance:
            query = query.exclude(id=self.instance.id)

        if query.exists():
            raise serializers.ValidationError(
                "This email is already registered."
            )

        return value
    def validate_phoneNumber(self, value):
          if not value.isdigit():
             raise serializers.ValidationError(
            "Mobile number should contain only digits."
        )

          if len(value) != 10:
                  raise serializers.ValidationError(
            "Mobile number must be exactly 10 digits."
        )

        
          query = register_tb.objects.filter(phoneNumber=value)

          if self.instance:
                query = query.exclude(id=self.instance.id)

          if query.exists():
                raise serializers.ValidationError(
                    "This mobile number is already registered."
                )

          return value
    def validate_password(self, value):

        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters."
            )

        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )

        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )

        if not re.search(r"[0-9]", value):
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )

        if not re.search(r"[^A-Za-z0-9]", value):
            raise serializers.ValidationError(
                "Password must contain at least one special character."
            )

        return value

    def create(self, validated_data):
        validated_data["password"] = hash_password(
            validated_data["password"]
        )

        return register_tb.objects.create(**validated_data)


class Course_serializer(serializers.ModelSerializer):
    class Meta:
        model=Course
        fields="__all__"

class create_assignment_serializer(serializers.ModelSerializer):
    class Meta:
        model=Assignment_details
        fields="__all__"


class Quiz_serializer(serializers.ModelSerializer):
    class Meta:
        model=Quiz_model
        fields="__all__"


class Question_serializer(serializers.ModelSerializer):
  class Meta:
    model=questions_model
    fields="__all__"

class enrolled_courses_serializer(serializers.ModelSerializer):
    class Meta:
        model=Enrolled_courses_model
        fields="__all__"

class created_modules_serializer(serializers.ModelSerializer):
    class Meta:
        model=created_modules_model
        fields="__all__"




class submitted_assignments_serializer(serializers.ModelSerializer):
    class Meta:
        model=submitted_assignments_model
        fields="__all__"


class complete_quiz_serializer(serializers.ModelSerializer):
    class Meta:
        model=completed_quiz_model
        fields="__all__"


