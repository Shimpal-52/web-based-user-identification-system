
from django.db import models
from django.contrib.auth.models import User


# 1. User Profile
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("TEACHER", "Teacher"),
        ("STUDENT", "Student"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


# 2. Department
class Department(models.Model):
    department_id = models.AutoField(primary_key=True)
    department_name = models.CharField(max_length=100, unique=True)
    department_code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.department_name


# 3. Student
class Student(models.Model):
    student_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="students",
    )

    admission_date = models.DateField()

    def __str__(self):
        return f"{self.student_id} - {self.name}"


# 4. Faculty
class Faculty(models.Model):
    faculty_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="faculty_members",
    )

    designation = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# 5. Course
class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=100)
    course_code = models.CharField(max_length=15, unique=True)
    credits = models.PositiveSmallIntegerField()

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="courses",
    )

    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.PROTECT,
        related_name="courses",
    )

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"


# 6. Enrollment
class Enrollment(models.Model):
    enrollment_id = models.AutoField(primary_key=True)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )

    semester = models.PositiveSmallIntegerField()

    enrollment_date = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course", "semester"],
                name="unique_student_course_semester",
            ),
            models.CheckConstraint(
                condition=models.Q(semester__gte=1, semester__lte=12),
                name="valid_enrollment_semester",
            ),
        ]

    def __str__(self):
        return f"{self.student.name} - {self.course.course_name}"


# 7. Attendance
class Attendance(models.Model):
    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
    ]

    attendance_id = models.AutoField(primary_key=True)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    date = models.DateField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course", "date"],
                name="unique_student_course_attendance_date",
            ),
        ]

    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.status}"


# 8. Marks
class Marks(models.Model):
    marks_id = models.AutoField(primary_key=True)

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="marks_records",
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="marks_records",
    )

    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(marks_obtained__gte=0),
                name="marks_obtained_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(max_marks__gt=0),
                name="max_marks_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(marks_obtained__lte=models.F("max_marks")),
                name="marks_not_above_max",
            ),
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_student_course_marks",
            ),
        ]

    def __str__(self):
        return f"{self.student.name} - {self.marks_obtained}/{self.max_marks}"
