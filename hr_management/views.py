from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.views import IsHRPermission

from .models import (
    RecruitmentQuestion,
    CandidateProfile,
    CandidateResponse,
    TrainingProgram,
    TrainingEnrollment,
    TrainingApplication,
    PerformanceReview,
    Feedback360,
    PeerEvaluation,
)
from .serializers import (
    RecruitmentQuestionSerializer,
    CandidateProfileSerializer,
    CandidateResponseSerializer,
    TrainingProgramSerializer,
    TrainingEnrollmentSerializer,
    TrainingApplicationSerializer,
    TrainingApplicationHRSerializer,
    PerformanceReviewSerializer,
    Feedback360Serializer,
    PeerEvaluationSerializer,
)

User = get_user_model()


class RecruitmentQuestionListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsHRPermission]
    serializer_class = RecruitmentQuestionSerializer

    def get_queryset(self):
        return RecruitmentQuestion.objects.filter(is_active=True).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CandidateListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsHRPermission]
    serializer_class = CandidateProfileSerializer

    def get_queryset(self):
        queryset = CandidateProfile.objects.all().order_by('-created_at')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset


class CandidateDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsHRPermission]
    serializer_class = CandidateProfileSerializer
    queryset = CandidateProfile.objects.all()


class CandidateResponseListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsHRPermission]
    serializer_class = CandidateResponseSerializer

    def get_queryset(self):
        candidate_id = self.kwargs['candidate_id']
        return CandidateResponse.objects.filter(candidate_id=candidate_id).select_related('question', 'candidate')

    def perform_create(self, serializer):
        serializer.save(candidate_id=self.kwargs['candidate_id'])


class CandidateShortlistAPIView(APIView):
    permission_classes = [IsHRPermission]

    def post(self, request, candidate_id):
        try:
            candidate = CandidateProfile.objects.get(id=candidate_id)
        except CandidateProfile.DoesNotExist:
            return Response({'error': 'Candidate not found.'}, status=status.HTTP_404_NOT_FOUND)

        candidate.status = 'SHORTLISTED'
        candidate.save(update_fields=['status', 'updated_at'])
        return Response({'message': 'Candidate shortlisted successfully.'}, status=status.HTTP_200_OK)


class TrainingProgramListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsHRPermission]
    serializer_class = TrainingProgramSerializer
    queryset = TrainingProgram.objects.all().order_by('-start_date')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TrainingEnrollmentListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsHRPermission]
    serializer_class = TrainingEnrollmentSerializer

    def get_queryset(self):
        queryset = TrainingEnrollment.objects.select_related('training_program', 'employee').all()
        employee_id = self.request.query_params.get('employee')
        program_id = self.request.query_params.get('training_program')

        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if program_id:
            queryset = queryset.filter(training_program_id=program_id)

        return queryset.order_by('-created_at')


class TrainingEnrollmentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsHRPermission]
    serializer_class = TrainingEnrollmentSerializer
    queryset = TrainingEnrollment.objects.select_related('training_program', 'employee').all()


class PerformanceReviewListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsHRPermission]
    serializer_class = PerformanceReviewSerializer

    def get_queryset(self):
        queryset = PerformanceReview.objects.select_related('employee', 'reviewer').all().order_by('-created_at')
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)


class PerformanceReviewDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsHRPermission]
    serializer_class = PerformanceReviewSerializer
    queryset = PerformanceReview.objects.select_related('employee', 'reviewer').all()


class Feedback360ListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = Feedback360Serializer

    def get_queryset(self):
        queryset = Feedback360.objects.select_related(
            'performance_review', 'from_employee', 'to_employee'
        ).all().order_by('-created_at')

        review_id = self.request.query_params.get('performance_review')
        to_employee = self.request.query_params.get('to_employee')

        if review_id:
            queryset = queryset.filter(performance_review_id=review_id)
        if to_employee:
            queryset = queryset.filter(to_employee_id=to_employee)

        if self.request.user.is_hr:
            return queryset

        return queryset.filter(from_employee=self.request.user)

    def perform_create(self, serializer):
        serializer.save(from_employee=self.request.user)


@api_view(['GET'])
@permission_classes([IsHRPermission])
def feedback_360_summary(request, review_id):
    feedback_items = Feedback360.objects.filter(performance_review_id=review_id)

    if not feedback_items.exists():
        return Response(
            {'review_id': review_id, 'total_feedback': 0, 'average_rating': 0, 'by_relationship': []},
            status=status.HTTP_200_OK,
        )

    average_rating = feedback_items.aggregate(avg=Avg('rating'))['avg'] or 0
    relationship_summary = []

    for relationship_key, relationship_label in Feedback360.RELATIONSHIP_CHOICES:
        subset = feedback_items.filter(relationship=relationship_key)
        if subset.exists():
            relationship_summary.append({
                'relationship': relationship_label,
                'count': subset.count(),
                'average_rating': subset.aggregate(avg=Avg('rating'))['avg'] or 0,
            })

    return Response({
        'review_id': review_id,
        'total_feedback': feedback_items.count(),
        'average_rating': round(float(average_rating), 2),
        'by_relationship': relationship_summary,
    })


@api_view(['GET'])
@permission_classes([IsHRPermission])
def employee_performance_report(request):
    employee_id = request.query_params.get('employee_id')
    if not employee_id:
        return Response({'error': 'employee_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        employee = User.objects.get(id=employee_id)
    except User.DoesNotExist:
        return Response({'error': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)

    reviews = PerformanceReview.objects.filter(employee=employee).select_related('reviewer').order_by('-created_at')
    feedback_items = Feedback360.objects.filter(to_employee=employee).select_related('from_employee', 'performance_review')
    training_enrollments = TrainingEnrollment.objects.filter(employee=employee).select_related('training_program').order_by('-created_at')

    review_average = reviews.aggregate(avg=Avg('overall_rating'))['avg'] or 0
    feedback_average = feedback_items.aggregate(avg=Avg('rating'))['avg'] or 0
    latest_review = reviews.first()

    relationship_breakdown = []
    for relationship_key, relationship_label in Feedback360.RELATIONSHIP_CHOICES:
        subset = feedback_items.filter(relationship=relationship_key)
        if subset.exists():
            relationship_breakdown.append({
                'relationship': relationship_label,
                'count': subset.count(),
                'average_rating': round(float(subset.aggregate(avg=Avg('rating'))['avg'] or 0), 2),
            })

    recommendations = []
    if latest_review and latest_review.improvement_areas:
        recommendations.append(f"Focus on improvement areas highlighted in the latest review: {latest_review.improvement_areas}")
    if float(review_average or 0) < 3:
        recommendations.append('Schedule a coaching plan with monthly follow-ups to improve core performance areas.')
    if float(feedback_average or 0) < 3:
        recommendations.append('Use 360 feedback themes to create a targeted communication and collaboration development plan.')

    completed_trainings = training_enrollments.filter(status='COMPLETED').count()
    active_trainings = training_enrollments.exclude(status='COMPLETED').count()

    if not recommendations:
        recommendations.append('Maintain current performance level and set stretch goals for the next review period.')

    report = {
        'employee': {
            'id': employee.id,
            'full_name': employee.get_full_name() or employee.username,
            'email': employee.email,
            'department': employee.department,
            'employee_id': employee.employee_id,
        },
        'summary': {
            'total_reviews': reviews.count(),
            'average_review_rating': round(float(review_average or 0), 2),
            'total_360_feedback': feedback_items.count(),
            'average_360_rating': round(float(feedback_average or 0), 2),
            'completed_trainings': completed_trainings,
            'active_trainings': active_trainings,
        },
        'latest_review': PerformanceReviewSerializer(latest_review).data if latest_review else None,
        'review_history': PerformanceReviewSerializer(reviews, many=True).data,
        'feedback_breakdown': relationship_breakdown,
        'recent_feedback': Feedback360Serializer(feedback_items.order_by('-created_at')[:5], many=True).data,
        'training_overview': TrainingEnrollmentSerializer(training_enrollments, many=True).data,
        'recommendations': recommendations,
    }

    return Response(report)


# ─────────────────────────────────────────────────────────────────────────────
# Employee-facing views
# ─────────────────────────────────────────────────────────────────────────────

class AvailableTrainingProgramsView(generics.ListAPIView):
    """Authenticated employees can list all active training programs."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrainingProgramSerializer

    def get_queryset(self):
        return TrainingProgram.objects.filter(is_active=True).order_by('-start_date')


class TrainingApplicationListCreateView(generics.ListCreateAPIView):
    """Employee applies for a training program; lists their own applications."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrainingApplicationSerializer

    def get_queryset(self):
        return TrainingApplication.objects.filter(applicant=self.request.user).select_related('training_program')

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)


class TrainingApplicationDetailView(generics.RetrieveDestroyAPIView):
    """Employee can view or withdraw (delete) their own application."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrainingApplicationSerializer

    def get_queryset(self):
        return TrainingApplication.objects.filter(applicant=self.request.user)

    def destroy(self, request, *args, **kwargs):
        application = self.get_object()
        if application.status not in ('PENDING',):
            return Response(
                {'error': 'Only pending applications can be withdrawn.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        application.status = 'WITHDRAWN'
        application.save(update_fields=['status', 'updated_at'])
        return Response({'message': 'Application withdrawn.'}, status=status.HTTP_200_OK)


class HRTrainingApplicationListView(generics.ListAPIView):
    """HR can list all training applications, optionally filtered."""
    permission_classes = [IsHRPermission]
    serializer_class = TrainingApplicationHRSerializer

    def get_queryset(self):
        queryset = TrainingApplication.objects.select_related('training_program', 'applicant').all()
        program_id = self.request.query_params.get('training_program')
        status_filter = self.request.query_params.get('status')
        if program_id:
            queryset = queryset.filter(training_program_id=program_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by('-applied_at')


class HRTrainingApplicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """HR can approve/reject a training application."""
    permission_classes = [IsHRPermission]
    serializer_class = TrainingApplicationHRSerializer
    queryset = TrainingApplication.objects.select_related('training_program', 'applicant').all()

    def perform_update(self, serializer):
        previous_status = serializer.instance.status
        application = serializer.save()

        if application.status == 'APPROVED' and previous_status != 'APPROVED':
            TrainingEnrollment.objects.get_or_create(
                training_program=application.training_program,
                employee=application.applicant,
                defaults={
                    'status': 'ASSIGNED',
                    'completion_percentage': 0,
                    'notes': 'Created from approved training application.',
                },
            )


class MyTrainingEnrollmentsView(generics.ListAPIView):
    """Authenticated employee can list their own training enrollments."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrainingEnrollmentSerializer

    def get_queryset(self):
        return TrainingEnrollment.objects.filter(employee=self.request.user).select_related('training_program')


class MyTrainingEnrollmentDetailView(generics.RetrieveUpdateAPIView):
    """Employee can view and update their own enrollment progress."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TrainingEnrollmentSerializer

    def get_queryset(self):
        return TrainingEnrollment.objects.filter(employee=self.request.user)

    def update(self, request, *args, **kwargs):
        # Employees may only update completion_percentage and notes
        allowed = {'completion_percentage', 'notes', 'status'}
        data = {k: v for k, v in request.data.items() if k in allowed}
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ── Peer Evaluations ──────────────────────────────────────────────────────────

class PeerEvaluationListCreateView(generics.ListCreateAPIView):
    """Employees can submit and view peer evaluations."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PeerEvaluationSerializer

    def get_queryset(self):
        user = self.request.user
        direction = self.request.query_params.get('direction', 'given')
        if direction == 'received':
            return PeerEvaluation.objects.filter(evaluatee=user).select_related('evaluator', 'evaluatee')
        # HR can see all; employees see ones they gave
        if user.is_hr:
            return PeerEvaluation.objects.select_related('evaluator', 'evaluatee').all()
        return PeerEvaluation.objects.filter(evaluator=user).select_related('evaluator', 'evaluatee')

    def perform_create(self, serializer):
        serializer.save(evaluator=self.request.user)


class PeerEvaluationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Evaluator can view/edit/delete their own submitted peer evaluations."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PeerEvaluationSerializer

    def get_queryset(self):
        if self.request.user.is_hr:
            return PeerEvaluation.objects.all()
        return PeerEvaluation.objects.filter(evaluator=self.request.user)


# ── Employee's own performance report ────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_performance_report(request):
    """An employee can view their own performance report."""
    employee = request.user

    reviews = PerformanceReview.objects.filter(employee=employee, status='FINALIZED').select_related('reviewer').order_by('-created_at')
    feedback_items = Feedback360.objects.filter(to_employee=employee).select_related('from_employee', 'performance_review')
    training_enrollments = TrainingEnrollment.objects.filter(employee=employee).select_related('training_program').order_by('-created_at')
    peer_evaluations_received = PeerEvaluation.objects.filter(evaluatee=employee).select_related('evaluator')

    review_average = reviews.aggregate(avg=Avg('overall_rating'))['avg'] or 0
    feedback_average = feedback_items.aggregate(avg=Avg('rating'))['avg'] or 0
    peer_avg = (
        peer_evaluations_received.aggregate(
            comm=Avg('communication_rating'),
            team=Avg('teamwork_rating'),
            tech=Avg('technical_rating'),
            lead=Avg('leadership_rating'),
        )
    )

    completed_trainings = training_enrollments.filter(status='COMPLETED').count()
    active_trainings = training_enrollments.exclude(status='COMPLETED').count()

    latest_review = reviews.first()

    relationship_breakdown = []
    for rel_key, rel_label in Feedback360.RELATIONSHIP_CHOICES:
        subset = feedback_items.filter(relationship=rel_key)
        if subset.exists():
            relationship_breakdown.append({
                'relationship': rel_label,
                'count': subset.count(),
                'average_rating': round(float(subset.aggregate(avg=Avg('rating'))['avg'] or 0), 2),
            })

    recommendations = []
    if latest_review and latest_review.improvement_areas:
        recommendations.append(f"Focus on: {latest_review.improvement_areas}")
    if float(review_average) < 3:
        recommendations.append('Consider discussing a coaching plan with your manager.')
    if not recommendations:
        recommendations.append('Keep up the great work! Continue setting stretch goals.')

    report = {
        'employee': {
            'id': employee.id,
            'full_name': employee.get_full_name() or employee.username,
            'email': employee.email,
            'department': employee.department,
            'employee_id': employee.employee_id,
        },
        'summary': {
            'total_reviews': reviews.count(),
            'average_review_rating': round(float(review_average), 2),
            'total_360_feedback': feedback_items.count(),
            'average_360_rating': round(float(feedback_average), 2),
            'completed_trainings': completed_trainings,
            'active_trainings': active_trainings,
            'peer_evaluations_received': peer_evaluations_received.count(),
            'peer_avg_communication': round(float(peer_avg.get('comm') or 0), 2),
            'peer_avg_teamwork': round(float(peer_avg.get('team') or 0), 2),
            'peer_avg_technical': round(float(peer_avg.get('tech') or 0), 2),
            'peer_avg_leadership': round(float(peer_avg.get('lead') or 0), 2),
        },
        'latest_review': PerformanceReviewSerializer(latest_review).data if latest_review else None,
        'review_history': PerformanceReviewSerializer(reviews, many=True).data,
        'feedback_breakdown': relationship_breakdown,
        'recent_peer_evaluations': PeerEvaluationSerializer(
            peer_evaluations_received.order_by('-created_at')[:5], many=True
        ).data,
        'training_overview': TrainingEnrollmentSerializer(training_enrollments, many=True).data,
        'training_applications': TrainingApplicationSerializer(
            TrainingApplication.objects.filter(applicant=employee).select_related('training_program'), many=True
        ).data,
        'recommendations': recommendations,
    }

    return Response(report)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_employee_alerts(request):
    """Employee-facing alerts for newly published trainings and finalized reviews."""
    user = request.user

    if user.is_hr:
        return Response({'has_notifications': False, 'notifications': []})

    try:
        days = int(request.query_params.get('days', 45))
    except (TypeError, ValueError):
        days = 45

    days = min(max(days, 1), 120)
    since = timezone.now() - timedelta(days=days)

    notifications = []

    trainings = TrainingProgram.objects.filter(
        is_active=True,
        created_at__gte=since,
    ).order_by('-created_at')[:20]

    for training in trainings:
        notifications.append({
            'id': f"training-{training.id}",
            'type': 'TRAINING_NEW',
            'title': f"New Training: {training.title}",
            'message': (
                f"A new training program is now available from {training.start_date} to {training.end_date}."
            ),
            'created_at': training.created_at,
            'priority': 'MEDIUM',
        })

    finalized_reviews = PerformanceReview.objects.filter(
        employee=user,
        status='FINALIZED',
        created_at__gte=since,
    ).select_related('reviewer').order_by('-created_at')[:20]

    for review in finalized_reviews:
        reviewer_name = '-'
        if review.reviewer:
            reviewer_name = review.reviewer.get_full_name() or review.reviewer.username

        notifications.append({
            'id': f"review-{review.id}",
            'type': 'PERFORMANCE_REVIEWED',
            'title': f"Performance Review Finalized ({review.review_period})",
            'message': (
                f"Your review for {review.review_period} is finalized with rating {review.overall_rating}. "
                f"Reviewer: {reviewer_name}."
            ),
            'created_at': review.created_at,
            'priority': 'HIGH',
        })

    notifications.sort(key=lambda item: item['created_at'], reverse=True)

    return Response({
        'has_notifications': len(notifications) > 0,
        'notifications': notifications[:30],
    })

