from django.contrib import admin
from .models import (
    RecruitmentQuestion,
    CandidateProfile,
    CandidateResponse,
    TrainingProgram,
    TrainingEnrollment,
    PerformanceReview,
    Feedback360,
)


admin.site.register(RecruitmentQuestion)
admin.site.register(CandidateProfile)
admin.site.register(CandidateResponse)
admin.site.register(TrainingProgram)
admin.site.register(TrainingEnrollment)
admin.site.register(PerformanceReview)
admin.site.register(Feedback360)
