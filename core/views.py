from .models import UserProfile
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is None:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

        if not user.is_active:
            messages.error(request, "Your account is inactive.")
            return redirect("login")

        try:
            role = user.profile.role
        except Exception:
            messages.error(
                request,
                "Your role is not configured. Contact the administrator."
            )
            return redirect("login")

        if role not in ("ADMIN", "TEACHER", "STUDENT"):
            messages.error(request, "Invalid account role.")
            return redirect("login")

        login(request, user)
        return redirect("dashboard")

    return render(request, "core/login.html")


@login_required
def dashboard_view(request):
    try:
        role = request.user.profile.role
    except Exception:
        logout(request)
        messages.error(request, "Your account role is not configured.")
        return redirect("login")

    if role == "ADMIN":
        return redirect("admin_dashboard")
    elif role == "TEACHER":
        return redirect("teacher_dashboard")
    elif role == "STUDENT":
        return redirect("student_dashboard")

    logout(request)
    return redirect("login")



@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        try:
            if request.user.profile.role != "ADMIN":
                return render(request, "core/403.html", status=403)
        except UserProfile.DoesNotExist:
            return render(request, "core/403.html", status=403)

    from django.contrib.auth.models import User
    

    return render(
        request,
        "core/admin_dashboard.html",
        {
            "total_users": User.objects.count(),
            "total_teachers": UserProfile.objects.filter(role="TEACHER").count(),
            "total_students": UserProfile.objects.filter(role="STUDENT").count(),
        },
    )
@login_required
def teacher_dashboard(request):
    try:
        if request.user.profile.role != "TEACHER":
            return render(request, "core/403.html", status=403)
    except Exception:
        return render(request, "core/403.html", status=403)

    return render(request, "core/teacher_dashboard.html")


@login_required
def student_dashboard(request):
    try:
        if request.user.profile.role != "STUDENT":
            return render(request, "core/403.html", status=403)
    except Exception:
        return render(request, "core/403.html", status=403)

    return render(request, "core/student_dashboard.html")


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")