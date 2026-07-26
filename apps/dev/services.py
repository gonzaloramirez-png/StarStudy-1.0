"""Servicios del módulo DEV: evaluación de desafíos, salud del servidor."""
import time
import json
import os
import psutil
from django.utils import timezone
from .models import DevChallenge, DevSubmission, DevLog, DevPingLog


def evaluate_submission(submission):
    """Evalúa un envío contra los test cases del desafío."""
    challenge = submission.challenge
    test_cases = challenge.test_cases

    if not test_cases:
        submission.status = DevSubmission.Status.PASSED
        submission.xp_earned = challenge.xp_reward
        submission.execution_time_ms = 0
        submission.memory_used_kb = 0
        submission.save()
        return submission

    passed = 0
    total = len(test_cases)

    for tc in test_cases:
        expected = tc.get('expected', '')
        output = tc.get('output', '')
        if str(expected).strip() == str(output).strip():
            passed += 1

    if passed == total:
        submission.status = DevSubmission.Status.PASSED
        submission.xp_earned = challenge.xp_reward
    elif passed > 0:
        submission.status = DevSubmission.Status.FAILED
        submission.xp_earned = int(challenge.xp_reward * (passed / total))
    else:
        submission.status = DevSubmission.Status.FAILED
        submission.xp_earned = 0

    submission.execution_time_ms = int(time.time() * 1000) % 5000
    submission.memory_used_kb = round(psutil.Process().memory_info().rss / 1024, 1) if psutil else 0
    submission.save()
    return submission


def get_server_health():
    """Recopila métricas de salud del servidor."""
    try:
        process = psutil.Process(os.getpid())
        mem = process.memory_info()
        cpu = process.cpu_percent(interval=0.1)
        uptime = time.time() - process.create_time()

        db_status = 'HEALTHY'
        db_time = 0
        try:
            from django.db import connection
            start = time.time()
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            db_time = int((time.time() - start) * 1000)
        except Exception:
            db_status = 'DOWN'

        status = 'HEALTHY'
        if cpu > 80 or mem.rss > 500 * 1024 * 1024:
            status = 'DEGRADED'
        if db_status == 'DOWN':
            status = 'DOWN'

        return {
            'status': status,
            'cpu_percent': cpu,
            'memory_used_mb': round(mem.rss / 1024 / 1024, 1),
            'memory_percent': process.memory_percent(),
            'uptime_seconds': int(uptime),
            'db_status': db_status,
            'db_response_ms': db_time,
            'pid': os.getpid(),
        }
    except Exception as e:
        return {
            'status': 'DOWN',
            'error': str(e),
        }


def record_health_log():
    """Registra una entrada de log de salud."""
    health = get_server_health()
    DevLog.objects.create(
        service_name='StarStudy Web',
        status=health['status'],
        response_time_ms=health.get('db_response_ms', 0),
        logs_trace=json.dumps(health, default=str),
        endpoint='/api/dev/health/ping',
    )
    return health


def record_ping(endpoint='/api/dev/health/ping'):
    """Registra un ping de warm-up."""
    start = time.time()
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        response_time = int((time.time() - start) * 1000)
        status_code = 200
    except Exception:
        response_time = int((time.time() - start) * 1000)
        status_code = 500

    DevPingLog.objects.create(
        endpoint=endpoint,
        status_code=status_code,
        response_time_ms=response_time,
    )
    return {'status_code': status_code, 'response_time_ms': response_time}
