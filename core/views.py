from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .models import UserProfile


ALLOWED_LOGIN_ROLES = {"ADMIN", "TEACHER", "STUDENT"}
REGISTRATION_ROLES = {"STUDENT", "TEACHER"}


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

        # Automatically configure an existing Django superuser as Admin.
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


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    selected_role = request.GET.get("role", "STUDENT").upper()

    if selected_role not in REGISTRATION_ROLES:
        selected_role = "STUDENT"

    if request.method == "POST":
        selected_role = request.POST.get("role", "STUDENT").upper()

        # Admin registration is not allowed from the public page.
        if selected_role not in REGISTRATION_ROLES:
            messages.error(
                request,
                "Admin registration is not available. "
                "Choose Student or Faculty."
            )
            selected_role = "STUDENT"
            form = UserCreationForm()
        else:
            form = UserCreationForm(request.POST)

            if form.is_valid():
                with transaction.atomic():
                    user = form.save()

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
        form = UserCreationForm()

    return render(
        request,
        "core/register.html",
        {
            "form": form,
            "selected_role": selected_role,
        }
    )


@login_required
def dashboard_view(request):
    # Ensure an existing Django superuser has an Admin profile.
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


@login_required
def admin_dashboard(request):
    # A Django superuser is allowed to access the Admin dashboard.
    if not request.user.is_superuser:
        try:
            if request.user.profile.role != "ADMIN":
                return render(
                    request,
                    "core/403.html",
                    status=403
                )
        except UserProfile.DoesNotExist:
            return render(
                request,
                "core/403.html",
                status=403
            )

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


@login_required
def teacher_dashboard(request):
    try:
        if request.user.profile.role != "TEACHER":
            return render(
                request,
                "core/403.html",
                status=403
            )
    except UserProfile.DoesNotExist:
        return render(
            request,
            "core/403.html",
            status=403
        )

    return render(request, "core/teacher_dashboard.html")


@login_required
def student_dashboard(request):
    try:
        if request.user.profile.role != "STUDENT":
            return render(
                request,
                "core/403.html",
                status=403
            )
    except UserProfile.DoesNotExist:
        return render(
            request,
            "core/403.html",
            status=403
        )

    return render(request, "core/student_dashboard.html")


@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You have been signed out.")
    return redirect("login")