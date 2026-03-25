from django.db import migrations


def seed_recruitment_questions(apps, schema_editor):
    RecruitmentQuestion = apps.get_model('hr_management', 'RecruitmentQuestion')

    questions = [
        {
            'question': 'Can you walk us through a recent project and your specific contribution to its success?',
            'category': 'EXPERIENCE',
        },
        {
            'question': 'How do you prioritize tasks when you have multiple deadlines at the same time?',
            'category': 'BEHAVIORAL',
        },
        {
            'question': 'Describe a challenging problem you solved at work and the steps you took to solve it.',
            'category': 'TECHNICAL',
        },
        {
            'question': 'How do you handle feedback from managers or teammates, especially when it is critical?',
            'category': 'BEHAVIORAL',
        },
        {
            'question': 'What interests you most about this role, and how does it align with your career goals?',
            'category': 'GENERAL',
        },
    ]

    for item in questions:
        RecruitmentQuestion.objects.get_or_create(
            question=item['question'],
            defaults={
                'category': item['category'],
                'is_active': True,
                'created_by': None,
            },
        )


def unseed_recruitment_questions(apps, schema_editor):
    RecruitmentQuestion = apps.get_model('hr_management', 'RecruitmentQuestion')
    question_texts = [
        'Can you walk us through a recent project and your specific contribution to its success?',
        'How do you prioritize tasks when you have multiple deadlines at the same time?',
        'Describe a challenging problem you solved at work and the steps you took to solve it.',
        'How do you handle feedback from managers or teammates, especially when it is critical?',
        'What interests you most about this role, and how does it align with your career goals?',
    ]
    RecruitmentQuestion.objects.filter(question__in=question_texts).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('hr_management', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_recruitment_questions, unseed_recruitment_questions),
    ]
