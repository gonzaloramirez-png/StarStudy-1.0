"""Vistas de Architecture Decision Records."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required
from ..decorators import dev_profile_required
from ..models import DevADR
from ..forms import DevADRForm


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def adr_list(request):
    """Listado de ADRs."""
    adrs = DevADR.objects.all()
    status = request.GET.get('status', '')
    if status:
        adrs = adrs.filter(status=status)
    return render(request, 'dev/adr/adr_list.html', {
        'adrs': adrs,
        'current_status': status,
        'status_choices': DevADR.Status.choices,
    })


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def adr_detail(request, pk):
    """Detalle de un ADR."""
    adr = get_object_or_404(DevADR, pk=pk)
    return render(request, 'dev/adr/adr_detail.html', {'adr': adr})


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def adr_create(request):
    """Crear un ADR."""
    if request.method == 'POST':
        form = DevADRForm(request.POST)
        if form.is_valid():
            adr = form.save(commit=False)
            adr.author = request.user
            adr.save()
            messages.success(request, 'ADR creado.')
            return redirect('dev:adr_list')
    else:
        form = DevADRForm()
    return render(request, 'dev/adr/adr_form.html', {'form': form, 'title': 'Nuevo ADR'})


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def adr_edit(request, pk):
    """Editar un ADR."""
    adr = get_object_or_404(DevADR, pk=pk, author=request.user)
    if request.method == 'POST':
        form = DevADRForm(request.POST, instance=adr)
        if form.is_valid():
            form.save()
            messages.success(request, 'ADR actualizado.')
            return redirect('dev:adr_detail', pk=pk)
    else:
        form = DevADRForm(instance=adr)
    return render(request, 'dev/adr/adr_form.html', {'form': form, 'title': 'Editar ADR'})
