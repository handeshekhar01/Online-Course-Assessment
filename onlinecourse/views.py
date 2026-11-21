import logging

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic

from .models import Course, Enrollment, Question, Submission

logger = logging.getLogger(__name__)


@login_required
def submit(request, course_id):
    if request.method != "POST":
        return HttpResponseRedirect(reverse("onlinecourse:course_details", args=(course_id,)))

    course = get_object_or_404(Course, pk=course_id)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)

    selected_ids = extract_answers(request)
    # Only choices belonging to this course can be attached to the submission.
    from .models import Choice
    choices = Choice.objects.filter(
        id__in=selected_ids, question__course=course
    )
    submission.choices.set(choices)

    return HttpResponseRedirect(
        reverse("onlinecourse:show_exam_result", args=(course_id, submission.id))
    )


@login_required
def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(
        Submission, pk=submission_id, enrollment__course=course,
        enrollment__user=request.user
    )
    selected_choices = submission.choices.select_related("question").all()
    selected_ids_by_question = {}
    for choice in selected_choices:
        selected_ids_by_question.setdefault(choice.question_id, set()).add(choice.id)

    total_score = 0
    question_results = []
    for question in Question.objects.filter(course=course).prefetch_related("choice_set"):
        selected_ids = selected_ids_by_question.get(question.id, set())
        is_correct = question.is_get_score(selected_ids)
        if is_correct:
            total_score += question.grade
        question_results.append({
            "question": question,
            "selected_choices": question.choice_set.filter(id__in=selected_ids),
            "is_correct": is_correct,
            "grade": question.grade if is_correct else 0,
        })

    context = {
        "course": course,
        "submission": submission,
        "grade": total_score,
        "choices": selected_choices,
        "question_results": question_results,
    }
    return render(request, "onlinecourse/exam_result_bootstrap.html", context)


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)

    username = request.POST.get('username', '').strip()
    password = request.POST.get('psw', '')
    first_name = request.POST.get('firstname', '')
    last_name = request.POST.get('lastname', '')
    if User.objects.filter(username=username).exists():
        context['message'] = "User already exists."
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)

    user = User.objects.create_user(
        username=username, first_name=first_name, last_name=last_name,
        password=password
    )
    login(request, user)
    return redirect("onlinecourse:index")


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST.get('username', '')
        password = request.POST.get('psw', '')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        context['message'] = "Invalid username or password."
    return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    if not user.is_authenticated:
        return False
    return Enrollment.objects.filter(user=user, course=course).exists()


class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_details_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    if user.is_authenticated and not check_if_enrolled(user, course):
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save(update_fields=["total_enrollment"])
    return HttpResponseRedirect(reverse('onlinecourse:course_details', args=(course.id,)))


def extract_answers(request):
    selected_ids = []
    for key, value in request.POST.items():
        if key.startswith('choice'):
            try:
                selected_ids.append(int(value))
            except (TypeError, ValueError):
                continue
    return selected_ids
