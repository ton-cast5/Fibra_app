/**
 * Reloj y fechas en zona horaria de México (America/Mexico_City).
 */
(function (global) {
    var TZ = 'America/Mexico_City';

    function partesMexico(date) {
        var d = date || new Date();
        var parts = {};
        new Intl.DateTimeFormat('en-US', {
            timeZone: TZ,
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        }).formatToParts(d).forEach(function (p) {
            if (p.type !== 'literal') parts[p.type] = p.value;
        });
        return parts;
    }

    function pad(n) {
        return String(n).padStart(2, '0');
    }

    function fechaDisplay(date) {
        var p = partesMexico(date);
        return pad(p.day) + '/' + pad(p.month) + '/' + p.year;
    }

    function horaDisplay(date) {
        var p = partesMexico(date);
        return pad(p.hour) + ':' + pad(p.minute) + ':' + pad(p.second);
    }

    function isoMexico(date) {
        var p = partesMexico(date);
        return p.year + '-' + p.month + '-' + p.day + 'T' + p.hour + ':' + p.minute + ':' + p.second;
    }

    function iniciarReloj(fechaEl, horaEl, hiddenEl) {
        if (!fechaEl || !horaEl) return;

        function tick() {
            var now = new Date();
            fechaEl.textContent = fechaDisplay(now);
            horaEl.textContent = horaDisplay(now);
            if (hiddenEl) hiddenEl.value = isoMexico(now);
        }

        tick();
        setInterval(tick, 1000);
    }

    global.FibraTiempo = {
        TZ: TZ,
        partesMexico: partesMexico,
        fechaDisplay: fechaDisplay,
        horaDisplay: horaDisplay,
        isoMexico: isoMexico,
        iniciarReloj: iniciarReloj
    };
})(typeof window !== 'undefined' ? window : this);
