// Colorea los <select> de list_editable (estado_moderacion, estado_consulta,
// estado_documento, etc.) según su valor actual — sin tocar admin.py ni
// perder la edición inline que ya tenían. Clasifica por palabra clave sobre
// el texto de la opción elegida (no por PK ni por código de enum, que
// difieren entre catálogos: estado_moderacion usa PENDIENTE/APROBADA/
// RECHAZADA, estado_consulta usa filas de una tabla EstadoConsulta con
// nombres como "Abierta"/"En progreso"/"Resuelta"/"Cerrada") — así un
// catálogo nuevo mañana no necesita tocar este archivo si usa palabras
// razonables.
document.addEventListener('DOMContentLoaded', function () {
  var URGENTE = ['pendiente', 'abierta', 'no firmado', 'solicitada', 'erroneo', 'errónea', 'erróneo'];
  var OK = ['aprobada', 'resuelta', 'en progreso', 'confirmada', 'en curso', 'completada', 'firmado', 'pagada', 'pagado'];
  // Todo lo que no matchea ninguna de las dos listas de arriba (ej. "Rechazada",
  // "Cancelada", "Cerrada") cae en "neutral" — no necesita su propia lista.

  function clasificar(texto) {
    var t = texto.trim().toLowerCase();
    for (var i = 0; i < URGENTE.length; i++) if (t.indexOf(URGENTE[i]) !== -1) return 'urgente';
    for (var i = 0; i < OK.length; i++) if (t.indexOf(OK[i]) !== -1) return 'ok';
    return 'neutral';
  }

  function actualizar(select) {
    var opcion = select.options[select.selectedIndex];
    if (!opcion) return;
    select.setAttribute('data-ks-tono', clasificar(opcion.textContent));
  }

  // Solo los <select> de columnas de estado (list_editable en admin.py) —
  // Django arma la clase `field-<nombre_de_campo>` en cada <td>, así que no
  // hace falta enumerar cada <select> por id.
  var selects = document.querySelectorAll(
    '.field-estado_moderacion select, .field-estado_consulta select, .field-estado_documento select, .field-estado select'
  );
  selects.forEach(function (select) {
    actualizar(select);
    select.addEventListener('change', function () { actualizar(select); });
  });
});
