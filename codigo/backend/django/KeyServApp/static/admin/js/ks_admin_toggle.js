// Agrega botones "Buscar ▾" / "Filtros ▾" para desplegar/esconder el
// buscador y la barra de filtros en los listados de /admin/ — colapsados
// por defecto para que la ventana quede compacta.
document.addEventListener('DOMContentLoaded', function () {
  var barra = document.createElement('div');
  barra.className = 'ks-admin-toggle-bar';
  var agregoAlguno = false;

  function agregarToggle(selector, etiqueta) {
    var el = document.querySelector(selector);
    if (!el) return;
    var boton = document.createElement('button');
    boton.type = 'button';
    boton.className = 'ks-admin-toggle-btn';
    boton.textContent = etiqueta + ' ▾';
    boton.addEventListener('click', function () {
      var abierto = el.classList.toggle('ks-show');
      boton.classList.toggle('ks-active', abierto);
      boton.textContent = etiqueta + (abierto ? ' ▴' : ' ▾');
    });
    barra.appendChild(boton);
    agregoAlguno = true;
  }

  agregarToggle('#toolbar', 'Buscar');
  agregarToggle('#changelist-filter', 'Filtros');

  if (agregoAlguno) {
    var contenido = document.getElementById('content-main') || document.getElementById('content');
    if (contenido) contenido.insertBefore(barra, contenido.firstChild);
  }
});
