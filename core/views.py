
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .models import UserProfile, Student, Attendance, Marks


ALLOWED_LOGIN_ROLES = {"ADMIN", "TEACHER", "STUDENT"}
REGISTRATION_ROLES = {"STUDENT", "TEACHER"}


# Registration form with email field
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


# Find the student record associated with the logged-in user.
def get_student_for_user(user):
    email = (user.email or "").strip()

    # First try to match the Django user's email.
    if email:
        student = Student.objects.filter(email__iexact=email).first()
        if student:
            return student

    # If email is empty or does not match, try username as email.
    student = Student.objects.filter(
        email__iexact=user.username
    ).first()

    if student:
        return student

    return None


# Login
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        selected_role = request.POST.get("role", "STUDENT").upper()

        if selected_role not in ALLOWED_LOGIN_ROLES:
            messages.error(request, "Please select a valid account type.")
            return redirect("login")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

        if not user.is_active:
            messages.error(request, "Your account is inactive.")
            return redirect("login")

        if user.is_superuser:
            UserProfile.objects.get_or_create(
                user=user,
                defaults={"role": "ADMIN"}
            )

        try:
            actual_role = user.profile.role
        except UserProfile.DoesNotExist:
            messages.error(
                request,
                "Your role is not configured. Contact the administrator."
            )
            return redirect("login")

        if actual_role != selected_role:
            messages.error(
                request,
                f"This account is registered as {actual_role}. "
                "Please select the correct account type."
            )
            return redirect("login")

        login(request, user)
        return redirect("dashboard")

    return render(request, "core/login.html")


# Registration
def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    selected_role = request.GET.get("role", "STUDENT").upper()

    if selected_role not in REGISTRATION_ROLES:
        selected_role = "STUDENT"

    if request.method == "POST":
        selected_role = request.POST.get("role", "STUDENT").upper()

        if selected_role not in REGISTRATION_ROLES:
            messages.error(
                request,
                "Admin registration is not available. "
                "Choose Student or Faculty."
            )
            selected_role = "STUDENT"
            form = CustomUserCreationForm()

        else:
            form = CustomUserCreationForm(request.POST)

            if form.is_valid():
                email = form.cleaned_data["email"].strip()

                # Prevent duplicate registration emails.
                if User.objects.filter(email__iexact=email).exists():
                    form.add_error(
                        "email",
                        "This email is already registered."
                    )
                else:
                    with transaction.atomic():
                        user = form.save(commit=False)
                        user.email = email
                        user.save()

                        UserProfile.objects.create(
                            user=user,
                            role=selected_role
                        )

                    messages.success(
                        request,
                        "Account created successfully! Please sign in."
                    )
                    return redirect("login")

    else:
        form = CustomUserCreationForm()

    return render(
        request,
        "core/register.html",
        {
            "form": form,
            "selected_role": selected_role,
        }
    )


# Dashboard redirect based on role
@login_required
def dashboard_view(request):
    if request.user.is_superuser:
        UserProfile.objects.get_or_create(
            user=request.user,
            defaults={"role": "ADMIN"}
        )

    try:
        role = request.user.profile.role
    except UserProfile.DoesNotExist:
        logout(request)
        messages.error(
            request,
            "Your account role is not configured. Contact the administrator."
        )
        return redirect("login")

    if role == "ADMIN":
        return redirect("admin_dashboard")

    if role == "TEACHER":
        return redirect("teacher_dashboard")

    if role == "STUDENT":
        return redirect("student_dashboard")

    logout(request)
    messages.error(request, "Invalid account role.")
    return redirect("login")


# Admin dashboard
@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        try:
            if request.user.profile.role != "ADMIN":
                return render(request, "core/403.html", status=403)
        except UserProfile.DoesNotExist:
            return render(request, "core/403.html", status=403)

    return render(
        request,
        "core/admin_dashboard.html",
        {
            "total_users": User.objects.count(),
            "total_teachers": UserProfile.objects.filter(
                role="TEACHER"
            ).count(),
            "total_students": UserProfile.objects.filter(
                role="STUDENT"
            ).count(),
        }
    )


# Teacher dashboard
@login_required
def teacher_dashboard(request):
    try:
        if request.user.profile.role != "TEACHER":
            return render(request, "core/403.html", status=403)
    except UserProfile.DoesNotExist:
        return render(request, "core/403.html", status=403)

    return render(request, "core/teacher_dashboard.html")


# Student dashboard
@login_required
def student_dashboard(request):
    try:
        if request.user.profile.role != "STUDENT":
            return render(request, "core/403.html", status=403)
    except UserProfile.DoesNotExist:
        return render(request, "core/403.html", status=403)

    return render(request, "core/student_dashboard.html")


# Attendance page
@login_required
def attendance_view(request):
    try:
        if request.user.profile.role != "STUDENT":
            return render(request, "core/403.html", status=403)
    except UserProfile.DoesNotExist:
        if not request.user.is_superuser:
            return render(request, "core/403.html", status=403)

    student = get_student_for_user(request.user)

    if student is None:
        messages.warning(
            request,
            "Your login account is not linked to a student record. "
            "Please contact the administrator."
        )
        records = Attendance.objects.none()
    else:
        records = Attendance.objects.filter(
            student=student
        ).select_related(
            "student", "course"
        ).order_by("-date")

    return render(
        request,
        "core/attendance.html",
        {"records": records}
    )


# Results page
@login_required
def results_view(request):
    try:
        if request.user.profile.role != "STUDENT":
            return render(request, "core/403.html", status=403)
    except UserProfile.DoesNotExist:
        if not request.user.is_superuser:
            return render(request, "core/403.html", status=403)

    student = get_student_for_user(request.user)

    if student is None:
        messages.warning(
            request,
            "Your login account is not linked to a student record. "
            "Please contact the administrator."
        )
        records = Marks.objects.none()
    else:
        records = Marks.objects.filter(
            student=student
        ).select_related(
            "student", "course"
        ).order_by("course__course_name")

    return render(
        request,
        "core/results.html",
        {"records": records}
    )


# Study materials page
@login_required
def study_materials_view(request):
    try:
        if request.user.profile.role != "STUDENT":
            return render(request, "core/403.html", status=403)
    except UserProfile.DoesNotExist:
        if not request.user.is_superuser:
            return render(request, "core/403.html", status=403)

    return render(request, "core/study_materials.html")


# Logout
@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You have been signed out.")
    return redirect("login")
