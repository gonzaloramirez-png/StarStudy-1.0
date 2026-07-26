"""Servicio de exportación: Excel/CSV + PDF para tareas y notas del curso."""
import csv
import io
from datetime import datetime
from django.http import HttpResponse
from django.db.models import Avg, Count, Q


def export_grades_csv(course, tasks):
    """Exportar notas del curso a CSV."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="notas_{course.name}_{datetime.now().strftime("%Y%m%d")}.csv"'

    # BOM para Excel
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Estudiante', 'Tarea', 'Importancia', 'Estado', 'Nota', 'XP', 'Fecha Entrega', 'Deadline', 'Corregido por', 'Fecha Corrección'])

    for task in tasks:
        xp = round(task.score * 0.25) if task.score else 0
        writer.writerow([
            task.assigned_to.get_full_name() or task.assigned_to.email,
            task.title,
            task.get_importance_display(),
            task.get_status_display(),
            task.score if task.score is not None else '',
            xp,
            task.completed_at.strftime('%d/%m/%Y %H:%M') if task.completed_at else '',
            task.deadline.strftime('%d/%m/%Y %H:%M'),
            task.corrected_by.get_full_name() if task.corrected_by else '',
            task.corrected_at.strftime('%d/%m/%Y %H:%M') if task.corrected_at else '',
        ])

    return response


def export_grades_pdf(course, tasks):
    """Exportar notas del curso a PDF (reportlab)."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        return HttpResponse('reportlab no instalado. Ejecutá: pip install reportlab', status=500)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="informe_{course.name}_{datetime.now().strftime("%Y%m%d")}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4), rightMargin=1*cm, leftMargin=1*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title2', parent=styles['Title'], fontSize=16, spaceAfter=6)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, textColor=colors.grey, spaceAfter=12)
    normal_style = ParagraphStyle('Normal2', parent=styles['Normal'], fontSize=8)

    elements = []

    # Título
    elements.append(Paragraph(f"Informe de Notas - {course.name}", title_style))
    elements.append(Paragraph(f"Año lectivo: {course.academic_year} | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))

    # Stats
    stats = tasks.aggregate(
        total=Count('id'),
        avg_score=Avg('score'),
        corrected=Count('id', filter=Q(status='CORRECTED')),
    )
    stats_text = f"Total tareas: {stats['total']} | Corregidas: {stats['corrected']} | Promedio: {stats['avg_score']:.1f}%" if stats['avg_score'] else f"Total tareas: {stats['total']}"
    elements.append(Paragraph(stats_text, normal_style))
    elements.append(Spacer(1, 12))

    # Tabla de datos
    data = [['Estudiante', 'Tarea', 'Estado', 'Nota', 'XP', 'Deadline']]
    for task in tasks:
        xp = round(task.score * 0.25) if task.score else 0
        data.append([
            (task.assigned_to.get_full_name() or task.assigned_to.email)[:25],
            task.title[:30],
            task.get_status_display(),
            str(task.score) if task.score is not None else '--',
            str(xp),
            task.deadline.strftime('%d/%m %H:%M'),
        ])

    table = Table(data, colWidths=[5*cm, 6*cm, 3*cm, 2*cm, 2*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1d21')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(table)
    doc.build(elements)

    return response


def export_student_report_pdf(course, student, tasks):
    """Exportar reporte individual de estudiante a PDF."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER
    except ImportError:
        return HttpResponse('reportlab no instalado', status=500)

    response = HttpResponse(content_type='application/pdf')
    filename = f"reporte_{student.get_full_name() or student.email}_{course.name}_{datetime.now().strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title2', parent=styles['Title'], fontSize=14)
    normal_style = ParagraphStyle('Normal2', parent=styles['Normal'], fontSize=10)
    bold_style = ParagraphStyle('Bold2', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')

    elements = []

    # Datos del estudiante
    elements.append(Paragraph(f"Reporte Académico", title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>Estudiante:</b> {student.get_full_name() or student.email}", normal_style))
    elements.append(Paragraph(f"<b>Curso:</b> {course.name} ({course.academic_year})", normal_style))
    elements.append(Paragraph(f"<b>XP total:</b> {student.xp} | <b>Nivel:</b> {student.level}", normal_style))
    elements.append(Spacer(1, 12))

    # Stats
    total = tasks.count()
    corrected = tasks.filter(status='CORRECTED').count()
    avg = tasks.aggregate(avg=Avg('score'))['avg']
    passed = tasks.filter(score__gte=60).count()

    elements.append(Paragraph(f"<b>Resumen:</b> {total} tareas | {corrected} corregidas | Promedio: {avg:.1f}% | Aprobadas (≥60%): {passed}", normal_style))
    elements.append(Spacer(1, 12))

    # Tabla de tareas
    data = [['Tarea', 'Estado', 'Nota', 'XP', 'Deadline']]
    for task in tasks:
        xp = round(task.score * 0.25) if task.score else 0
        data.append([
            task.title[:40],
            task.get_status_display(),
            str(task.score) if task.score is not None else '--',
            str(xp),
            task.deadline.strftime('%d/%m/%Y'),
        ])

    table = Table(data, colWidths=[7*cm, 3*cm, 2*cm, 2*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(table)
    doc.build(elements)

    return response
