"""Crea desafíos de ejemplo para el módulo DEV."""
from django.db import migrations


CHALLENGES = [
    {
        'title': 'Simplificar con ternarios',
        'description': 'Reescribí las siguientes funciones usando operadores ternarios para hacer el código más conciso.',
        'difficulty': 'EASY',
        'category': 'REFACTORING',
        'initial_code': 'def paridad(n):\n    if n % 2 == 0:\n        return "par"\n    else:\n        return "impar"',
        'test_cases': [
            {'input': 'paridad(4)', 'expected': 'par'},
            {'input': 'paridad(7)', 'expected': 'impar'},
            {'input': 'paridad(0)', 'expected': 'par'},
        ],
        'xp_reward': 25,
        'frequency': 'DAILY',
    },
    {
        'title': 'Optimizar query con JOIN',
        'description': 'Dado el siguiente ORM query que hace N+1, optimizalo usando select_related o prefetch_related.',
        'difficulty': 'EASY',
        'category': 'SQL_OPTIMIZATION',
        'initial_code': '# Mal: N+1 queries\nfor task in Task.objects.all():\n    print(task.assigned_to.email)',
        'test_cases': [
            {'input': 'select_related', 'expected': 'assigned_to'},
            {'input': 'query_count', 'expected': '1'},
        ],
        'xp_reward': 25,
        'frequency': 'DAILY',
    },
    {
        'title': 'Validar input contra XSS',
        'description': 'Implementá sanitización de input para prevenir ataques XSS en un formulario que acepta HTML.',
        'difficulty': 'MEDIUM',
        'category': 'SECURITY_OWASP',
        'initial_code': 'def sanitize_input(user_input):\n    # Tu código aquí\n    pass',
        'test_cases': [
            {'input': '<script>alert("xss")</script>', 'expected': 'sanitized'},
            {'input': 'Hello <b>world</b>', 'expected': 'Hello world'},
        ],
        'xp_reward': 50,
        'frequency': 'EVERY_3_DAYS',
    },
    {
        'title': 'Separar concerns en clase',
        'description': 'Refactorizá esta clase que hace demasiadas cosas: validación, persistencia y notificación.',
        'difficulty': 'MEDIUM',
        'category': 'ARCHITECTURE',
        'initial_code': 'class OrderProcessor:\n    def process(self, data):\n        self.validate(data)\n        self.save(data)\n        self.notify(data)\n        self.log(data)',
        'test_cases': [
            {'input': 'single_responsibility', 'expected': True},
            {'input': 'classes_count', 'expected': '>=3'},
        ],
        'xp_reward': 50,
        'frequency': 'EVERY_3_DAYS',
    },
    {
        'title': 'Extraer función de monolito',
        'description': 'Identificá y extraé la lógica de cálculo de descuentos en una función pura separada.',
        'difficulty': 'MEDIUM',
        'category': 'REFACTORING',
        'initial_code': 'def process_purchase(user, items):\n    total = sum(i.price for i in items)\n    if user.is_premium:\n        total *= 0.8\n    if total > 100:\n        total -= 10\n    return total',
        'test_cases': [
            {'input': 'function_extracted', 'expected': True},
            {'input': 'testable_independently', 'expected': True},
        ],
        'xp_reward': 50,
        'frequency': 'WEEKLY',
    },
    {
        'title': 'Query recursivo optimizado',
        'description': 'Implementá una query recursiva en Django ORM para obtener la jerarquía de categorías sin hacer queries en loop.',
        'difficulty': 'HARD',
        'category': 'SQL_OPTIMIZATION',
        'initial_code': '# Obtener todos los hijos de una categoría\n# sin hacer N+1 queries',
        'test_cases': [
            {'input': 'recursive_query', 'expected': 'single_query'},
            {'input': 'performance', 'expected': 'O(1) queries'},
        ],
        'xp_reward': 100,
        'frequency': 'WEEKLY',
    },
    {
        'title': 'Autenticación segura de endpoints',
        'description': 'Implementá un sistema de autenticación que prevenga timing attacks,CSRF, y rate limiting.',
        'difficulty': 'HARD',
        'category': 'SECURITY_OWASP',
        'initial_code': 'def secure_endpoint(request):\n    # Implementar autenticación segura\n    pass',
        'test_cases': [
            {'input': 'timing_attack_resistant', 'expected': True},
            {'input': 'rate_limited', 'expected': True},
            {'input': 'csrf_protected', 'expected': True},
        ],
        'xp_reward': 100,
        'frequency': 'WEEKLY',
    },
    {
        'title': 'Patrón Strategy para pagos',
        'description': 'Implementá el patrón Strategy para soportar múltiples métodos de pago sin usar if/elif.',
        'difficulty': 'HARD',
        'category': 'ARCHITECTURE',
        'initial_code': 'class PaymentProcessor:\n    def pay(self, method, amount):\n        if method == "credit_card":\n            ...\n        elif method == "paypal":\n            ...\n        elif method == "crypto":\n            ...',
        'test_cases': [
            {'input': 'strategy_pattern', 'expected': True},
            {'input': 'open_closed_principle', 'expected': True},
            {'input': 'easy_to_add_new', 'expected': True},
        ],
        'xp_reward': 100,
        'frequency': 'WEEKLY',
    },
]


def forwards(apps, schema_editor):
    DevChallenge = apps.get_model('dev', 'DevChallenge')
    for c in CHALLENGES:
        DevChallenge.objects.get_or_create(
            title=c['title'],
            defaults=c,
        )


def backwards(apps, schema_editor):
    DevChallenge = apps.get_model('dev', 'DevChallenge')
    for c in CHALLENGES:
        DevChallenge.objects.filter(title=c['title']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('dev', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
