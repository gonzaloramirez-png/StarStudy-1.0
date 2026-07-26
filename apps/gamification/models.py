"""Models de gamification: Tip System, Rewards, Badges, Quizzes, Rankings.

- TipTransaction: Registro de +XP manuales que da el profesor (Tip System).
- Reward: Tienda de recompensas académicas canjeables por XP.
- StudentReward: Canjes de recompensas por estudiantes.
- Badge: Insignias/badge del sistema.
- StudentBadge: Badges ganados por estudiantes.
- Quiz: Quiz autocorregible con preguntas de opción múltiple.
- QuizQuestion: Preguntas del quiz.
- QuizChoice: Opciones de respuesta.
- QuizAttempt: Intento de quiz por estudiante.
- Ranking: Snapshot semanal/mensual de rankings por curso.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.courses.models import Course, StudentCourse


class TipTransaction(models.Model):
    """Transacción de Tip (+XP manual del profesor a estudiante)."""
    class Reason(models.TextChoices):
        GREAT_PARTICIPATION = 'PARTICIPATION', 'Gran participación'
        HELP_PEER = 'HELP_PEER', 'Ayudó a compañero'
        CREATIVE_SOLUTION = 'CREATIVE', 'Solución creativa'
        EXTRA_EFFORT = 'EFFORT', 'Esfuerzo extra'
        LEADERSHIP = 'LEADERSHIP', 'Liderazgo'
        CUSTOM = 'CUSTOM', 'Otro'

    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tips_given')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tips_received')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='tip_transactions')
    xp_amount = models.PositiveIntegerField(default=5, help_text='XP otorgado (default 5)')
    reason = models.CharField(max_length=20, choices=Reason.choices, default=Reason.CUSTOM)
    custom_reason = models.CharField(max_length=200, blank=True, help_text='Motivo personalizado')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"+{self.xp_amount} XP para {self.student.email} por {self.get_reason_display()}"


class Reward(models.Model):
    """Recompensa académica canjeable por XP."""
    class Type(models.TextChoices):
        EXTENSION = 'EXTENSION', 'Día extra de plazo'
        SKIP_TASK = 'SKIP_TASK', 'Saltar una tarea'
        BONUS_XP = 'BONUS_XP', 'Bonus XP extra'
        BADGE = 'BADGE', 'Badge exclusivo'
        PRIVILEGE = 'PRIVILEGE', 'Privilegio especial'
        CUSTOM = 'CUSTOM', 'Personalizada'

    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='rewards')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.CUSTOM)
    xp_cost = models.PositiveIntegerField(help_text='Costo en XP del estudiante')
    icon = models.CharField(max_length=50, default='bi-gift', help_text='Icono Bootstrap Icons')
    max_claims = models.PositiveIntegerField(default=0, help_text='0 = ilimitado')
    current_claims = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='rewards_created')

    class Meta:
        ordering = ['xp_cost', 'name']

    def __str__(self):
        return f"{self.name} ({self.xp_cost} XP)"

    @property
    def is_available(self):
        if not self.is_active:
            return False
        if self.max_claims > 0 and self.current_claims >= self.max_claims:
            return False
        return True


class StudentReward(models.Model):
    """Canje de recompensa por estudiante."""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='claimed_rewards')
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE, related_name='student_claims')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    claimed_at = models.DateTimeField(auto_now_add=True)
    xp_spent = models.PositiveIntegerField()  # XP gastado en el momento del canje
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-claimed_at']

    def __str__(self):
        return f"{self.student.email} canjeó {self.reward.name}"


class Badge(models.Model):
    """Insignia/badge del sistema."""
    class Category(models.TextChoices):
        ACADEMIC = 'ACADEMIC', 'Académica'
        SOCIAL = 'SOCIAL', 'Social'
        CONSISTENCY = 'CONSISTENCY', 'Constancia'
        ACHIEVEMENT = 'ACHIEVEMENT', 'Logro'
        SPECIAL = 'SPECIAL', 'Especial'

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.ACHIEVEMENT)
    icon = models.CharField(max_length=50, default='bi-award', help_text='Icono Bootstrap Icons')
    color = models.CharField(max_length=20, default='gold', help_text='Color CSS o clase')
    xp_reward = models.PositiveIntegerField(default=0, help_text='XP extra al ganarla')
    is_secret = models.BooleanField(default=False, help_text='No visible hasta ganarla')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='badges_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class StudentBadge(models.Model):
    """Badge ganado por estudiante."""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='student_badges')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='student_badges')
    earned_at = models.DateTimeField(auto_now_add=True)
    earned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='badges_awarded')
    xp_awarded = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['student', 'badge', 'course']
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.student.email} - {self.badge.name}"


# === QUIZZES AUTOCORREGIBLES ===

class Quiz(models.Model):
    """Quiz autocorregible para un curso."""
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    xp_reward = models.PositiveIntegerField(default=10, help_text='XP al completar con nota mínima')
    passing_score = models.PositiveIntegerField(default=60, help_text='Nota mínima para aprobar (0-100)')
    time_limit = models.PositiveIntegerField(default=0, help_text='Límite en minutos (0 = sin límite)')
    max_attempts = models.PositiveIntegerField(default=3, help_text='Máx. intentos permitidos')
    shuffle_questions = models.BooleanField(default=True)
    shuffle_choices = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='quizzes_created')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.course.name} - {self.title}"

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def total_points(self):
        return sum(q.points for q in self.questions.all())

    def is_available(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.available_from and now < self.available_from:
            return False
        if self.available_until and now > self.available_until:
            return False
        return True


class QuizQuestion(models.Model):
    """Pregunta de quiz."""
    class Type(models.TextChoices):
        SINGLE_CHOICE = 'SINGLE', 'Opción única'
        MULTIPLE_CHOICE = 'MULTIPLE', 'Opción múltiple'
        TRUE_FALSE = 'TF', 'Verdadero/Falso'

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    order = models.PositiveIntegerField(default=0)
    text = models.TextField()
    type = models.CharField(max_length=10, choices=Type.choices, default=Type.SINGLE_CHOICE)
    points = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True, help_text='Explicación mostrada tras responder')

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}: {self.text[:50]}"


class QuizChoice(models.Model):
    """Opción de respuesta."""
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='choices')
    order = models.PositiveIntegerField(default=0)
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.question} - {self.text[:50]}"


class QuizAttempt(models.Model):
    """Intento de quiz por estudiante."""
    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'En progreso'
        SUBMITTED = 'SUBMITTED', 'Enviado'
        GRADED = 'GRADED', 'Calificado'

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Porcentaje 0-100')
    xp_earned = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)
    answers = models.JSONField(default=dict, help_text='Respuestas: {question_id: [choice_ids]}')
    time_spent = models.PositiveIntegerField(default=0, help_text='Segundos')

    class Meta:
        ordering = ['-started_at']
        unique_together = ['quiz', 'student']  # Un intento activo por quiz

    def __str__(self):
        return f"{self.student.email} - {self.quiz.title} ({self.get_status_display()})"

    def submit(self, answers_dict):
        """Auto-corregir y calcular puntaje."""
        self.answers = answers_dict
        self.submitted_at = timezone.now()
        self.status = self.Status.GRADED

        total_points = 0
        earned_points = 0

        for question in self.quiz.questions.all():
            total_points += question.points
            correct_choices = set(c.pk for c in question.choices.filter(is_correct=True))
            student_choices = set(answers_dict.get(str(question.pk), []))

            if question.type == QuizQuestion.Type.TRUE_FALSE or question.type == QuizQuestion.Type.SINGLE_CHOICE:
                if len(student_choices) == 1 and student_choices == correct_choices:
                    earned_points += question.points
            elif question.type == QuizQuestion.Type.MULTIPLE_CHOICE:
                # Crédito parcial: puntos por cada opción correcta marcada, penalización por incorrectas
                # Solo puntos completos si coincide exactamente
                if student_choices == correct_choices:
                    earned_points += question.points

        if total_points > 0:
            self.score = round((earned_points / total_points) * 100, 2)
        else:
            self.score = 0

        self.passed = self.score >= self.quiz.passing_score

        if self.passed:
            self.xp_earned = self.quiz.xp_reward
            self.student.add_xp(self.xp_earned, source=f'Quiz: {self.quiz.title}')

            # Registrar actividad para streaks
            from apps.accounts.models import UserActivity
            UserActivity.record_activity(self.student, 'quiz')

            # Notificar al estudiante con link al loot box
            from apps.accounts.models import Notification
            Notification.objects.create(
                user=self.student,
                message=f'¡Completaste el quiz "{self.quiz.title}" con {self.score}%! Ganaste {self.xp_earned} XP.',
                link=f'/tasks/lootbox/quiz/{self.pk}/'
            )
        else:
            self.xp_earned = 0

        self.save(update_fields=['answers', 'submitted_at', 'status', 'score', 'xp_earned', 'passed'])
        return self


class Ranking(models.Model):
    """Snapshot de ranking por curso (semanal o mensual)."""
    class Period(models.TextChoices):
        WEEKLY = 'WEEKLY', 'Semanal'
        MONTHLY = 'MONTHLY', 'Mensual'

    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='rankings')
    period = models.CharField(max_length=10, choices=Period.choices, default=Period.WEEKLY)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rankings')
    position = models.PositiveIntegerField(help_text='Posición en el ranking')
    xp_earned = models.PositiveIntegerField(default=0, help_text='XP ganado en el período')
    total_xp = models.PositiveIntegerField(default=0, help_text='XP acumulado total')
    tasks_completed = models.PositiveIntegerField(default=0)
    period_start = models.DateField()
    period_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['period', 'position']
        unique_together = ['course', 'student', 'period', 'period_start']

    def __str__(self):
        return f"{self.course.name} - #{self.position} {self.student.email} ({self.get_period_display()})"

    @classmethod
    def _calculate_student_course_xp(cls, student, course, start_date, end_date):
        """Calcula todo el XP de un estudiante en un curso dentro de un período."""
        from apps.tasks.models import Task
        from django.db.models import Sum

        total_xp = 0

        # 1. XP de tareas completadas (score de la tarea)
        task_xp = Task.objects.filter(
            course=course,
            assigned_to=student,
            is_completed=True,
            completed_at__date__gte=start_date,
            completed_at__date__lte=end_date,
        ).aggregate(total=Sum('score'))['total'] or 0
        total_xp += task_xp

        # 2. XP de Tips recibidos en este curso
        tip_xp = cls.objects.none()  # placeholder
        from apps.gamification.models import TipTransaction
        tip_xp = TipTransaction.objects.filter(
            student=student,
            course=course,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ).aggregate(total=Sum('xp_amount'))['total'] or 0
        total_xp += tip_xp

        # 3. XP de Quizzes completados en este curso
        from apps.gamification.models import QuizAttempt
        quiz_xp = QuizAttempt.objects.filter(
            student=student,
            quiz__course=course,
            passed=True,
            submitted_at__date__gte=start_date,
            submitted_at__date__lte=end_date,
        ).aggregate(total=Sum('xp_earned'))['total'] or 0
        total_xp += quiz_xp

        # 4. XP de Badges ganados en este curso
        from apps.gamification.models import StudentBadge
        badge_xp = StudentBadge.objects.filter(
            student=student,
            course=course,
            earned_at__date__gte=start_date,
            earned_at__date__lte=end_date,
        ).aggregate(total=Sum('xp_awarded'))['total'] or 0
        total_xp += badge_xp

        return total_xp

    @classmethod
    def _count_completed_tasks(cls, student, course, start_date, end_date):
        """Cuenta tareas completadas en un curso dentro de un período."""
        from apps.tasks.models import Task
        return Task.objects.filter(
            course=course,
            assigned_to=student,
            is_completed=True,
            completed_at__date__gte=start_date,
            completed_at__date__lte=end_date,
        ).count()

    @classmethod
    def generate_weekly(cls, course):
        """Genera ranking semanal para un curso (todas las fuentes de XP)."""
        from datetime import timedelta

        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        return cls._generate_ranking(course, cls.Period.WEEKLY, week_start, week_end)

    @classmethod
    def generate_monthly(cls, course):
        """Genera ranking mensual para un curso (todas las fuentes de XP)."""
        import calendar

        today = timezone.now().date()
        month_start = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        month_end = today.replace(day=last_day)

        return cls._generate_ranking(course, cls.Period.MONTHLY, month_start, month_end)

    @classmethod
    def _generate_ranking(cls, course, period, start_date, end_date):
        """Genera ranking genérico incluyendo TODAS las fuentes de XP."""
        students = StudentCourse.objects.filter(
            course=course, status=StudentCourse.Status.ACTIVE
        ).select_related('student')

        rankings = []
        for enrollment in students:
            student = enrollment.student
            xp_earned = cls._calculate_student_course_xp(student, course, start_date, end_date)
            tasks_completed = cls._count_completed_tasks(student, course, start_date, end_date)

            if xp_earned > 0 or tasks_completed > 0:
                rankings.append({
                    'student': student,
                    'xp_earned': xp_earned,
                    'total_xp': student.xp,
                    'tasks_completed': tasks_completed,
                })

        rankings.sort(key=lambda x: x['xp_earned'], reverse=True)

        cls.objects.filter(
            course=course,
            period=period,
            period_start=start_date,
        ).delete()

        for i, r in enumerate(rankings, 1):
            cls.objects.create(
                course=course,
                period=period,
                student=r['student'],
                position=i,
                xp_earned=r['xp_earned'],
                total_xp=r['total_xp'],
                tasks_completed=r['tasks_completed'],
                period_start=start_date,
                period_end=end_date,
            )

        return len(rankings)

    @classmethod
    def get_course_stats(cls, course):
        """Retorna estadísticas de productividad de un curso."""
        from apps.tasks.models import Task
        from django.db.models import Avg, Count, Q, Sum
        from apps.gamification.models import TipTransaction, QuizAttempt, StudentBadge

        students = StudentCourse.objects.filter(
            course=course, status=StudentCourse.Status.ACTIVE
        )

        total_students = students.count()
        total_tasks = Task.objects.filter(course=course).count()
        completed_tasks = Task.objects.filter(course=course, is_completed=True).count()
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        avg_score = Task.objects.filter(
            course=course, is_completed=True, score__isnull=False
        ).aggregate(avg=Avg('score'))['avg'] or 0

        total_tips_xp = TipTransaction.objects.filter(course=course).aggregate(
            total=Sum('xp_amount'))['total'] or 0

        total_quiz_xp = QuizAttempt.objects.filter(
            quiz__course=course, passed=True
        ).aggregate(total=Sum('xp_earned'))['total'] or 0

        total_badge_xp = StudentBadge.objects.filter(
            course=course
        ).aggregate(total=Sum('xp_awarded'))['total'] or 0

        total_xp_generated = total_tips_xp + total_quiz_xp + total_badge_xp

        overdue_tasks = Task.objects.filter(
            course=course,
            is_completed=False,
            deadline__lt=timezone.now(),
        ).count()

        return {
            'total_students': total_students,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': round(completion_rate, 1),
            'avg_score': round(avg_score, 1),
            'overdue_tasks': overdue_tasks,
            'total_tips_xp': total_tips_xp,
            'total_quiz_xp': total_quiz_xp,
            'total_badge_xp': total_badge_xp,
            'total_xp_generated': total_xp_generated,
        }

    @classmethod
    def get_all_courses_ranking(cls):
        """Ranking entre cursos: compara rendimiento promedio."""
        from apps.tasks.models import Task
        from apps.gamification.models import TipTransaction, QuizAttempt, StudentBadge
        from django.db.models import Avg, Sum, Count, Q, F

        courses = Course.objects.filter(status=Course.Status.ACTIVE).annotate(
            active_students=Count(
                'student_enrollments',
                filter=Q(student_enrollments__status=StudentCourse.Status.ACTIVE)
            ),
            total_tasks=Count('tasks'),
            completed_tasks=Count('tasks', filter=Q(tasks__is_completed=True)),
        ).filter(active_students__gt=0)

        course_data = []
        for course in courses:
            total_tasks = course.total_tasks
            completed_tasks = course.completed_tasks
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            avg_score = Task.objects.filter(
                course=course, is_completed=True, score__isnull=False
            ).aggregate(avg=Avg('score'))['avg'] or 0

            tips_xp = TipTransaction.objects.filter(course=course).aggregate(
                total=Sum('xp_amount'))['total'] or 0
            quiz_xp = QuizAttempt.objects.filter(
                quiz__course=course, passed=True
            ).aggregate(total=Sum('xp_earned'))['total'] or 0
            badge_xp = StudentBadge.objects.filter(
                course=course
            ).aggregate(total=Sum('xp_awarded'))['total'] or 0

            total_xp = tips_xp + quiz_xp + badge_xp
            avg_xp_per_student = (total_xp / course.active_students) if course.active_students > 0 else 0

            course_data.append({
                'course': course,
                'active_students': course.active_students,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': round(completion_rate, 1),
                'avg_score': round(avg_score, 1),
                'total_xp_generated': total_xp,
                'avg_xp_per_student': round(avg_xp_per_student, 1),
            })

        course_data.sort(key=lambda x: x['avg_xp_per_student'], reverse=True)

        for i, data in enumerate(course_data, 1):
            data['position'] = i

        return course_data