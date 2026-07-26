"""Vistas de snippets."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.accounts.decorators import role_required
from ..decorators import dev_profile_required
from ..models import DevSnippet
from ..forms import DevSnippetForm


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def snippet_list(request):
    """Listado de snippets del dev."""
    profile = request.dev_profile
    snippets = DevSnippet.objects.filter(dev_profile=profile)

    tag = request.GET.get('tag', '')
    if tag:
        snippets = snippets.filter(tags__contains=[tag])

    all_tags = set()
    for s in DevSnippet.objects.filter(dev_profile=profile):
        all_tags.update(s.tags)

    context = {
        'snippets': snippets,
        'all_tags': sorted(all_tags),
        'current_tag': tag,
    }
    return render(request, 'dev/snippets/snippet_list.html', context)


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def snippet_create(request):
    """Crear un snippet."""
    if request.method == 'POST':
        form = DevSnippetForm(request.POST)
        if form.is_valid():
            snippet = form.save(commit=False)
            snippet.dev_profile = request.dev_profile
            snippet.save()
            messages.success(request, 'Snippet guardado.')
            return redirect('dev:snippet_list')
    else:
        form = DevSnippetForm()
    return render(request, 'dev/snippets/snippet_form.html', {'form': form, 'title': 'Nuevo Snippet'})


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def snippet_edit(request, pk):
    """Editar un snippet."""
    snippet = get_object_or_404(DevSnippet, pk=pk, dev_profile=request.dev_profile)
    if request.method == 'POST':
        form = DevSnippetForm(request.POST, instance=snippet)
        if form.is_valid():
            form.save()
            messages.success(request, 'Snippet actualizado.')
            return redirect('dev:snippet_list')
    else:
        form = DevSnippetForm(instance=snippet)
    return render(request, 'dev/snippets/snippet_form.html', {'form': form, 'title': 'Editar Snippet'})


@login_required
@role_required('PROGRAMMER')
@dev_profile_required
def snippet_delete(request, pk):
    """Eliminar un snippet."""
    snippet = get_object_or_404(DevSnippet, pk=pk, dev_profile=request.dev_profile)
    if request.method == 'POST':
        snippet.delete()
        messages.success(request, 'Snippet eliminado.')
    return redirect('dev:snippet_list')
