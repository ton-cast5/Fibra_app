/**
 * TONYLEX Reports — diseño ejecutivo tipo informe corporativo.
 * Paleta alineada a FINNOVA / referencia profesional (azul + violeta).
 */
(function (global) {
    'use strict';

    var BRAND = {
        name: 'TONYLEX',
        tagline: 'Infraestructura de fibra optica',
        url: 'tonylex.app',
        contact: 'operaciones@tonylex.app',
        logoUrl: '/static/brand/logo-tonylex.png',
    };

    var C = {
        navy: [26, 59, 139],
        navyDeep: [15, 40, 95],
        violet: [108, 92, 239],
        purple: [159, 115, 210],
        sky: [133, 193, 233],
        skySoft: [232, 244, 252],
        ink: [30, 41, 59],
        muted: [100, 116, 139],
        light: [148, 163, 184],
        line: [191, 219, 254],
        white: [255, 255, 255],
        alt: [248, 250, 252],
        ok: [5, 150, 105],
        warn: [217, 119, 6],
        bad: [220, 38, 38],
    };

    var _logoDataUrl = null;
    var _logoPromise = null;

    function jsPDF() {
        return new global.jspdf.jsPDF({ unit: 'mm', format: 'a4' });
    }

    function fechaLarga() {
        return new Date().toLocaleDateString('es-MX', {
            timeZone: 'America/Mexico_City',
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        });
    }

    function fechaCorta() {
        return new Date().toLocaleDateString('es-MX', {
            timeZone: 'America/Mexico_City',
            day: 'numeric',
            month: 'long',
            year: 'numeric',
        });
    }

    function clean(text) {
        return String(text == null ? '' : text)
            .replace(/[^\x20-\x7E\u00A0-\u024F]/g, '')
            .trim();
    }

    function loadLogo() {
        if (_logoDataUrl) return Promise.resolve(_logoDataUrl);
        if (_logoPromise) return _logoPromise;
        _logoPromise = fetch(BRAND.logoUrl)
            .then(function (r) { return r.ok ? r.blob() : null; })
            .then(function (blob) {
                if (!blob) return null;
                return new Promise(function (resolve) {
                    var reader = new FileReader();
                    reader.onload = function () {
                        _logoDataUrl = reader.result;
                        resolve(_logoDataUrl);
                    };
                    reader.onerror = function () { resolve(null); };
                    reader.readAsDataURL(blob);
                });
            })
            .catch(function () { return null; });
        return _logoPromise;
    }

    function drawLogoMark(doc, x, y) {
        // Marca geometrica (por si falla el PNG)
        doc.setFillColor.apply(doc, C.violet);
        doc.roundedRect(x, y, 7.2, 7.2, 1.6, 1.6, 'F');
        doc.setFillColor.apply(doc, C.navy);
        doc.roundedRect(x + 3.2, y + 2.2, 7.2, 7.2, 1.6, 1.6, 'F');
    }

    function drawBrandHeader(doc, logo) {
        var pageW = doc.internal.pageSize.getWidth();
        if (logo) {
            try {
                doc.addImage(logo, 'PNG', 14, 10, 9, 9);
            } catch (e) {
                drawLogoMark(doc, 14, 10);
            }
        } else {
            drawLogoMark(doc, 14, 10);
        }
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(12);
        doc.setTextColor.apply(doc, C.navy);
        doc.text(BRAND.name, 26, 16);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7.5);
        doc.setTextColor.apply(doc, C.muted);
        doc.text(BRAND.tagline, 26, 20.5);
        return 28;
    }

    function drawMasthead(doc, subtitle) {
        var pageW = doc.internal.pageSize.getWidth();
        var cx = pageW / 2;

        doc.setDrawColor.apply(doc, C.navy);
        doc.setLineWidth(0.45);
        doc.line(48, 34, pageW - 48, 34);

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(28);
        doc.setTextColor.apply(doc, C.navy);
        doc.text('REPORTE', cx, 46, { align: 'center' });

        doc.line(48, 51, pageW - 48, 51);

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9);
        doc.setTextColor.apply(doc, C.navy);
        doc.text(clean(subtitle).toUpperCase(), cx, 58, { align: 'center' });
        return 66;
    }

    function drawFooter(doc) {
        var pageCount = doc.internal.getNumberOfPages();
        var pageW = doc.internal.pageSize.getWidth();
        var pageH = doc.internal.pageSize.getHeight();
        var i;
        for (i = 1; i <= pageCount; i++) {
            doc.setPage(i);
            doc.setDrawColor.apply(doc, C.navy);
            doc.setLineWidth(0.35);
            doc.line(14, pageH - 14, pageW - 14, pageH - 14);

            doc.setFont('helvetica', 'normal');
            doc.setFontSize(7.5);
            doc.setTextColor.apply(doc, C.navy);
            doc.text(BRAND.url, 14, pageH - 8);
            doc.text(fechaCorta(), pageW - 14, pageH - 8, { align: 'right' });
            doc.setTextColor.apply(doc, C.light);
            doc.text(String(i) + ' / ' + String(pageCount), pageW / 2, pageH - 8, { align: 'center' });
        }
    }

    function drawPageHeader(doc, title, logo) {
        drawBrandHeader(doc, logo);
        var pageW = doc.internal.pageSize.getWidth();
        doc.setDrawColor.apply(doc, C.line);
        doc.setLineWidth(0.4);
        doc.line(14, 24, pageW - 14, 24);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(11);
        doc.setTextColor.apply(doc, C.navy);
        doc.text(clean(title).toUpperCase(), 14, 31);
        return 38;
    }

    function wrapText(doc, text, maxW) {
        return doc.splitTextToSize(clean(text), maxW);
    }

    function drawSectionTitle(doc, x, y, title) {
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(12);
        doc.setTextColor.apply(doc, C.navy);
        doc.text(clean(title), x, y);
        return y + 6;
    }

    function drawProse(doc, x, y, maxW, paragraphs, fontSize) {
        fontSize = fontSize || 8.5;
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(fontSize);
        doc.setTextColor.apply(doc, C.ink);
        var yy = y;
        (paragraphs || []).forEach(function (p) {
            var lines = wrapText(doc, p, maxW);
            doc.text(lines, x, yy);
            yy += lines.length * (fontSize * 0.45) + 3.2;
        });
        return yy;
    }

    function drawTintBand(doc, y, h, fill) {
        var pageW = doc.internal.pageSize.getWidth();
        doc.setFillColor.apply(doc, fill || C.skySoft);
        doc.rect(0, y, pageW, h, 'F');
    }

    function drawGroupedBars(doc, opts) {
        var x = opts.x;
        var y = opts.y;
        var w = opts.w;
        var h = opts.h;
        var labels = opts.labels || [];
        var series = opts.series || []; // [{color, values:[]}]
        var maxVal = opts.max || 0;
        var i, s, v, groupW, barW, gap, gx, bx, bh, baseY;

        series.forEach(function (ser) {
            (ser.values || []).forEach(function (n) {
                if (n > maxVal) maxVal = n;
            });
        });
        if (maxVal <= 0) maxVal = 1;

        // grid
        doc.setDrawColor.apply(doc, C.line);
        doc.setLineWidth(0.2);
        for (i = 0; i <= 4; i++) {
            var gy = y + h - (h * i / 4);
            doc.line(x, gy, x + w, gy);
            doc.setFontSize(6.5);
            doc.setTextColor.apply(doc, C.light);
            doc.text(String(Math.round(maxVal * i / 4)), x - 2, gy + 1.2, { align: 'right' });
        }

        groupW = w / Math.max(labels.length, 1);
        barW = Math.min(4.2, (groupW - 4) / Math.max(series.length, 1));
        gap = 0.7;
        baseY = y + h;

        labels.forEach(function (label, gi) {
            gx = x + gi * groupW + groupW / 2;
            series.forEach(function (ser, si) {
                v = Number(ser.values[gi] || 0);
                bh = (v / maxVal) * (h - 2);
                bx = gx - ((series.length * barW + (series.length - 1) * gap) / 2) + si * (barW + gap);
                doc.setFillColor.apply(doc, ser.color);
                doc.roundedRect(bx, baseY - bh, barW, Math.max(bh, 0.4), 0.4, 0.4, 'F');
            });
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(6.5);
            doc.setTextColor.apply(doc, C.muted);
            doc.text(clean(label), gx, baseY + 4, { align: 'center' });
        });
    }

    function drawDonut(doc, opts) {
        var cx = opts.cx;
        var cy = opts.cy;
        var r = opts.r || 28;
        var slices = opts.slices || [];
        var total = 0;
        slices.forEach(function (s) { total += Number(s.value) || 0; });
        if (total <= 0) {
            doc.setDrawColor.apply(doc, C.line);
            doc.setLineWidth(6);
            doc.circle(cx, cy, r - 3, 'S');
            return;
        }

        // Approximate donut with colored arcs via thin wedges of triangles/rects
        // jsPDF lacks arc fill; draw stacked pie wedges as lines around circumference
        var start = -Math.PI / 2;
        var step = Math.PI / 90;
        slices.forEach(function (slice) {
            var portion = (Number(slice.value) || 0) / total;
            var sweep = portion * Math.PI * 2;
            var a = start;
            var end = start + sweep;
            doc.setDrawColor.apply(doc, slice.color);
            doc.setLineWidth(7.5);
            while (a < end) {
                var a2 = Math.min(a + step, end);
                var x1 = cx + Math.cos(a) * (r - 3.5);
                var y1 = cy + Math.sin(a) * (r - 3.5);
                var x2 = cx + Math.cos(a2) * (r - 3.5);
                var y2 = cy + Math.sin(a2) * (r - 3.5);
                doc.line(x1, y1, x2, y2);
                a = a2;
            }
            start = end;
        });

        doc.setFillColor.apply(doc, C.white);
        doc.circle(cx, cy, r - 9, 'F');

        if (opts.centerLabel) {
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(11);
            doc.setTextColor.apply(doc, C.navy);
            doc.text(String(opts.centerLabel), cx, cy + 1, { align: 'center' });
        }
        if (opts.centerSub) {
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(7);
            doc.setTextColor.apply(doc, C.muted);
            doc.text(String(opts.centerSub), cx, cy + 6, { align: 'center' });
        }
    }

    function drawKpiStack(doc, x, y, items) {
        var yy = y;
        (items || []).forEach(function (item) {
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(22);
            doc.setTextColor.apply(doc, item.color || C.navy);
            doc.text(String(item.value), x, yy);

            doc.setFont('helvetica', 'normal');
            doc.setFontSize(8);
            doc.setTextColor.apply(doc, C.ink);
            var lines = wrapText(doc, item.text || '', 78);
            doc.text(lines, x + 28, yy - 5);
            yy += Math.max(16, lines.length * 4 + 8);
        });
        return yy;
    }

    function tableStyles(overrides) {
        return Object.assign({
            theme: 'plain',
            headStyles: {
                fillColor: C.navy,
                textColor: C.white,
                fontSize: 8,
                fontStyle: 'bold',
                halign: 'left',
                cellPadding: { top: 3.2, bottom: 3.2, left: 3, right: 3 },
            },
            bodyStyles: {
                fontSize: 7.8,
                textColor: C.ink,
                cellPadding: { top: 2.8, bottom: 2.8, left: 3, right: 3 },
            },
            alternateRowStyles: { fillColor: C.alt },
            styles: {
                lineColor: C.line,
                lineWidth: 0.15,
            },
            margin: { left: 14, right: 14 },
        }, overrides || {});
    }

    function ensureSpace(doc, y, need, title, logo) {
        var pageH = doc.internal.pageSize.getHeight();
        if (y + need < pageH - 20) return y;
        doc.addPage();
        return drawPageHeader(doc, title, logo);
    }

    function groupByPlan(clientes) {
        var map = {};
        (clientes || []).forEach(function (c) {
            var key = clean(c.plan) || 'Sin plan';
            map[key] = (map[key] || 0) + 1;
        });
        var entries = Object.keys(map).map(function (k) { return { label: k, value: map[k] }; });
        entries.sort(function (a, b) { return b.value - a.value; });
        return entries.slice(0, 6);
    }

    function occupancyBuckets(naps) {
        var buckets = { optimo: 0, moderado: 0, critico: 0 };
        (naps || []).forEach(function (n) {
            if (n.tipo_caja === 'empalme') return;
            var pct = Number(n.porcentaje_uso);
            if (!isFinite(pct) && n.puertos_total) {
                pct = ((n.clientes_count || n.puertos_ocupados || 0) / n.puertos_total) * 100;
            }
            pct = pct || 0;
            if (pct >= 80) buckets.critico++;
            else if (pct >= 50) buckets.moderado++;
            else buckets.optimo++;
        });
        return buckets;
    }

    // ---------- REPORT BUILDERS ----------

    async function reportClientes(clientes) {
        var logo = await loadLogo();
        var doc = jsPDF();
        var list = Array.isArray(clientes) ? clientes : [];
        var total = list.length;
        var activos = list.filter(function (c) { return !!c.activo; }).length;
        var inactivos = total - activos;
        var pctAct = total ? Math.round((activos / total) * 1000) / 10 : 0;
        var pctIna = total ? Math.round((inactivos / total) * 1000) / 10 : 0;
        var planes = groupByPlan(list);
        var pageW = doc.internal.pageSize.getWidth();

        drawBrandHeader(doc, logo);
        drawMasthead(doc, 'Cartera de clientes · estado operativo');

        // Section 1: prose + bars by plan
        var y = 70;
        drawSectionTitle(doc, 14, y, 'Panorama de la cartera');
        y = drawProse(doc, 14, y + 6, 88, [
            'Este documento consolida la base de clientes registrados en TONYLEX, con enfasis en activacion, planes contratados y datos de contacto para operacion en campo.',
            'Los indicadores se calculan en tiempo real al momento de la exportacion. Utilice la tabla detallada para auditoria y seguimiento comercial.',
            'Priorice la reactivacion de cuentas inactivas y valide que cada servicio activo tenga NAP y plan asignados correctamente.'
        ], 8.2);

        var planLabels = planes.length ? planes.map(function (p) {
            return p.label.length > 9 ? p.label.slice(0, 9) + '.' : p.label;
        }) : ['Sin datos'];
        var planAct = planes.map(function (p) {
            return list.filter(function (c) { return (clean(c.plan) || 'Sin plan') === p.label && c.activo; }).length;
        });
        var planIna = planes.map(function (p) {
            return list.filter(function (c) { return (clean(c.plan) || 'Sin plan') === p.label && !c.activo; }).length;
        });
        drawGroupedBars(doc, {
            x: 112, y: 72, w: 80, h: 42,
            labels: planLabels,
            series: planes.length ? [
                { color: C.sky, values: planIna },
                { color: C.purple, values: planAct },
                { color: C.navy, values: planes.map(function (p) { return p.value; }) },
            ] : [{ color: C.navy, values: [0] }],
        });
        doc.setFontSize(7);
        doc.setTextColor.apply(doc, C.muted);
        doc.text('Por plan: inactivos · activos · total', 112, 120);

        // Tint band
        var bandY = 128;
        drawTintBand(doc, bandY, 36, C.skySoft);
        drawSectionTitle(doc, 14, bandY + 10, 'Lectura operativa');
        drawProse(doc, 14, bandY + 16, pageW - 28, [
            'Activos: ' + activos + ' de ' + total + ' (' + pctAct + '%). Inactivos: ' + inactivos + ' (' + pctIna + '%). ' +
            'Mantenga la tasa de activacion por encima del 90% y documente bajas con motivo comercial o tecnico.'
        ], 8.5);

        // Donut + KPIs
        y = bandY + 48;
        drawDonut(doc, {
            cx: 48, cy: y + 28, r: 26,
            slices: [
                { value: activos, color: C.navy },
                { value: inactivos, color: C.purple },
            ],
            centerLabel: pctAct + '%',
            centerSub: 'activos',
        });
        drawKpiStack(doc, 90, y + 12, [
            { value: pctAct + '%', color: C.navy, text: 'Clientes activos sobre el total de la cartera al corte del reporte.' },
            { value: pctIna + '%', color: C.purple, text: 'Cuentas inactivas que requieren revision comercial o tecnica.' },
            { value: String(planes.length), color: C.sky, text: 'Planes distintos detectados en la base exportada.' },
        ]);

        // Detail table
        doc.addPage();
        y = drawPageHeader(doc, 'Detalle de clientes', logo);
        doc.autoTable({
            head: [['ID', 'NOMBRE', 'DIRECCION', 'PLAN', 'ESTADO', 'CONTACTO', 'NAP']],
            body: list.map(function (c) {
                return [
                    c.id,
                    clean(c.nombre),
                    clean(c.direccion),
                    clean(c.plan) || '—',
                    c.activo ? 'ACTIVO' : 'INACTIVO',
                    clean(c.contacto) || '—',
                    clean(c.nap_nombre) || '—',
                ];
            }),
            startY: y,
            ...tableStyles({
                didParseCell: function (d) {
                    if (d.section === 'body' && d.column.index === 4) {
                        var raw = String(d.cell.raw || '');
                        d.cell.styles.fontStyle = 'bold';
                        d.cell.styles.textColor = raw === 'ACTIVO' ? C.ok : C.bad;
                    }
                },
            }),
        });

        drawFooter(doc);
        doc.save('TONYLEX_Clientes_' + new Date().toISOString().slice(0, 10) + '.pdf');
    }

    async function reportNaps(naps) {
        var logo = await loadLogo();
        var doc = jsPDF();
        var list = Array.isArray(naps) ? naps : [];
        var dist = list.filter(function (n) { return n.tipo_caja !== 'empalme'; });
        var buckets = occupancyBuckets(list);
        var totalPuertos = dist.reduce(function (a, n) { return a + (n.puertos_total || 0); }, 0);
        var usados = dist.reduce(function (a, n) { return a + (n.clientes_count || n.puertos_ocupados || 0); }, 0);
        var pct = totalPuertos ? Math.round((usados / totalPuertos) * 1000) / 10 : 0;
        var pageW = doc.internal.pageSize.getWidth();

        drawBrandHeader(doc, logo);
        drawMasthead(doc, 'Cajas NAP · capacidad y ocupacion');

        var y = 70;
        drawSectionTitle(doc, 14, y, 'Salud de la red de acceso');
        drawProse(doc, 14, y + 6, 88, [
            'El reporte resume la capacidad instalada en cajas de distribucion, el uso real de puertos y la concentracion de riesgo por saturacion.',
            'Las cajas en nivel critico (>80%) deben priorizarse para expansion o redistribucion de clientes.',
            'Los empalmes se listan en reportes de tipificacion; aqui el foco es capacidad util de acceso.'
        ], 8.2);

        drawGroupedBars(doc, {
            x: 112, y: 72, w: 80, h: 42,
            labels: ['Optimo', 'Moderado', 'Critico'],
            series: [
                { color: C.ok, values: [buckets.optimo, 0, 0] },
                { color: C.warn, values: [0, buckets.moderado, 0] },
                { color: C.bad, values: [0, 0, buckets.critico] },
            ],
            max: Math.max(buckets.optimo, buckets.moderado, buckets.critico, 1),
        });

        var bandY = 128;
        drawTintBand(doc, bandY, 34, C.skySoft);
        drawSectionTitle(doc, 14, bandY + 10, 'Capacidad consolidada');
        drawProse(doc, 14, bandY + 16, pageW - 28, [
            usados + ' puertos en uso de ' + totalPuertos + ' instalados (' + pct + '%). ' +
            'Criticas: ' + buckets.critico + ' · Moderadas: ' + buckets.moderado + ' · Optimas: ' + buckets.optimo + '.'
        ], 8.5);

        y = bandY + 46;
        drawDonut(doc, {
            cx: 48, cy: y + 28, r: 26,
            slices: [
                { value: buckets.optimo, color: C.ok },
                { value: buckets.moderado, color: C.warn },
                { value: buckets.critico, color: C.bad },
            ],
            centerLabel: pct + '%',
            centerSub: 'ocupacion',
        });
        drawKpiStack(doc, 90, y + 10, [
            { value: pct + '%', color: C.navy, text: 'Ocupacion media de puertos en cajas de distribucion.' },
            { value: String(buckets.critico), color: C.bad, text: 'Cajas en nivel critico que requieren accion inmediata.' },
            { value: String(dist.length), color: C.violet, text: 'Cajas NAP de distribucion contempladas en el analisis.' },
        ]);

        doc.addPage();
        y = drawPageHeader(doc, 'Inventario de cajas NAP', logo);
        doc.autoTable({
            head: [['ID', 'NOMBRE', 'TIPO', 'PUERTOS', 'USADOS', 'OCUPACION', 'HILO', 'MODELO']],
            body: list.map(function (n) {
                var u = n.clientes_count || n.puertos_ocupados || 0;
                var p = n.puertos_total > 0 ? Math.round((u / n.puertos_total) * 100) : 0;
                return [
                    n.id,
                    clean(n.nombre),
                    clean(n.tipo_caja_display || n.tipo_caja || '—'),
                    n.puertos_total || 0,
                    u,
                    p + '%',
                    clean(n.hilo_conexion) || '—',
                    clean(n.nap_model_nombre) || '—',
                ];
            }),
            startY: y,
            ...tableStyles({
                didParseCell: function (d) {
                    if (d.section === 'body' && d.column.index === 5) {
                        var p = parseInt(String(d.cell.raw), 10) || 0;
                        d.cell.styles.fontStyle = 'bold';
                        d.cell.styles.textColor = p >= 80 ? C.bad : (p >= 50 ? C.warn : C.ok);
                    }
                },
            }),
        });

        drawFooter(doc);
        doc.save('TONYLEX_NAPs_' + new Date().toISOString().slice(0, 10) + '.pdf');
    }

    async function reportTipos(naps) {
        var logo = await loadLogo();
        var doc = jsPDF();
        var list = Array.isArray(naps) ? naps : [];
        var dist = list.filter(function (n) { return n.tipo_caja === 'distribucion'; });
        var emp = list.filter(function (n) { return n.tipo_caja === 'empalme'; });
        var total = list.length || 1;
        var pctD = Math.round((dist.length / total) * 1000) / 10;
        var pctE = Math.round((emp.length / total) * 1000) / 10;
        var pageW = doc.internal.pageSize.getWidth();

        drawBrandHeader(doc, logo);
        drawMasthead(doc, 'Distribucion y empalmes · tipificacion de red');

        var y = 70;
        drawSectionTitle(doc, 14, y, 'Composicion de la red');
        drawProse(doc, 14, y + 6, 88, [
            'Clasificacion de cajas por rol funcional: acceso (distribucion/NAP) frente a nodos de empalme.',
            'Una red equilibrada mantiene suficiente capacidad de acceso y empalmes estrategicos para continuidad del backbone.',
            'Revise modelos y hilos en el detalle tabular para cuadrar inventario fisico vs sistema.'
        ], 8.2);

        drawGroupedBars(doc, {
            x: 112, y: 72, w: 80, h: 42,
            labels: ['NAP', 'Empalme'],
            series: [
                { color: C.sky, values: [dist.length, 0] },
                { color: C.purple, values: [0, emp.length] },
                { color: C.navy, values: [dist.length, emp.length] },
            ],
            max: Math.max(dist.length, emp.length, 1),
        });

        var bandY = 128;
        drawTintBand(doc, bandY, 32, C.skySoft);
        drawSectionTitle(doc, 14, bandY + 10, 'Balance tipologico');
        drawProse(doc, 14, bandY + 16, pageW - 28, [
            'Distribucion: ' + dist.length + ' (' + pctD + '%) · Empalmes: ' + emp.length + ' (' + pctE + '%) · Total: ' + list.length + ' cajas.'
        ], 8.5);

        y = bandY + 44;
        drawDonut(doc, {
            cx: 48, cy: y + 28, r: 26,
            slices: [
                { value: dist.length, color: C.navy },
                { value: emp.length, color: C.purple },
            ],
            centerLabel: String(list.length),
            centerSub: 'cajas',
        });
        drawKpiStack(doc, 90, y + 12, [
            { value: pctD + '%', color: C.navy, text: 'Participacion de cajas de distribucion (NAP) en la red.' },
            { value: pctE + '%', color: C.purple, text: 'Participacion de empalmes sobre el inventario total.' },
            { value: String(list.length), color: C.sky, text: 'Elementos tipificados al momento de la exportacion.' },
        ]);

        function tableTipo(titulo, rows) {
            doc.addPage();
            var start = drawPageHeader(doc, titulo, logo);
            if (!rows.length) {
                doc.setFontSize(9);
                doc.setTextColor.apply(doc, C.muted);
                doc.text('Sin registros de este tipo.', 14, start + 6);
                return;
            }
            doc.autoTable({
                head: [['ID', 'NOMBRE', 'MODELO', 'PUERTOS', 'USADOS', 'OCUPACION', 'HILO']],
                body: rows.map(function (n) {
                    var u = n.clientes_count || n.puertos_ocupados || 0;
                    var p = n.puertos_total > 0 ? Math.round((u / n.puertos_total) * 100) : 0;
                    return [n.id, clean(n.nombre), clean(n.nap_model_nombre) || '—', n.puertos_total || 0, u, p + '%', clean(n.hilo_conexion) || '—'];
                }),
                startY: start,
                ...tableStyles(),
            });
        }

        tableTipo('Cajas de distribucion (NAP)', dist);
        tableTipo('Cajas de empalme', emp);

        drawFooter(doc);
        doc.save('TONYLEX_Tipos_Caja_' + new Date().toISOString().slice(0, 10) + '.pdf');
    }

    async function reportInventarioCompleto(clientes, naps) {
        var logo = await loadLogo();
        var doc = jsPDF();
        var cli = Array.isArray(clientes) ? clientes : [];
        var nap = Array.isArray(naps) ? naps : [];
        var activos = cli.filter(function (c) { return !!c.activo; }).length;
        var buckets = occupancyBuckets(nap);
        var pageW = doc.internal.pageSize.getWidth();

        drawBrandHeader(doc, logo);
        drawMasthead(doc, 'Inventario completo · infraestructura y cartera');

        var y = 70;
        drawSectionTitle(doc, 14, y, 'Resumen ejecutivo');
        drawProse(doc, 14, y + 6, pageW - 28, [
            'Documento maestro generado por TONYLEX con la fotografia operativa de clientes y cajas. Incluye indicadores visuales, tipificacion y anexos tabulares para auditoria.',
            'Fecha de emision: ' + fechaLarga() + '. Uso interno y confidencial.'
        ], 8.5);

        y = 100;
        drawGroupedBars(doc, {
            x: 14, y: y, w: 95, h: 40,
            labels: ['Clientes', 'Activos', 'Cajas', 'Criticas'],
            series: [
                { color: C.sky, values: [cli.length, 0, 0, 0] },
                { color: C.purple, values: [0, activos, 0, 0] },
                { color: C.navy, values: [0, 0, nap.length, buckets.critico] },
            ],
            max: Math.max(cli.length, activos, nap.length, buckets.critico, 1),
        });

        drawDonut(doc, {
            cx: 150, cy: y + 22, r: 24,
            slices: [
                { value: buckets.optimo, color: C.ok },
                { value: buckets.moderado, color: C.warn },
                { value: buckets.critico, color: C.bad },
            ],
            centerLabel: String(nap.length),
            centerSub: 'cajas',
        });

        var bandY = 152;
        drawTintBand(doc, bandY, 28, C.skySoft);
        drawProse(doc, 14, bandY + 10, pageW - 28, [
            'Cartera: ' + cli.length + ' clientes (' + activos + ' activos). Red: ' + nap.length + ' cajas · ' + buckets.critico + ' en ocupacion critica.'
        ], 8.5);

        // Reuse table pages via internal helpers
        doc.addPage();
        y = drawPageHeader(doc, 'Anexo A · Clientes', logo);
        doc.autoTable({
            head: [['ID', 'NOMBRE', 'PLAN', 'ESTADO', 'NAP', 'CONTACTO']],
            body: cli.map(function (c) {
                return [c.id, clean(c.nombre), clean(c.plan) || '—', c.activo ? 'ACTIVO' : 'INACTIVO', clean(c.nap_nombre) || '—', clean(c.contacto) || '—'];
            }),
            startY: y,
            ...tableStyles({
                didParseCell: function (d) {
                    if (d.section === 'body' && d.column.index === 3) {
                        d.cell.styles.fontStyle = 'bold';
                        d.cell.styles.textColor = String(d.cell.raw) === 'ACTIVO' ? C.ok : C.bad;
                    }
                },
            }),
        });

        doc.addPage();
        y = drawPageHeader(doc, 'Anexo B · Cajas', logo);
        doc.autoTable({
            head: [['ID', 'NOMBRE', 'TIPO', 'PUERTOS', 'USADOS', 'OCUPACION', 'HILO']],
            body: nap.map(function (n) {
                var u = n.clientes_count || n.puertos_ocupados || 0;
                var p = n.puertos_total > 0 ? Math.round((u / n.puertos_total) * 100) : 0;
                return [n.id, clean(n.nombre), clean(n.tipo_caja_display || n.tipo_caja || '—'), n.puertos_total || 0, u, p + '%', clean(n.hilo_conexion) || '—'];
            }),
            startY: y,
            ...tableStyles(),
        });

        drawFooter(doc);
        doc.save('TONYLEX_Inventario_Completo_' + new Date().toISOString().slice(0, 10) + '.pdf');
    }

    async function reportAsistencia(payload) {
        var logo = await loadLogo();
        var doc = jsPDF();
        var res = (payload && payload.resumen) || {};
        var periodo = (payload && payload.periodo) || {};
        var registros = (payload && payload.registros) || [];
        var entradas = res.entradas_periodo || 0;
        var salidas = res.salidas_periodo || 0;
        var totalMov = entradas + salidas || 1;
        var pctE = Math.round((entradas / totalMov) * 1000) / 10;
        var pctS = Math.round((salidas / totalMov) * 1000) / 10;
        var pageW = doc.internal.pageSize.getWidth();

        drawBrandHeader(doc, logo);
        drawMasthead(doc, 'Asistencia laboral · ' + (periodo.desde || '') + ' al ' + (periodo.hasta || ''));

        var y = 70;
        drawSectionTitle(doc, 14, y, 'Control de jornada');
        drawProse(doc, 14, y + 6, 88, [
            'Consolidado de entradas y salidas del personal activo. Sirve para cuadrar presencia en campo, turnos y cumplimiento operativo.',
            'El detalle cronologico permite auditoria por trabajador y tipo de movimiento.',
            'Periodo analizado: ultimos ' + (periodo.dias || 30) + ' dias.'
        ], 8.2);

        drawGroupedBars(doc, {
            x: 112, y: 72, w: 80, h: 42,
            labels: ['Entradas', 'Salidas', 'Hoy in', 'Hoy out'],
            series: [
                { color: C.sky, values: [entradas, 0, res.entradas_hoy || 0, 0] },
                { color: C.purple, values: [0, salidas, 0, res.salidas_hoy || 0] },
                { color: C.navy, values: [entradas, salidas, res.entradas_hoy || 0, res.salidas_hoy || 0] },
            ],
            max: Math.max(entradas, salidas, res.entradas_hoy || 0, res.salidas_hoy || 0, 1),
        });

        var bandY = 128;
        drawTintBand(doc, bandY, 34, C.skySoft);
        drawSectionTitle(doc, 14, bandY + 10, 'Indicadores del periodo');
        drawProse(doc, 14, bandY + 16, pageW - 28, [
            'Personal: ' + (res.total_trabajadores || 0) +
            ' · Registros: ' + (res.registros_periodo || 0) +
            ' · Dentro hoy: ' + (res.dentro_hoy || 0) +
            ' · Movimientos hoy: ' + ((res.entradas_hoy || 0) + (res.salidas_hoy || 0))
        ], 8.5);

        y = bandY + 46;
        drawDonut(doc, {
            cx: 48, cy: y + 28, r: 26,
            slices: [
                { value: entradas, color: C.navy },
                { value: salidas, color: C.purple },
            ],
            centerLabel: String(res.registros_periodo || 0),
            centerSub: 'movs',
        });
        drawKpiStack(doc, 90, y + 12, [
            { value: pctE + '%', color: C.navy, text: 'Entradas respecto al total de movimientos del periodo.' },
            { value: pctS + '%', color: C.purple, text: 'Salidas registradas en el mismo intervalo de analisis.' },
            { value: String(res.dentro_hoy || 0), color: C.sky, text: 'Colaboradores actualmente en jornada al corte de hoy.' },
        ]);

        doc.addPage();
        y = drawPageHeader(doc, 'Registro detallado de asistencia', logo);
        if (!registros.length) {
            doc.setFontSize(9);
            doc.setTextColor.apply(doc, C.muted);
            doc.text('No hay registros en el periodo seleccionado.', 14, y + 8);
        } else {
            doc.autoTable({
                head: [['ID', 'TRABAJADOR', 'TIPO', 'FECHA', 'HORA']],
                body: registros.map(function (r) {
                    return [r.id, clean(r.trabajador), clean((r.tipo_label || r.tipo || '').toUpperCase()), r.fecha || '', r.hora || ''];
                }),
                startY: y,
                ...tableStyles({
                    didParseCell: function (d) {
                        if (d.section === 'body' && d.column.index === 2) {
                            var val = String(d.cell.raw || '').toUpperCase();
                            d.cell.styles.fontStyle = 'bold';
                            d.cell.styles.textColor = val.indexOf('ENTRADA') >= 0 ? C.ok : C.navy;
                        }
                    },
                }),
            });
        }

        drawFooter(doc);
        doc.save('TONYLEX_Asistencia_' + new Date().toISOString().slice(0, 10) + '.pdf');
    }

    global.TonylexReports = {
        brand: BRAND,
        reportClientes: reportClientes,
        reportNaps: reportNaps,
        reportTipos: reportTipos,
        reportInventarioCompleto: reportInventarioCompleto,
        reportAsistencia: reportAsistencia,
    };
})(typeof window !== 'undefined' ? window : this);
