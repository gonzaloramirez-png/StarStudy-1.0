"""Admin para courses: Course, CourseCode, TeacherCourse, StudentCourse."""
from django.contrib import admin
from .models import Course, CourseCode, TeacherCourse, StudentCourse


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'academic_year')
    search_fields = ('name', 'description')


@admin.register(CourseCode)
class CourseCodeAdmin(admin.ModelAdmin):
    list_display = ('course', 'code', 'status', 'current_uses', 'created_at')
    list_filter = ('status',)


@admin.register(TeacherCourse)
class TeacherCourseAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'course', 'role', 'assigned_at')
    list_filter = ('role',)


@admin.register(StudentCourse)
class StudentCourseAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'enrolled_at')
    list_filter = ('status',)
