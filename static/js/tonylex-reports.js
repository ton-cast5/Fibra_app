/**
 * TONYLEX Reports — informe ejecutivo (layout tipo reporte corporativo).
 * Tablas sin IDs, tipografia contenida, graficas cuadradas y sin desborde.
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
        royal: [52, 87, 213],
        violet: [108, 92, 239],
        purple: [159, 115, 210],
        sky: [133, 193, 233],
        skySoft: [232, 244, 252],
        ink: [30, 41, 59],
        muted: [100, 116, 139],
        light: [148, 163, 184],
        line: [191, 219, 254],
        rule: [203, 213, 225],
        white: [255, 255, 255],
        alt: [246, 249, 252],
        ok: [5, 150, 105],
        warn: [217, 119, 6],
        bad: [220, 38, 38],
    };

    var PAGE = { w: 210, h: 297, ml: 14, mr: 14, mt: 12, mb: 18 };
    PAGE.contentW = PAGE.w - PAGE.ml - PAGE.mr;

    var _logoDataUrl = null;
    var _logoPromise = null;

    function createDoc() {
        return new global.jspdf.jsPDF({ unit: 'mm', format: 'a4', compress: true });
    }

    function fechaLarga() {
        return new Date().toLocaleDateString('es-MX', {
            timeZone: 'America/Mexico_City',
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
        });
    }

    function fechaCorta() {
        return new Date().toLocaleDateString('es-MX', {
            timeZone: 'America/Mexico_City',
            day: 'numeric', month: 'long', year: 'numeric',
        });
    }

    function clean(text) {
        return String(text == null ? '' : text)
            .replace(/[\u0000-\u001F\u007F]/g, '')
            .replace(/[^\x20-\x7E\u00A0-\u024F]/g, '')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function clip(text, max) {
        var t = clean(text);
        if (t.length <= max) return t;
        return t.slice(0, Math.max(0, max - 1)) + '.';
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
                    reader.onload = function () { _logoDataUrl = reader.result; resolve(_logoDataUrl); };
                    reader.onerror = function () { resolve(null); };
                    reader.readAsDataURL(blob);
                });
            })
            .catch(function () { return null; });
        return _logoPromise;
    }

    function drawLogoMark(doc, x, y) {
        doc.setFillColor.apply(doc, C.purple);
        doc.roundedRect(x, y, 6.8, 6.8, 1.5, 1.5, 'F');
        doc.setFillColor.apply(doc, C.navy);
        doc.roundedRect(x + 3.0, y + 2.0, 6.8, 6.8, 1.5, 1.5, 'F');
    }

    function drawBrandHeader(doc, logo) {
        if (logo) {
            try { doc.addImage(logo, 'PNG', PAGE.ml, 9, 8.5, 8.5); }
            catch (e) { drawLogoMark(doc, PAGE.ml, 9.2); }
        } else {
            drawLogoMark(doc, PAGE.ml, 9.2);
        }
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(11.5);
        doc.setTextColor.apply(doc, C.navy);
        doc.text(BRAND.name, PAGE.ml + 11, 14.2);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7);
        doc.setTextColor.apply(doc, C.muted);
        doc.text(BRAND.tagline, PAGE.ml + 11, 18.4);
        return 24;
    }

    function drawMasthead(doc, subtitle) {
        var cx = PAGE.w / 2;
        var lineL = 52;
        var lineR = PAGE.w - 52;

        doc.setDrawColor.apply(doc, C.navy);
        doc.setLineWidth(0.4);
        doc.line(lineL, 30, lineR, 30);

        doc.setFont('helvetica', 'bold');
        doc.setFontSize(26);
        doc.setTextColor.apply(doc, C.navy);
        doc.text('REPORTE', cx, 41, { align: 'center' });

        doc.line(lineL, 46, lineR, 46);

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8.5);
        doc.setTextColor.apply(doc, C.royal);
        var sub = clip(String(subtitle || '').toUpperCase(), 78);
        doc.text(sub, cx, 53, { align: 'center' });
        return 60;
    }

    function drawFooter(doc) {
        var pages = doc.internal.getNumberOfPages();
        for (var i = 1; i <= pages; i++) {
            doc.setPage(i);
            doc.setDrawColor.apply(doc, C.navy);
            doc.setLineWidth(0.3);
            doc.line(PAGE.ml, PAGE.h - 12, PAGE.w - PAGE.mr, PAGE.h - 12);

            doc.setFont('helvetica', 'normal');
            doc.setFontSize(7.2);
            doc.setTextColor.apply(doc, C.navy);
            doc.text(BRAND.url, PAGE.ml, PAGE.h - 7);
            doc.text(fechaCorta(), PAGE.w - PAGE.mr, PAGE.h - 7, { align: 'right' });
            doc.setTextColor.apply(doc, C.light);
            doc.text(String(i) + ' / ' + String(pages), PAGE.w / 2, PAGE.h - 7, { align: 'center' });
        }
    }

    function drawPageHeader(doc, title, logo) {
        drawBrandHeader(doc, logo);
        doc.setDrawColor.apply(doc, C.line);
        doc.setLineWidth(0.35);
        doc.line(PAGE.ml, 22.5, PAGE.w - PAGE.mr, 22.5);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(10);
        doc.setTextColor.apply(doc, C.navy);
        doc.text(clip(String(title || '').toUpperCase(), 70), PAGE.ml, 29);
        return 36;
    }

    function wrap(doc, text, maxW) {
        return doc.splitTextToSize(clean(text), maxW);
    }

    function drawSectionTitle(doc, x, y, title) {
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(11.5);
        doc.setTextColor.apply(doc, C.navy);
        doc.text(clip(title, 48), x, y);
        return y + 5.5;
    }

    function drawProse(doc, x, y, maxW, paragraphs, fontSize) {
        fontSize = fontSize || 8.2;
        var yy = y;
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(fontSize);
        doc.setTextColor.apply(doc, C.ink);
        (paragraphs || []).forEach(function (p) {
            var lines = wrap(doc, p, maxW);
            doc.text(lines, x, yy);
            yy += lines.length * (fontSize * 0.42) + 2.8;
        });
        return yy;
    }

    function drawTintBand(doc, y, h) {
        doc.setFillColor.apply(doc, C.skySoft);
        doc.rect(0, y, PAGE.w, h, 'F');
    }

    function drawLegend(doc, x, y, items) {
        var xx = x;
        (items || []).forEach(function (it) {
            doc.setFillColor.apply(doc, it.color);
            doc.roundedRect(xx, y - 2.2, 3.2, 3.2, 0.5, 0.5, 'F');
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(6.5);
            doc.setTextColor.apply(doc, C.muted);
            doc.text(clip(it.label, 18), xx + 4.2, y);
            xx += 4.2 + doc.getTextWidth(clip(it.label, 18)) + 5;
        });
    }

    /** Barras agrupadas, sin desborde, ejes limpios */
    function drawGroupedBars(doc, opts) {
        var x = opts.x;
        var y = opts.y;
        var w = opts.w;
        var h = opts.h;
        var labels = opts.labels || [];
        var series = opts.series || [];
        var maxVal = opts.max || 0;
        var i, gi, si, v, groupW, barW, gap, gx, bx, bh, baseY, gy;

        series.forEach(function (ser) {
            (ser.values || []).forEach(function (n) {
                n = Number(n) || 0;
                if (n > maxVal) maxVal = n;
            });
        });
        maxVal = Math.max(maxVal, 1);
        // Round nice max
        var nice = Math.ceil(maxVal / 4) * 4;
        if (nice < maxVal) nice = maxVal;
        maxVal = nice;

        var axisL = x + 8;
        var plotW = w - 10;

        doc.setDrawColor.apply(doc, C.line);
        doc.setLineWidth(0.18);
        for (i = 0; i <= 4; i++) {
            gy = y + h - (h * i / 4);
            doc.line(axisL, gy, x + w, gy);
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(6);
            doc.setTextColor.apply(doc, C.light);
            doc.text(String(Math.round(maxVal * i / 4)), axisL - 1.5, gy + 1.1, { align: 'right' });
        }

        groupW = plotW / Math.max(labels.length, 1);
        var nSeries = Math.max(series.length, 1);
        barW = Math.min(3.8, Math.max(2.2, (groupW - 5) / nSeries));
        gap = 0.55;
        baseY = y + h;
        var clusterW = nSeries * barW + (nSeries - 1) * gap;

        labels.forEach(function (label, gi) {
            gx = axisL + gi * groupW + groupW / 2;
            series.forEach(function (ser, si) {
                v = Number(ser.values[gi] || 0);
                bh = (v / maxVal) * (h - 1.5);
                bx = gx - clusterW / 2 + si * (barW + gap);
                doc.setFillColor.apply(doc, ser.color);
                if (bh < 0.6) bh = v > 0 ? 0.6 : 0;
                if (bh > 0) doc.roundedRect(bx, baseY - bh, barW, bh, 0.35, 0.35, 'F');
            });
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(6.2);
            doc.setTextColor.apply(doc, C.muted);
            doc.text(clip(label, 10), gx, baseY + 3.8, { align: 'center' });
        });

        if (opts.legend && opts.legend.length) {
            drawLegend(doc, axisL, y + h + 8.5, opts.legend);
        }
    }

    function drawDonut(doc, opts) {
        var cx = opts.cx;
        var cy = opts.cy;
        var r = opts.r || 27;
        var slices = opts.slices || [];
        var total = 0;
        slices.forEach(function (s) { total += Math.max(0, Number(s.value) || 0); });

        if (total <= 0) {
            doc.setDrawColor.apply(doc, C.line);
            doc.setLineWidth(7);
            doc.circle(cx, cy, r - 3.5, 'S');
        } else {
            var start = -Math.PI / 2;
            var step = Math.PI / 120;
            slices.forEach(function (slice) {
                var sweep = (Math.max(0, Number(slice.value) || 0) / total) * Math.PI * 2;
                var a = start;
                var end = start + sweep;
                doc.setDrawColor.apply(doc, slice.color);
                doc.setLineWidth(7.2);
                while (a < end - 0.0001) {
                    var a2 = Math.min(a + step, end);
                    doc.line(
                        cx + Math.cos(a) * (r - 3.6),
                        cy + Math.sin(a) * (r - 3.6),
                        cx + Math.cos(a2) * (r - 3.6),
                        cy + Math.sin(a2) * (r - 3.6)
                    );
                    a = a2;
                }
                start = end;
            });
        }

        doc.setFillColor.apply(doc, C.white);
        doc.circle(cx, cy, r - 8.8, 'F');

        if (opts.centerLabel != null) {
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(12);
            doc.setTextColor.apply(doc, C.navy);
            doc.text(String(opts.centerLabel), cx, cy + 0.5, { align: 'center' });
        }
        if (opts.centerSub) {
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(6.5);
            doc.setTextColor.apply(doc, C.muted);
            doc.text(clip(opts.centerSub, 16), cx, cy + 5.5, { align: 'center' });
        }

        // Side labels for slices
        if (opts.showLabels) {
            var ly = cy - (slices.length * 5) / 2;
            slices.forEach(function (s, idx) {
                var pct = total ? Math.round((Number(s.value) / total) * 1000) / 10 : 0;
                doc.setFillColor.apply(doc, s.color);
                doc.circle(cx + r + 6, ly + idx * 7, 1.4, 'F');
                doc.setFont('helvetica', 'normal');
                doc.setFontSize(6.5);
                doc.setTextColor.apply(doc, C.ink);
                doc.text(clip((s.label || '') + '  ' + pct + '%', 28), cx + r + 9, ly + idx * 7 + 1.2);
            });
        }
    }

    function drawKpiStack(doc, x, y, items, textW) {
        textW = textW || 72;
        var yy = y;
        (items || []).forEach(function (item) {
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(20);
            doc.setTextColor.apply(doc, item.color || C.navy);
            var val = clip(String(item.value), 8);
            doc.text(val, x, yy);

            var valueW = Math.min(30, doc.getTextWidth(val) + 4);
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(7.5);
            doc.setTextColor.apply(doc, C.ink);
            var lines = wrap(doc, item.text || '', textW);
            // max 3 lines to avoid cascade overflow
            if (lines.length > 3) lines = lines.slice(0, 3);
            doc.text(lines, x + valueW, yy - 4.5);
            yy += Math.max(15, lines.length * 3.6 + 7);
        });
        return yy;
    }

    /** Tabla ejecutiva: sin rejilla pesada, anchos fijos, ellipsis */
    function renderTable(doc, opts) {
        var head = opts.head || [];
        var body = opts.body || [];
        var startY = opts.startY;
        var widths = opts.widths || [];
        var aligns = opts.aligns || [];
        var paint = opts.paint || null;

        doc.autoTable({
            head: [head],
            body: body,
            startY: startY,
            margin: { left: PAGE.ml, right: PAGE.mr, bottom: PAGE.mb },
            tableWidth: PAGE.contentW,
            theme: 'plain',
            styles: {
                font: 'helvetica',
                fontSize: 7.4,
                textColor: C.ink,
                cellPadding: { top: 2.6, right: 2.4, bottom: 2.6, left: 2.4 },
                overflow: 'ellipsize',
                minCellHeight: 7,
                lineColor: C.rule,
                lineWidth: 0,
                valign: 'middle',
            },
            headStyles: {
                fillColor: C.navy,
                textColor: C.white,
                fontStyle: 'bold',
                fontSize: 7.2,
                cellPadding: { top: 3.2, right: 2.4, bottom: 3.2, left: 2.4 },
            },
            alternateRowStyles: { fillColor: C.alt },
            columnStyles: (function () {
                var map = {};
                widths.forEach(function (w, i) {
                    map[i] = {
                        cellWidth: w,
                        halign: aligns[i] || 'left',
                    };
                });
                return map;
            })(),
            didParseCell: function (data) {
                if (paint) paint(data);
            },
            didDrawCell: function (data) {
                // linea inferior suave (look ejecutivo)
                if (data.section === 'body') {
                    doc.setDrawColor.apply(doc, C.rule);
                    doc.setLineWidth(0.12);
                    doc.line(
                        data.cell.x,
                        data.cell.y + data.cell.height,
                        data.cell.x + data.cell.width,
                        data.cell.y + data.cell.height
                    );
                }
            },
        });
        return doc.lastAutoTable.finalY;
    }

    function groupByPlan(clientes) {
        var map = {};
        (clientes || []).forEach(function (c) {
            var key = clean(c.plan) || 'Sin plan';
            map[key] = (map[key] || 0) + 1;
        });
        return Object.keys(map)
            .map(function (k) { return { label: k, value: map[k] }; })
            .sort(function (a, b) { return b.value - a.value; })
            .slice(0, 5);
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

    function statusPaint(colIndex, activeLabel) {
        activeLabel = activeLabel || 'ACTIVO';
        return function (d) {
            if (d.section !== 'body' || d.column.index !== colIndex) return;
            var raw = String(d.cell.raw || '').toUpperCase();
            d.cell.styles.fontStyle = 'bold';
            if (raw.indexOf(activeLabel) >= 0 || raw === 'OPTIMO' || raw.indexOf('ENTRADA') >= 0) {
                d.cell.styles.textColor = C.ok;
            } else if (raw.indexOf('MODER') >= 0 || raw.indexOf('WARN') >= 0) {
                d.cell.styles.textColor = C.warn;
            } else if (raw.indexOf('CRIT') >= 0 || raw.indexOf('INACT') >= 0 || (raw.indexOf('%') >= 0 && parseInt(raw, 10) >= 80)) {
                d.cell.styles.textColor = C.bad;
            } else if (raw.indexOf('SALIDA') >= 0) {
                d.cell.styles.textColor = C.navy;
            }
        };
    }

    function pctPaint(colIndex) {
        return function (d) {
            if (d.section !== 'body' || d.column.index !== colIndex) return;
            var p = parseInt(String(d.cell.raw), 10);
            if (!isFinite(p)) return;
            d.cell.styles.fontStyle = 'bold';
            d.cell.styles.textColor = p >= 80 ? C.bad : (p >= 50 ? C.warn : C.ok);
        };
    }

    // ---------- REPORTS ----------

    async function reportClientes(clientes) {
        var logo = await loadLogo();
        var doc = createDoc();
        var list = Array.isArray(clientes) ? clientes : [];
        var total = list.length;
        var activos = list.filter(function (c) { return !!c.activo; }).length;
        var inactivos = total - activos;
        var pctAct = total ? Math.round((activos / total) * 1000) / 10 : 0;
        var pctIna = total ? Math.round((inactivos / total) * 1000) / 10 : 0;
        var planes = groupByPlan(list);

        drawBrandHeader(doc, logo);
        drawMasthead(doc, 'Cartera de clientes · estado operativo');

        // Columna texto + grafica
        var leftW = 88;
        var chartX = PAGE.ml + leftW + 6;
        var chartW = PAGE.contentW - leftW - 6;
        var y = 66;

        drawSectionTitle(doc, PAGE.ml, y, 'Panorama de la cartera');
        drawProse(doc, PAGE.ml, y + 6, leftW, [
            'Consolidado de clientes registrados en TONYLEX: activacion, planes y datos de contacto para operacion en campo.',
            'Los indicadores se calculan al momento de exportar. Use el anexo tabular para auditoria comercial.',
            'Priorice reactivacion de inactivos y valide NAP/plan en cada servicio activo.'
        ], 8);

        var planLabels = planes.length ? planes.map(function (p) { return clip(p.label, 8); }) : ['N/D'];
        var planAct = planes.map(function (p) {
            return list.filter(function (c) { return (clean(c.plan) || 'Sin plan') === p.label && c.activo; }).length;
        });
        var planIna = planes.map(function (p) {
            return list.filter(function (c) { return (clean(c.plan) || 'Sin plan') === p.label && !c.activo; }).length;
        });
        var planTot = planes.map(function (p) { return p.value; });

        drawGroupedBars(doc, {
            x: chartX, y: 66, w: chartW, h: 40,
            labels: planLabels,
            series: planes.length ? [
                { color: C.sky, values: planIna },
                { color: C.purple, values: planAct },
                { color: C.navy, values: planTot },
            ] : [{ color: C.navy, values: [0] }],
            legend: [
                { color: C.sky, label: 'Inactivos' },
                { color: C.purple, label: 'Activos' },
                { color: C.navy, label: 'Total' },
            ],
        });

        // Banda
        var bandY = 128;
        drawTintBand(doc, bandY, 30);
        drawSectionTitle(doc, PAGE.ml, bandY + 9, 'Lectura operativa');
        drawProse(doc, PAGE.ml, bandY + 15, PAGE.contentW, [
            'Activos ' + activos + ' de ' + total + ' (' + pctAct + '%). Inactivos ' + inactivos +
            ' (' + pctIna + '%). Meta sugerida: mantener activacion por encima del 90%.'
        ], 8);

        // Donut + KPIs
        var blockY = bandY + 40;
        drawDonut(doc, {
            cx: PAGE.ml + 28, cy: blockY + 26, r: 24,
            slices: [
                { value: activos, color: C.navy, label: 'Activos' },
                { value: Math.max(inactivos, 0), color: C.purple, label: 'Inactivos' },
            ],
            centerLabel: pctAct + '%',
            centerSub: 'activos',
        });
        drawKpiStack(doc, PAGE.ml + 64, blockY + 10, [
            { value: pctAct + '%', color: C.navy, text: 'Clientes activos sobre el total de la cartera al corte.' },
            { value: pctIna + '%', color: C.purple, text: 'Cuentas inactivas pendientes de revision.' },
            { value: String(planes.length), color: C.sky, text: 'Planes distintos detectados en la exportacion.' },
        ], 100);

        // Tabla
        doc.addPage();
        y = drawPageHeader(doc, 'Anexo · detalle de clientes', logo);
        // widths sum ~ 182
        renderTable(doc, {
            startY: y,
            head: ['NOMBRE', 'DIRECCION', 'PLAN', 'ESTADO', 'CONTACTO', 'NAP'],
            widths: [38, 42, 26, 18, 28, 30],
            aligns: ['left', 'left', 'left', 'center', 'left', 'left'],
            body: list.map(function (c) {
                return [
                    clip(c.nombre, 42),
                    clip(c.direccion, 48),
                    clip(c.plan || '—', 22),
                    c.activo ? 'ACTIVO' : 'INACTIVO',
                    clip(c.contacto || '—', 26),
                    clip(c.nap_nombre || '—', 28),
                ];
            }),
            paint: statusPaint(3),
        });

        drawFooter(doc);
        doc.save('TONYLEX_Clientes_' + new Date().toISOString().slice(0, 10) + '.pdf');
    }

    async function reportNaps(naps) {
        var logo = await loadLogo();
        var doc = createDoc();
        var list = Array.isArray(naps) ? naps : [];
        var dist = list.filter(function (n) { return n.tipo_caja !== 'empalme'; });
        var buckets = occupancyBuckets(list);
        var totalPuertos = dist.reduce(function (a, n) { return a + (n.puertos_total || 0); }, 0);
        var usados = dist.reduce(function (a, n) { return a + (n.clientes_count || n.puertos_ocupados || 0); }, 0);
        var pct = totalPuertos ? Math.round((usados / totalPuertos) * 1000) / 10 : 0;

        drawBrandHeader(doc, logo);
        drawMasthead(doc, 'Cajas NAP · capacidad y ocupacion');

        var leftW = 88;
        var chartX = PAGE.ml + leftW + 6;
        var chartW = PAGE.contentW - leftW - 6;
        var y = 66;

        drawSectionTitle(doc, PAGE.ml, y, 'Salud de la red de acceso');
        drawProse(doc, PAGE.ml, y + 6, leftW, [
            'Capacidad instalada en cajas de distribucion, uso real de puertos y concentracion de riesgo por saturacion.',
            'Cajas en nivel critico (>80%) deben priorizarse para expansion o redistribucion.',
            'Este corte excluye empalmes del calculo de ocupacion util de acceso.'
        ], 8);

        var topNaps = dist.slice().sort(function (a, b) {
            return (b.porcentaje_uso || 0) - (a.porcentaje_uso || 0);
        }).slice(0, 5);
        if (!topNaps.length) topNaps = dist.slice(0, 5);
        var topLabels = topNaps.map(function (n) { return clip(n.nombre || 'NAP', 8); });
        var topTotal = topNaps.map(function (n) { return n.puertos_total || 0; });
        var topUsed = topNaps.map(function (n) { return n.clientes_count || n.puertos_ocupados || 0; });
        var topFree = topNaps.map(function (n, i) { return Math.max(0, topTotal[i] - topUsed[i]); });

        drawGroupedBars(doc, {
            x: chartX, y: 66, w: chartW, h: 40,
            labels: topLabels.length ? topLabels : ['N/D'],
            series: topLabels.length ? [
                { color: C.sky, values: topFree },
                { color: C.purple, values: topUsed },
                { color: C.navy, values: topTotal },
            ] : [{ color: C.navy, values: [0] }],
            legend: [
                { color: C.sky, label: 'Libres' },
                { color: C.purple, label: 'Usados' },
                { color: C.navy, label: 'Total' },
            ],
        });

        var bandY = 128;
        drawTintBand(doc, bandY, 28);
        drawSectionTitle(doc, PAGE.ml, bandY + 9, 'Capacidad consolidada');
        drawProse(doc, PAGE.ml, bandY + 15, PAGE.contentW, [
            usados + ' puertos en uso de ' + totalPuertos + ' (' + pct + '%). Criticas ' +
            buckets.critico + ' · Moderadas ' + buckets.moderado + ' · Optimas ' + buckets.optimo + '.'
        ], 8);

        var blockY = bandY + 38;
        drawDonut(doc, {
            cx: PAGE.ml + 28, cy: blockY + 26, r: 24,
            slices: [
                { value: buckets.optimo, color: C.ok, label: 'Optimo' },
                { value: buckets.moderado, color: C.warn, label: 'Moderado' },
                { value: buckets.critico, color: C.bad, label: 'Critico' },
            ],
            centerLabel: pct + '%',
            centerSub: 'ocupacion',
        });
        drawKpiStack(doc, PAGE.ml + 64, blockY + 8, [
            { value: pct + '%', color: C.navy, text: 'Ocupacion media de puertos en distribucion.' },
            { value: String(buckets.critico), color: C.bad, text: 'Cajas en nivel critico con accion prioritaria.' },
            { value: String(dist.length), color: C.violet, text: 'Cajas NAP de distribucion en el analisis.' },
        ], 100);

        doc.addPage();
        y = drawPageHeader(doc, 'Anexo · inventario de cajas NAP', logo);
        renderTable(doc, {
            startY: y,
            head: ['NOMBRE', 'TIPO', 'PUERTOS', 'USADOS', 'OCUPACION', 'HILO', 'MODELO'],
            widths: [40, 26, 18, 18, 22, 26, 32],
            aligns: ['left', 'left', 'center', 'center', 'center', 'left', 'left'],
            body: list.map(function (n) {
                var u = n.clientes_count || n.puertos_ocupados || 0;
                var p = n.puertos_total > 0 ? Math.round((u / n.puertos_total) * 100) : 0;
                return [
                    clip(n.nombre, 36),
                    clip(n.tipo_caja_display || n.tipo_caja || '—', 18),
                    String(n.puertos_total || 0),
                    String(u),
                    p + '%',
                    clip(n.hilo_conexion || '—', 20),
                    clip(n.nap_model_nombre || '—', 28),
                ];
            }),
            paint: pctPaint(4),
        });

        drawFooter(doc);
        doc.save('TONYLEX_NAPs_' + new Date().toISOString().slice(0, 10) + '.pdf');
    }

    async function reportTipos(naps) {
        var logo = await loadLogo();
        var doc = createDoc();
        var list = Array.isArray(naps) ? naps : [];
        var dist = list.filter(function (n) { return n.tipo_caja === 'distribucion'; });
        var emp = list.filter(function (n) { return n.tipo_caja === 'empalme'; });
        var total = list.length || 1;
        var pctD = Math.round((dist.length / total) * 1000) / 10;
        var pctE = Math.round((emp.length / total) * 1000) / 10;

        drawBrandHeader(doc, logo);
        drawMasthead(doc, 'Distribucion y empalmes · tipificacion de red');

        var leftW = 88;
        var chartX = PAGE.ml + leftW + 6;
        var chartW = PAGE.contentW - leftW - 6;

        drawSectionTitle(doc, PAGE.ml, 66, 'Composicion de la red');
        drawProse(doc, PAGE.ml, 72, leftW, [
            'Clasificacion por rol: acceso (NAP) frente a nodos de empalme.',
            'Una red equilibrada combina capacidad de acceso con empalmes estrategicos.',
            'Revise modelos e hilos en los anexos para cuadrar inventario fisico.'
        ], 8);

        var distPuertos = dist.reduce(function (a, n) { return a + (n.puertos_total || 0); }, 0);
        var empPuertos = emp.reduce(function (a, n) { return a + (n.puertos_total || 0); }, 0);
        var distUsados = dist.reduce(function (a, n) { return a + (n.clientes_count || n.puertos_ocupados || 0); }, 0);
        var empUsados = emp.reduce(function (a, n) { return a + (n.clientes_count || n.puertos_ocupados || 0); }, 0);

        drawGroupedBars(doc, {
            x: chartX, y: 66, w: chartW, h: 40,
            labels: ['NAP', 'Empalme'],
            series: [
                { color: C.sky, values: [dist.length, emp.length] },
                { color: C.purple, values: [distUsados, empUsados] },
                { color: C.navy, values: [distPuertos, empPuertos] },
            ],
            legend: [
                { color: C.sky, label: 'Cajas' },
                { color: C.purple, label: 'Usados' },
                { color: C.navy, label: 'Puertos' },
            ],
        });

        var bandY = 128;
        drawTintBand(doc, bandY, 26);
        drawSectionTitle(doc, PAGE.ml, bandY + 8, 'Balance tipologico');
        drawProse(doc, PAGE.ml, bandY + 14, PAGE.contentW, [
            'Distribucion ' + dist.length + ' (' + pctD + '%) · Empalmes ' + emp.length + ' (' + pctE + '%) · Total ' + list.length + '.'
        ], 8);

        var blockY = bandY + 36;
        drawDonut(doc, {
            cx: PAGE.ml + 28, cy: blockY + 26, r: 24,
            slices: [
                { value: dist.length, color: C.navy, label: 'NAP' },
                { value: emp.length, color: C.purple, label: 'Empalme' },
            ],
            centerLabel: String(list.length),
            centerSub: 'cajas',
        });
        drawKpiStack(doc, PAGE.ml + 64, blockY + 10, [
            { value: pctD + '%', color: C.navy, text: 'Participacion de cajas de distribucion (NAP).' },
            { value: pctE + '%', color: C.purple, text: 'Participacion de empalmes en el inventario.' },
            { value: String(list.length), color: C.sky, text: 'Elementos tipificados al exportar.' },
        ], 100);

        function tableTipo(titulo, rows) {
            doc.addPage();
            var start = drawPageHeader(doc, titulo, logo);
            if (!rows.length) {
                doc.setFontSize(9);
                doc.setTextColor.apply(doc, C.muted);
                doc.text('Sin registros de este tipo.', PAGE.ml, start + 6);
                return;
            }
            renderTable(doc, {
                startY: start,
                head: ['NOMBRE', 'MODELO', 'PUERTOS', 'USADOS', 'OCUPACION', 'HILO'],
                widths: [48, 40, 20, 20, 24, 30],
                aligns: ['left', 'left', 'center', 'center', 'center', 'left'],
                body: rows.map(function (n) {
                    var u = n.clientes_count || n.puertos_ocupados || 0;
                    var p = n.puertos_total > 0 ? Math.round((u / n.puertos_total) * 100) : 0;
                    return [
                        clip(n.nombre, 40),
                        clip(n.nap_model_nombre || '—', 34),
                        String(n.puertos_total || 0),
                        String(u),
                        p + '%',
                        clip(n.hilo_conexion || '—', 22),
                    ];
                }),
                paint: pctPaint(4),
            });
        }

        tableTipo('Anexo · cajas de distribucion (NAP)', dist);
        tableTipo('Anexo · cajas de empalme', emp);

        drawFooter(doc);
        doc.save('TONYLEX_Tipos_Caja_' + new Date().toISOString().slice(0, 10) + '.pdf');
    }

    async function reportInventarioCompleto(clientes, naps) {
        var logo = await loadLogo();
        var doc = createDoc();
        var cli = Array.isArray(clientes) ? clientes : [];
        var nap = Array.isArray(naps) ? naps : [];
        var activos = cli.filter(function (c) { return !!c.activo; }).length;
        var buckets = occupancyBuckets(nap);
        var pctAct = cli.length ? Math.round((activos / cli.length) * 1000) / 10 : 0;

        drawBrandHeader(doc, logo);
        drawMasthead(doc, 'Inventario completo · infraestructura y cartera');

        drawSectionTitle(doc, PAGE.ml, 66, 'Resumen ejecutivo');
        drawProse(doc, PAGE.ml, 72, PAGE.contentW, [
            'Documento maestro TONYLEX con fotografia operativa de clientes y cajas. Incluye indicadores, tipificacion y anexos tabulares.',
            'Emision: ' + fechaLarga() + '. Uso interno y confidencial.'
        ], 8.2);

        var inact = Math.max(0, cli.length - activos);
        drawGroupedBars(doc, {
            x: PAGE.ml, y: 96, w: 100, h: 38,
            labels: ['Clientes', 'Cajas'],
            series: [
                { color: C.sky, values: [cli.length, nap.length] },
                { color: C.purple, values: [activos, buckets.optimo + buckets.moderado] },
                { color: C.navy, values: [inact, buckets.critico] },
            ],
            legend: [
                { color: C.sky, label: 'Total' },
                { color: C.purple, label: 'Activos / OK+Mod' },
                { color: C.navy, label: 'Inact. / Critico' },
            ],
        });

        drawDonut(doc, {
            cx: 158, cy: 116, r: 24,
            slices: [
                { value: buckets.optimo, color: C.ok, label: 'Optimo' },
                { value: buckets.moderado, color: C.warn, label: 'Moderado' },
                { value: buckets.critico, color: C.bad, label: 'Critico' },
            ],
            centerLabel: String(nap.length),
            centerSub: 'cajas',
        });

        var bandY = 150;
        drawTintBand(doc, bandY, 24);
        drawProse(doc, PAGE.ml, bandY + 10, PAGE.contentW, [
            'Cartera ' + cli.length + ' (' + activos + ' activos, ' + pctAct + '%). Red ' + nap.length +
            ' cajas · ' + buckets.critico + ' en ocupacion critica.'
        ], 8);

        doc.addPage();
        var y = drawPageHeader(doc, 'Anexo A · clientes', logo);
        renderTable(doc, {
            startY: y,
            head: ['NOMBRE', 'PLAN', 'ESTADO', 'NAP', 'CONTACTO'],
            widths: [48, 32, 22, 40, 40],
            aligns: ['left', 'left', 'center', 'left', 'left'],
            body: cli.map(function (c) {
                return [
                    clip(c.nombre, 40),
                    clip(c.plan || '—', 26),
                    c.activo ? 'ACTIVO' : 'INACTIVO',
                    clip(c.nap_nombre || '—', 34),
                    clip(c.contacto || '—', 34),
                ];
            }),
            paint: statusPaint(2),
        });

        doc.addPage();
        y = drawPageHeader(doc, 'Anexo B · cajas', logo);
        renderTable(doc, {
            startY: y,
            head: ['NOMBRE', 'TIPO', 'PUERTOS', 'USADOS', 'OCUPACION', 'HILO'],
            widths: [48, 30, 20, 20, 26, 38],
            aligns: ['left', 'left', 'center', 'center', 'center', 'left'],
            body: nap.map(function (n) {
                var u = n.clientes_count || n.puertos_ocupados || 0;
                var p = n.puertos_total > 0 ? Math.round((u / n.puertos_total) * 100) : 0;
                return [
                    clip(n.nombre, 40),
                    clip(n.tipo_caja_display || n.tipo_caja || '—', 22),
                    String(n.puertos_total || 0),
                    String(u),
                    p + '%',
                    clip(n.hilo_conexion || '—', 28),
                ];
            }),
            paint: pctPaint(4),
        });

        drawFooter(doc);
        doc.save('TONYLEX_Inventario_Completo_' + new Date().toISOString().slice(0, 10) + '.pdf');
    }

    async function reportAsistencia(payload) {
        var logo = await loadLogo();
        var doc = createDoc();
        var res = (payload && payload.resumen) || {};
        var periodo = (payload && payload.periodo) || {};
        var registros = (payload && payload.registros) || [];
        var entradas = res.entradas_periodo || 0;
        var salidas = res.salidas_periodo || 0;
        var totalMov = (entradas + salidas) || 1;
        var pctE = Math.round((entradas / totalMov) * 1000) / 10;
        var pctS = Math.round((salidas / totalMov) * 1000) / 10;

        drawBrandHeader(doc, logo);
        drawMasthead(doc, 'Asistencia laboral · ' + clip((periodo.desde || '') + ' al ' + (periodo.hasta || ''), 48));

        var leftW = 88;
        var chartX = PAGE.ml + leftW + 6;
        var chartW = PAGE.contentW - leftW - 6;

        drawSectionTitle(doc, PAGE.ml, 66, 'Control de jornada');
        drawProse(doc, PAGE.ml, 72, leftW, [
            'Consolidado de entradas y salidas del personal activo para cuadrar presencia en campo.',
            'El anexo cronologico permite auditoria por trabajador y tipo de movimiento.',
            'Periodo: ultimos ' + (periodo.dias || 30) + ' dias.'
        ], 8);

        drawGroupedBars(doc, {
            x: chartX, y: 66, w: chartW, h: 40,
            labels: ['Periodo', 'Hoy'],
            series: [
                { color: C.sky, values: [entradas, res.entradas_hoy || 0] },
                { color: C.purple, values: [salidas, res.salidas_hoy || 0] },
                { color: C.navy, values: [entradas + salidas, (res.entradas_hoy || 0) + (res.salidas_hoy || 0)] },
            ],
            legend: [
                { color: C.sky, label: 'Entradas' },
                { color: C.purple, label: 'Salidas' },
                { color: C.navy, label: 'Total' },
            ],
        });

        var bandY = 128;
        drawTintBand(doc, bandY, 28);
        drawSectionTitle(doc, PAGE.ml, bandY + 9, 'Indicadores del periodo');
        drawProse(doc, PAGE.ml, bandY + 15, PAGE.contentW, [
            'Personal ' + (res.total_trabajadores || 0) +
            ' · Registros ' + (res.registros_periodo || 0) +
            ' · Dentro hoy ' + (res.dentro_hoy || 0) +
            ' · Movimientos hoy ' + ((res.entradas_hoy || 0) + (res.salidas_hoy || 0))
        ], 8);

        var blockY = bandY + 38;
        drawDonut(doc, {
            cx: PAGE.ml + 28, cy: blockY + 26, r: 24,
            slices: [
                { value: entradas, color: C.navy, label: 'Entradas' },
                { value: salidas, color: C.purple, label: 'Salidas' },
            ],
            centerLabel: String(res.registros_periodo || 0),
            centerSub: 'movs',
        });
        drawKpiStack(doc, PAGE.ml + 64, blockY + 10, [
            { value: pctE + '%', color: C.navy, text: 'Entradas respecto al total de movimientos.' },
            { value: pctS + '%', color: C.purple, text: 'Salidas registradas en el mismo intervalo.' },
            { value: String(res.dentro_hoy || 0), color: C.sky, text: 'Colaboradores en jornada al corte de hoy.' },
        ], 100);

        doc.addPage();
        var y = drawPageHeader(doc, 'Anexo · registro detallado', logo);
        if (!registros.length) {
            doc.setFontSize(9);
            doc.setTextColor.apply(doc, C.muted);
            doc.text('No hay registros en el periodo seleccionado.', PAGE.ml, y + 8);
        } else {
            renderTable(doc, {
                startY: y,
                head: ['TRABAJADOR', 'TIPO', 'FECHA', 'HORA'],
                widths: [86, 32, 32, 32],
                aligns: ['left', 'center', 'center', 'center'],
                body: registros.map(function (r) {
                    return [
                        clip(r.trabajador, 55),
                        clip((r.tipo_label || r.tipo || '').toUpperCase(), 16),
                        r.fecha || '',
                        r.hora || '',
                    ];
                }),
                paint: statusPaint(1),
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
