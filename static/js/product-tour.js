/**
 * Product Tour - StarStudy
 * Tour guiado para nuevos usuarios usando Shepherd.js
 * Detecta el rol del usuario y muestra pasos relevantes
 */

(function () {
  'use strict';

  const STORAGE_KEY = 'starstudy_tour_completed';
  const TOUR_VERSION = '1.0';

  // ====================================
  // Utilidades
  // ====================================

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }

  function getUserRole() {
    const body = document.body;
    if (body.classList.contains('role-student')) return 'STUDENT';
    if (body.classList.contains('role-teacher')) return 'TEACHER';
    if (body.classList.contains('role-staff')) return 'STAFF';
    if (body.classList.contains('role-programmer')) return 'PROGRAMMER';
    return 'STUDENT';
  }

  function hasCompletedTour() {
    try {
      const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      return data.version === TOUR_VERSION;
    } catch {
      return false;
    }
  }

  function markTourCompleted() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: TOUR_VERSION, date: new Date().toISOString() }));
  }

  function elementExists(selector) {
    return document.querySelector(selector) !== null;
  }

  // ====================================
  // Definición de pasos por sección
  // ====================================

  const commonSteps = [
    {
      id: 'welcome',
      title: 'Bienvenido a StarStudy',
      text: `<div class="tour-welcome">
        <span class="tour-welcome-icon">⭐</span>
        <div class="tour-welcome-title">Tu plataforma de estudio inteligente</div>
        <div class="tour-welcome-subtitle">Te vamos a guiar por las principales funciones para que empieces a usar StarStudy como un pro.</div>
      </div>`,
      buttons: [
        { text: 'Empezar Tour', action: function () { this.next(); }, classes: 'shepherd-button-primary' }
      ],
      cancelIcon: { enabled: true },
      classes: 'tour-welcome-step',
      scrollTo: false
    },
    {
      id: 'navbar',
      title: 'Tu Barra de Navegación',
      text: 'Acá tenés acceso rápido a todas las secciones de StarStudy. Desde aquí podés navegar a tus tareas, horarios, hábitos y más.',
      attachTo: { element: '.navbar', on: 'bottom' },
      buttons: [
        { text: 'Anterior', action: function () { this.back(); }, classes: 'shepherd-button-secondary' },
        { text: 'Siguiente', action: function () { this.next(); }, classes: 'shepherd-button-primary' }
      ],
      cancelIcon: { enabled: true },
      classes: 'tour-step'
    },
    {
      id: 'stats',
      title: 'Tus Estadísticas',
      text: 'Estas tarjetas muestran tu progreso en tiempo real: cuántas tareas tenés pendientes, cuántas vencieron, cuántas entregaste y tu nivel actual con barra de XP.',
      attachTo: { element: '.row.g-2.g-md-3.mb-4', on: 'bottom' },
      buttons: [
        { text: 'Anterior', action: function () { this.back(); }, classes: 'shepherd-button-secondary' },
        { text: 'Siguiente', action: function () { this.next(); }, classes: 'shepherd-button-primary' }
      ],
      cancelIcon: { enabled: true },
      classes: 'tour-step'
    },
    {
      id: 'streaks',
      title: 'Tus Rachas',
      text: 'Seguí completando hábitos todos los días para mantener tu racha. ¡La meta es llegar a 7 días y activar el badge de fuego! 🔥',
      attachTo: { element: '.card[style*="border-left: 4px solid #ff6b35"]', on: 'bottom' },
      buttons: [
        { text: 'Anterior', action: function () { this.back(); }, classes: 'shepherd-button-secondary' },
        { text: 'Siguiente', action: function () { this.next(); }, classes: 'shepherd-button-primary' }
      ],
      cancelIcon: { enabled: true },
      classes: 'tour-step'
    },
    {
      id: 'recent-tasks',
      title: 'Tus Tareas',
      text: 'Acá ves tus tareas más recientes y cuáles tenés que entregar. Hacé clic en cualquiera para ver los detalles y subir tu entrega.',
      attachTo: { element: '.col-md-6:first-child .card', on: 'left' },
      buttons: [
        { text: 'Anterior', action: function () { this.back(); }, classes: 'shepherd-button-secondary' },
        { text: 'Siguiente', action: function () { this.next(); }, classes: 'shepherd-button-primary' }
      ],
      cancelIcon: { enabled: true },
      classes: 'tour-step'
    },
    {
      id: 'notifications',
      title: 'Notificaciones',
      text: 'Las notificaciones aparecen acá. Mantené el ojo en los avisos de nuevas tareas, correcciones y mensajes de tu profesor.',
      attachTo: { element: '.btn-icon[aria-label="Notificaciones"]', on: 'bottom' },
      buttons: [
        { text: 'Anterior', action: function () { this.back(); }, classes: 'shepherd-button-secondary' },
        { text: 'Siguiente', action: function () { this.next(); }, classes: 'shepherd-button-primary' }
      ],
      cancelIcon: { enabled: true },
      classes: 'tour-step'
    },
    {
      id: 'profile-menu',
      title: 'Tu Perfil y Menú',
      text: 'Desde este menú podés acceder a tu perfil, configurar tus preferencias y cerrar sesión.',
      attachTo: { element: '.nav-item.dropdown:last-child', on: 'bottom' },
      buttons: [
        { text: 'Anterior', action: function () { this.back(); }, classes: 'shepherd-button-secondary' },
        { text: 'Entendido', action: function () { this.complete(); }, classes: 'shepherd-button-primary' }
      ],
      cancelIcon: { enabled: true },
      classes: 'tour-step'
    }
  ];

  const studentSteps = [
    {
      id: 'welcome-banner',
      title: 'Vinculate con tu Profesor',
      text: 'Si tu profesor te dio un código, ingresalo desde tu perfil para que te asigne tareas y cursos. ¡Es el primer paso para empezar!',
      attachTo: { element: '.welcome-banner', on: 'bottom' },
      buttons: [
        { text: 'Anterior', action: function () { this.back(); }, classes: 'shepherd-button-secondary' },
        { text: 'Siguiente', action: function () { this.next(); }, classes: 'shepherd-button-primary' }
      ],
      cancelIcon: { enabled: true },
      classes: 'tour-step',
      when: { show: function () { return elementExists('.welcome-banner'); } }
    },
    {
      id: 'course-switcher-student',
      title: 'Selector de Cursos',
      text: 'Si estás inscripto en varios cursos, podés cambiar entre ellos desde acá. Las tareas, horarios y estadísticas se actualizan según el curso seleccionado.',
      attachTo: { element: '#openCourseSwitcherBtn', on: 'bottom' },
      buttons: [
        { text: 'Anterior', action: function () { this.back(); }, classes: 'shepherd-button-secondary' },
        { text: 'Siguiente', action: function () { this.next(); }, classes: 'shepherd-button-primary' }
      ],
      cancelIcon: { enabled: true },
      classes: 'tour-step'
    }
  ];

  const teacherSteps = [
    {
      id: 'course-switcher-teacher',
      title: 'Gestioná tus Cursos',
      text: 'Como profesor, podés crear y administrar tus cursos desde acá. Seleccioná un curso para ver sus tareas, estudiantes y estadísticas.',
      attachTo: { element: '#openCourseSwitcherBtn', on: 'bottom' },
      buttons: [
        { text: 'Anterior', action: function () { this.back(); }, classes: 'shepherd-button-secondary' },
        { text: 'Siguiente', action: function () { this.next(); }, classes: 'shepherd-button-primary' }
      ],
      cancelIcon: { enabled: true },
      classes: 'tour-step'
    }
  ];

  const staffSteps = [
    {
      id: 'course-switcher-staff',
      title: 'Supervisión de Cursos',
      text: 'Como staff, tenés acceso a todos los cursos de la institución. Seleccioná uno para supervisar el progreso de profesores y estudiantes.',
      attachTo: { element: '#openCourseSwitcherBtn', on: 'bottom' },
      buttons: [
        { text: 'Anterior', action: function () { this.back(); }, classes: 'shepherd-button-secondary' },
        { text: 'Siguiente', action: function () { this.next(); }, classes: 'shepherd-button-primary' }
      ],
      cancelIcon: { enabled: true },
      classes: 'tour-step'
    }
  ];

  const programmerSteps = [
    {
      id: 'dev-dashboard',
      title: 'Panel de Desarrollo',
      text: 'Como programador, tenés acceso al Dev Dashboard con challenges, snippets, rankings y métricas de la plataforma.',
      attachTo: { element: '.nav-link[href*="dev"]', on: 'bottom' },
      buttons: [
        { text: 'Anterior', action: function () { this.back(); }, classes: 'shepherd-button-secondary' },
        { text: 'Siguiente', action: function () { this.next(); }, classes: 'shepherd-button-primary' }
      ],
      cancelIcon: { enabled: true },
      classes: 'tour-step'
    }
  ];

  const finalStep = [
    {
      id: 'finish',
      title: '¡Todo Listo!',
      text: `<div class="tour-welcome">
        <span class="tour-welcome-icon">🚀</span>
        <div class="tour-welcome-title">Estás listo para usar StarStudy</div>
        <div class="tour-welcome-subtitle">Si necesitás volver a ver este tour, hacé clic en "Replay Tour" desde el menú de perfil.</div>
      </div>`,
      buttons: [
        { text: '¡Empezar a Usar!', action: function () { this.complete(); }, classes: 'shepherd-button-primary' }
      ],
      cancelIcon: { enabled: true },
      classes: 'tour-welcome-step',
      scrollTo: false
    }
  ];

  // ====================================
  // Construir tour según rol
  // ====================================

  function buildStepsForRole(role) {
    let steps = [...commonSteps];

    switch (role) {
      case 'STUDENT':
        steps.splice(1, 0, ...studentSteps);
        break;
      case 'TEACHER':
        steps.splice(1, 0, ...teacherSteps);
        break;
      case 'STAFF':
        steps.splice(1, 0, ...staffSteps);
        break;
      case 'PROGRAMMER':
        steps.splice(1, 0, ...programmerSteps);
        break;
    }

    // Filter steps that don't have valid attachTo elements
    steps = steps.filter(function (step) {
      if (!step.attachTo) return true;
      if (typeof step.when === 'object' && step.when.show) return step.when.show();
      return elementExists(step.attachTo.element);
    });

    return steps;
  }

  // ====================================
  // Crear e inicializar tour
  // ====================================

  function createTour() {
    const role = getUserRole();
    const steps = buildStepsForRole(role);

    if (steps.length === 0) return null;

    const tour = new Shepherd.Tour({
      tourName: 'starstudy-' + role.toLowerCase(),
      useModalOverlay: true,
      defaultStepOptions: {
        classes: 'shepherd-theme-starstudy',
        scrollTo: { behavior: 'smooth', block: 'center' },
        cancelIcon: { enabled: true }
      },
      steps: steps,
      onComplete: function () {
        markTourCompleted();
        showReplayButton();
      },
      onCancel: function () {
        markTourCompleted();
        showReplayButton();
      }
    });

    // Add progress bar to each step
    tour.on('show', function (event) {
      var currentStep = event.step;
      var currentStepIndex = tour.steps.indexOf(currentStep);
      var totalSteps = tour.steps.length;

      // Update progress dots if header exists
      var progressContainer = document.querySelector('.shepherd-progress');
      if (progressContainer) {
        progressContainer.innerHTML = '';
        for (var i = 0; i < totalSteps; i++) {
          var dot = document.createElement('span');
          dot.className = 'shepherd-progress-dot';
          if (i < currentStepIndex) dot.classList.add('completed');
          if (i === currentStepIndex) dot.classList.add('active');
          progressContainer.appendChild(dot);
        }
      }
    });

    return tour;
  }

  // ====================================
  // Botón Replay Tour
  // ====================================

  function showReplayButton() {
    // Check if button already exists
    if (document.getElementById('btnReplayTour')) return;

    // Try to add to profile dropdown
    var profileDropdown = document.querySelector('.nav-item.dropdown:last-child .dropdown-menu');
    if (profileDropdown) {
      var li = document.createElement('li');
      li.innerHTML = '<hr class="dropdown-divider">';
      profileDropdown.appendChild(li);

      var replayLi = document.createElement('li');
      replayLi.innerHTML = '<a class="dropdown-item" href="#" id="btnReplayTour"><i class="bi bi-question-circle me-2"></i>Replay Tour</a>';
      profileDropdown.appendChild(replayLi);

      document.getElementById('btnReplayTour').addEventListener('click', function (e) {
        e.preventDefault();
        localStorage.removeItem(STORAGE_KEY);
        startTour(true);
      });
    }
  }

  // ====================================
  // Iniciar tour
  // ====================================

  function startTour(force) {
    if (!force && hasCompletedTour()) {
      showReplayButton();
      return;
    }

    // Wait for DOM and Bootstrap to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () { startTour(force); });
      return;
    }

    // Small delay to let Bootstrap initialize
    setTimeout(function () {
      var tour = createTour();
      if (tour) {
        tour.start();
        showReplayButton();
      }
    }, 1000);
  }

  // ====================================
  // Expose globally
  // ====================================

  window.StarStudyTour = {
    start: function () { startTour(true); },
    reset: function () {
      localStorage.removeItem(STORAGE_KEY);
      startTour(true);
    }
  };

  // Auto-start on first visit
  startTour(false);

})();
