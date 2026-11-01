from django.urls import path
from . import views


urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),

    path("dashboard/", views.dashboard_view, name="dashboard"),

    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard"
    ),

    path(
        "teacher-dashboard/",
        views.teacher_dashboard,
        name="teacher_dashboard"
    ),

    path(
        "student-dashboard/",
        views.student_dashboard,
        name="student_dashboard"
    ),
    path(
        "attendance/",
        views.attendance_view,
        name="attendance"
    ),
    path(
        "results/",
        views.results_view,
        name="results"
    ),
    path(
        "study-materials/",
        views.study_materials_view,
        name="study_materials"

    ),
    path("logout/", views.logout_view, name="logout"),
]