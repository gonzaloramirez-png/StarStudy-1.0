"""Comando para generar rankings semanales y mensuales de todos los cursos activos.

Uso:
    python manage.py generate_rankings              # Genera ambos
    python manage.py generate_rankings --period weekly
    python manage.py generate_rankings --period monthly
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.courses.models import Course
from apps.gamification.models import Ranking


class Command(BaseCommand):
    help = 'Genera rankings semanales y mensuales para todos los cursos activos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            choices=['weekly', 'monthly', 'both'],
            default='both',
            help='Período a generar (default: both)',
        )
        parser.add_argument(
            '--course',
            type=int,
            help='ID de curso específico (default: todos los activos)',
        )

    def handle(self, *args, **options):
        period = options['period']
        course_id = options.get('course')

        if course_id:
            courses = Course.objects.filter(pk=course_id, status=Course.Status.ACTIVE)
        else:
            courses = Course.objects.filter(status=Course.Status.ACTIVE)

        total_weekly = 0
        total_monthly = 0

        for course in courses:
            if period in ('weekly', 'both'):
                count = Ranking.generate_weekly(course)
                total_weekly += count
                self.stdout.write(f'  [SEMANAL] {course.name}: {count} estudiantes rankeados')

            if period in ('monthly', 'both'):
                count = Ranking.generate_monthly(course)
                total_monthly += count
                self.stdout.write(f'  [MENSUAL] {course.name}: {count} estudiantes rankeados')

        self.stdout.write(self.style.SUCCESS(
            f'\nRankings generados: {total_weekly} semanales, {total_monthly} mensuales'
        ))
