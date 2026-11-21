# Coursera grading fixes applied

Updated files:
- `onlinecourse/models.py`: added readable `__str__()` methods to `Choice` and `Submission`; added `Question.question_text` display alias; made `Question.is_get_score()` require an exact match of selected and correct choices.
- `onlinecourse/admin.py`: `QuestionAdmin.list_display` now uses `question_text`.
- `onlinecourse/views.py`: submission is saved from posted choices; scoring checks each question's complete correct-choice set; result view uses the submission and course belonging to the logged-in learner.
- `onlinecourse/urls.py`: added the required `show_exam_result` route name.
- `onlinecourse/templates/onlinecourse/course_details_bootstrap.html`: added the exact plural filename requested by the rubric, showing the course name and related lessons with Django template tags and Bootstrap. The original singular filename is retained as a compatibility copy.

Validation:
- Python syntax compilation passed for the four updated Python modules.
- Django runtime checks were not run because Django is not installed in this execution environment.
- Question 3's rubric was not included in the screenshots, so that criterion cannot yet be verified or implemented reliably.
