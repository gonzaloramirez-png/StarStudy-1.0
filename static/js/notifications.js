/* StarStudy - Alertas del navegador (Push).
 *
 * Usa la API de Notificaciones del navegador para recordar
 * tareas urgentes y hábitos del día, sin necesidad de servicios externos.
 * El botón de la barra de navegación (#push-toggle) activa/desactiva.
 */
(function () {
    'use strict';

    var CHECK_INTERVAL = 60 * 1000; // cada 1 minuto
    var COOKIE_NAME = 'starstudy_push_optin';
    var HABIT_WINDOW = 5; // minutos de tolerancia para hábitos

    function registerSW() {
        if ('serviceWorker' in navigator && window.location.protocol.indexOf('https') === 0 ||
            window.location.hostname === '127.0.0.1' ||
            window.location.hostname === 'localhost') {
            navigator.serviceWorker.register('/service-worker.js').catch(function () {});
        }
    }

    function isOptedIn() {
        return document.cookie.indexOf(COOKIE_NAME + '=1') !== -1;
    }

    function setOptIn() {
        document.cookie = COOKIE_NAME + '=1; max-age=' + (60 * 60 * 24 * 365) + '; path=/';
    }

    function supported() {
        return 'Notification' in window;
    }

    function updateButton(state) {
        var btn = document.getElementById('push-toggle');
        if (!btn) return;
        btn.classList.remove('d-none');
        if (state === 'granted') {
            btn.setAttribute('aria-label', 'Alertas del navegador activadas');
            btn.title = 'Alertas del navegador activadas';
            btn.innerHTML = '<i class="bi bi-bell-fill"></i>';
        } else {
            btn.setAttribute('aria-label', 'Activar alertas del navegador');
            btn.title = 'Activar alertas del navegador';
            btn.innerHTML = '<i class="bi bi-bell-slash"></i>';
        }
    }

    function requestPermission() {
        if (!supported()) return;
        Notification.requestPermission().then(function (permission) {
            if (permission === 'granted') {
                setOptIn();
                updateButton('granted');
                fireImmediate();
            } else {
                updateButton('denied');
            }
        });
    }

    function showNotification(title, body, url) {
        if (!supported() || Notification.permission !== 'granted') return;
        // Solo molestar cuando la pestaña no está en foco
        if (!document.hidden && !sessionStorage.getItem('starstudy_push_test')) return;
        var opts = { body: body, icon: '/static/img/starry-night.jpg', tag: 'starstudy' };
        var n = new Notification(title, opts);
        n.onclick = function () {
            n.close();
            window.focus();
            if (url) window.location.href = url;
        };
        n.onshow = function () { setTimeout(function () { n.close(); }, 10000); };
    }

    function fireImmediate() {
        fetch('/api/push-status/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.push_enabled === false) return;
                var now = new Date();
                var cur = now.getHours() * 60 + now.getMinutes();

                (data.urgent || []).forEach(function (t) {
                    showNotification('Tarea urgente: ' + t.title, 'Vence: ' + t.deadline, '/tasks/' + t.pk + '/');
                });

                (data.habits || []).forEach(function (h) {
                    var start = h.start_time.split(':');
                    var startMin = parseInt(start[0], 10) * 60 + parseInt(start[1], 10);
                    if (Math.abs(cur - startMin) <= HABIT_WINDOW) {
                        showNotification('¡Hora de comenzar "' + h.title + '"!', 'Tu Misión Principal te espera.', '/habitos/');
                    }
                });
            })
            .catch(function () {});
    }

    document.addEventListener('DOMContentLoaded', function () {
        registerSW();

        var btn = document.getElementById('push-toggle');
        if (!btn || !supported()) return;

        if (Notification.permission === 'granted') {
            setOptIn();
            updateButton('granted');
            setInterval(function () { fireImmediate(); }, CHECK_INTERVAL);
        } else if (isOptedIn()) {
            requestPermission();
        } else {
            updateButton('denied');
            btn.addEventListener('click', requestPermission);
        }
    });
})();
