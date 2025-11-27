// Estructura default con nuevos campos
let ESTRUCTURA_DEFAULT = {
  "01_DNI": {"id_seccion": 1, "tipo_documento": "DNI", "descripcion": "Cédula de Identidad", "pagina_inicio": 1, "pagina_fin": 1},
  "02_Curriculum": {"id_seccion": 2, "tipo_documento": "Curriculum", "descripcion": "Currículum Vitae", "pagina_inicio": 2, "pagina_fin": 5},
  "03_Titulo_Universitario": {"id_seccion": 3, "tipo_documento": "Titulo", "descripcion": "Título Universitario", "pagina_inicio": 6, "pagina_fin": 6},
  "04_Contrato_Laboral": {"id_seccion": 4, "tipo_documento": "Contrato", "descripcion": "Contrato Laboral", "pagina_inicio": 7, "pagina_fin": 12},
  "05_Antecedentes_Penales": {"id_seccion": 5, "tipo_documento": "Antecedentes", "descripcion": "Antecedentes Penales", "pagina_inicio": 13, "pagina_fin": 14},
  "06_Carnet_Sanitario": {"id_seccion": 6, "tipo_documento": "Carnet", "descripcion": "Carnet Sanitario", "pagina_inicio": 15, "pagina_fin": 15},
  "07_Licencias": {"id_seccion": 7, "tipo_documento": "Licencias", "descripcion": "Licencias Profesionales", "pagina_inicio": 16, "pagina_fin": 20}
};

// Función segura para escapar HTML y prevenir XSS
function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}

// Cache de secciones cargadas una sola vez
let seccionesCache = null;

document.addEventListener('DOMContentLoaded', function() {
  console.log('DOMContentLoaded: iniciando carga de estructura');
  console.log('ESTRUCTURA_DEFAULT inicial:', JSON.stringify(ESTRUCTURA_DEFAULT));
  
  cargarSecciones().then(async () => {
    // Cargar estructura personalizada desde BD si existe
    await cargarEstructuraDesdeServidor();
    console.log('ESTRUCTURA_DEFAULT despues de cargarEstructuraDesdeServidor:', JSON.stringify(ESTRUCTURA_DEFAULT));
    
    // IMPORTANTE: Actualizar el campo del formulario con la estructura (personalizada o por defecto)
    const estructuraJsonField = document.getElementById('estructura_json');
    if (estructuraJsonField) {
      const estructuraSerializada = JSON.stringify(ESTRUCTURA_DEFAULT);
      estructuraJsonField.value = estructuraSerializada;
      console.log('[DEBUG] Campo estructura_json actualizado en DOMContentLoaded:', estructuraSerializada.substring(0, 100) + '...');
    }
    
    cargarEstructura();
    setupEventListeners();
    
    // Verificar que la estructura este correcta
    if (Object.keys(ESTRUCTURA_DEFAULT).length === 0) {
      console.error('ESTRUCTURA_DEFAULT esta vacia despues de inicializar');
    } else {
      console.log('OK: ESTRUCTURA_DEFAULT cargada con', Object.keys(ESTRUCTURA_DEFAULT).length, 'elementos');
      console.log('Contenido:', ESTRUCTURA_DEFAULT);
    }
  });
});

function cargarEstructuraDesdeServidor() {
  return new Promise((resolve) => {
    try {
      // Obtener id_personal del atributo data del formulario
      const formCargarPDF = document.getElementById('formCargarPDF');
      if (!formCargarPDF) {
        console.log('[DEBUG] Formulario de carga PDF no encontrado, usando estructura por defecto');
        resolve();
        return;
      }
      
      const id_personal = formCargarPDF.getAttribute('data-personal-id');
      console.log('[DEBUG] id_personal obtenido del formulario:', id_personal);
      
      if (!id_personal) {
        console.log('[DEBUG] No se pudo determinar id_personal, usando estructura por defecto');
        resolve();
        return;
      }
      
      // Llamar al API para obtener la estructura personalizada
      console.log('[DEBUG] Solicitando estructura personalizada del servidor...');
      fetch(`/legajo/api/estructura/${id_personal}`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log('[DEBUG] Respuesta del servidor:', data);
          
          if (data.exito && data.estructura) {
            console.log('[DEBUG] Estructura personalizada encontrada en servidor');
            console.log('[DEBUG] Estructura personalizada:', data.estructura);
            
            // Hacer MERGE con la estructura por defecto
            Object.assign(ESTRUCTURA_DEFAULT, data.estructura);
            
            console.log('[DEBUG] ESTRUCTURA_DEFAULT fusionada con estructura personalizada del servidor');
            console.log('[DEBUG] Elementos totales:', Object.keys(ESTRUCTURA_DEFAULT).length);
          } else {
            console.log('[DEBUG] No hay estructura personalizada en servidor, usando por defecto');
          }
          
          resolve();
        })
        .catch(error => {
          console.warn('[DEBUG] Error al cargar estructura del servidor:', error);
          console.log('[DEBUG] Usando estructura por defecto');
          resolve();
        });
      
    } catch (error) {
      console.error('[DEBUG] Error en cargarEstructuraDesdeServidor:', error);
      resolve();
    }
  });
}

function cargarEstructuraGuardada() {
  try {
    // Obtener id_personal del atributo data del formulario
    const formCargarPDF = document.getElementById('formCargarPDF');
    if (!formCargarPDF) {
      console.log('[DEBUG] Formulario de carga PDF no encontrado');
      return;
    }
    
    const id_personal = formCargarPDF.getAttribute('data-personal-id');
    console.log('[DEBUG] id_personal obtenido del formulario:', id_personal);
    
    if (!id_personal) {
      console.log('[DEBUG] No se pudo determinar id_personal del formulario');
      return;
    }
    
    const storageName = `estructura_${id_personal}`;
    console.log('[DEBUG] Buscando en localStorage con clave:', storageName);
    
    const estructuraGuardada = localStorage.getItem(storageName);
    console.log('[DEBUG] Valor en localStorage:', estructuraGuardada ? 'ENCONTRADO (length: ' + estructuraGuardada.length + ')' : 'NO ENCONTRADO');
    
    if (estructuraGuardada) {
      try {
        const parsed = JSON.parse(estructuraGuardada);
        console.log('[DEBUG] JSON parseado exitosamente. Elementos:', Object.keys(parsed).length);
        console.log('[DEBUG] Elementos guardados:', Object.keys(parsed));
        
        // Validar estructura antes de aplicar
        let estructuraValida = true;
        for (const [key, val] of Object.entries(parsed)) {
          // Validar que tenga la estructura esperada
          if (typeof val !== 'object' || !val.hasOwnProperty('id_seccion')) {
            console.warn('[DEBUG] Estructura inválida en localStorage, ignorando:', key);
            estructuraValida = false;
            break;
          }
        }
        
        if (!estructuraValida) {
          console.warn('[DEBUG] La estructura en localStorage no es válida, usando por defecto');
          localStorage.removeItem(storageName);
          return;
        }
        
        // IMPORTANTE: Hacer MERGE en lugar de reemplazar completamente
        // De esta forma se mantienen los elementos nuevos de la estructura por defecto
        // y se aplican las personalizaciones guardadas
        Object.assign(ESTRUCTURA_DEFAULT, parsed);
        
        console.log('[DEBUG] ESTRUCTURA_DEFAULT fusionada con estructura guardada');
        console.log('[DEBUG] Elementos totales ahora:', Object.keys(ESTRUCTURA_DEFAULT).length);
        console.log('[DEBUG] Elementos finales:', Object.keys(ESTRUCTURA_DEFAULT));
      } catch (e) {
        console.warn('[DEBUG] Error al parsear estructura guardada:', e);
        console.warn('[DEBUG] Removiendo estructura inválida del localStorage');
        localStorage.removeItem(storageName);
      }
    } else {
      console.log('[DEBUG] No hay estructura personalizada guardada para personal', id_personal, 'usando por defecto');
      console.log('[DEBUG] ESTRUCTURA_DEFAULT actual:', Object.keys(ESTRUCTURA_DEFAULT));
    }
  } catch (error) {
    console.error('[DEBUG] Error en cargarEstructuraGuardada:', error);
  }
}

async function cargarSecciones() {
  if (!seccionesCache) {
    try {
      const response = await fetch('/legajo/api/secciones');
      seccionesCache = await response.json();
    } catch (error) {
      console.error('Error cargando secciones:', error);
      seccionesCache = [];
    }
  }
  return seccionesCache;
}

function setupEventListeners() {
  const btnPersonalizar = document.getElementById('btnPersonalizar');
  const btnCancelarPersonalizacion = document.getElementById('btnCancelarPersonalizacion');
  const btnGuardarPersonalizacion = document.getElementById('btnGuardarPersonalizacion');
  const editarEstructura = document.getElementById('editarEstructura');

  if (btnPersonalizar) {
    btnPersonalizar.addEventListener('click', function(e) {
      e.preventDefault();
      editarEstructura.classList.toggle('d-none');
      btnPersonalizar.innerHTML = editarEstructura.classList.contains('d-none') 
        ? '<i class="bi bi-pencil me-1"></i>Personalizar Estructura'
        : '<i class="bi bi-x me-1"></i>Ocultar Edición';
    });
  }

  if (btnCancelarPersonalizacion) {
    btnCancelarPersonalizacion.addEventListener('click', function(e) {
      e.preventDefault();
      editarEstructura.classList.add('d-none');
      btnPersonalizar.innerHTML = '<i class="bi bi-pencil me-1"></i>Personalizar Estructura';
      generarFormularioEstructura();
    });
  }

  if (btnGuardarPersonalizacion) {
    btnGuardarPersonalizacion.addEventListener('click', function(e) {
      e.preventDefault();
      guardarEstructuraLocalmente();
    });
  }
}

function guardarEstructuraLocalmente() {
  try {
    // Obtener id_personal del atributo data del formulario
    const formCargarPDF = document.getElementById('formCargarPDF');
    if (!formCargarPDF) {
      console.error('[DEBUG] No se encontró el formulario de carga');
      alert('No se encontró el formulario de carga');
      return;
    }
    
    const id_personal = formCargarPDF.getAttribute('data-personal-id');
    console.log('[DEBUG] id_personal para guardar:', id_personal);
    
    if (!id_personal) {
      console.error('[DEBUG] No se encontró data-personal-id en formCargarPDF');
      alert('No se pudo determinar el personal. Por favor, recarga la página.');
      return;
    }
    
    // Guardar en localStorage (sin tocar BD)
    const storageName = `estructura_${id_personal}`;
    const estructuraJSON = JSON.stringify(ESTRUCTURA_DEFAULT);
    
    console.log('[DEBUG] Guardando en localStorage:');
    console.log('[DEBUG]   Clave:', storageName);
    console.log('[DEBUG]   Contenido:', ESTRUCTURA_DEFAULT);
    console.log('[DEBUG]   JSON:', estructuraJSON.substring(0, 100) + '...');
    
    localStorage.setItem(storageName, estructuraJSON);
    
    console.log('[DEBUG] Estructura guardada en localStorage. Verificando:');
    const verificacion = localStorage.getItem(storageName);
    console.log('[DEBUG]   Guardado correctamente:', verificacion ? 'SI' : 'NO');
    
    // ACTUALIZAR el campo del formulario INMEDIATAMENTE
    const estructuraJsonField = document.getElementById('estructura_json');
    if (estructuraJsonField) {
      estructuraJsonField.value = estructuraJSON;
      console.log('[DEBUG] Campo estructura_json ACTUALIZADO después de guardar');
    }
    
    // Feedback visual
    alert('Estructura personalizada guardada correctamente');
    const editarEstructura = document.getElementById('editarEstructura');
    const btnPersonalizar = document.getElementById('btnPersonalizar');
    editarEstructura.classList.add('d-none');
    btnPersonalizar.innerHTML = '<i class="bi bi-pencil me-1"></i>Personalizar Estructura';
    
  } catch (error) {
    console.error('[DEBUG] Error en guardarEstructuraLocalmente:', error);
    alert('Error al guardar: ' + error.message);
  }
}

function cargarEstructura() {
  const tbody = document.getElementById('estructuraBody');
  if (!tbody) return;
  tbody.innerHTML = '';
  Object.entries(ESTRUCTURA_DEFAULT).forEach(([seccion, datos]) => {
    // Buscar el nombre de la sección en el cache
    let nombreSeccion = seccion;  // Por defecto, usar el ID de la sección
    if (datos.id_seccion && seccionesCache && seccionesCache.length > 0) {
      const seccionEncontrada = seccionesCache.find(s => s.id === parseInt(datos.id_seccion));
      if (seccionEncontrada) {
        nombreSeccion = seccionEncontrada.nombre;
      }
    }
    
    const paginas = datos.pagina_inicio === datos.pagina_fin ? datos.pagina_inicio : `${datos.pagina_inicio}-${datos.pagina_fin}`;
    // SEGURIDAD: Escapar todos los valores para prevenir XSS
    tbody.innerHTML += `<tr data-seccion="${escapeHtml(seccion)}"><td>${escapeHtml(nombreSeccion)}</td><td>${escapeHtml(datos.tipo_documento)}</td><td>${escapeHtml(datos.descripcion)}</td><td>${escapeHtml(paginas)}</td></tr>`;
  });
  generarFormularioEstructura();
}

function generarFormularioEstructura() {
  const formulario = document.getElementById('formularioEstructura');
  if (!formulario) return;
  formulario.innerHTML = '';
  Object.entries(ESTRUCTURA_DEFAULT).forEach(([seccion, datos]) => generarCardSeccion(seccion, datos, formulario));
  
  const btnAgregar = document.createElement('button');
  btnAgregar.type = 'button';
  btnAgregar.className = 'btn btn-sm btn-success mt-3';
  btnAgregar.innerHTML = '<i class="bi bi-plus-lg me-1"></i>Agregar Sección';
  btnAgregar.addEventListener('click', () => {
    const num = Object.keys(ESTRUCTURA_DEFAULT).length + 1;
    const newSeccion = `${String(num).padStart(2, '0')}_Nueva`;
    ESTRUCTURA_DEFAULT[newSeccion] = {"id_seccion": 0, "tipo_documento": "", "descripcion": "", "pagina_inicio": 1, "pagina_fin": 1};
    // SEGURIDAD: Escapar el nombre de la sección
    document.getElementById('estructuraBody').innerHTML += `<tr data-seccion="${escapeHtml(newSeccion)}"><td>${escapeHtml(newSeccion)}</td><td></td><td></td><td>1</td></tr>`;
    generarCardSeccion(newSeccion, ESTRUCTURA_DEFAULT[newSeccion], formulario);
    formulario.appendChild(btnAgregar);
  });
  formulario.appendChild(btnAgregar);
}

function generarCardSeccion(seccion, datos, formulario) {
  const card = document.createElement('div');
  card.className = 'card mb-3';
  card.setAttribute('data-seccion', seccion);
  
  // Crear estructura SIN inline handlers - ID es NO EDITABLE
  card.innerHTML = `
    <div class="card-body p-2">
      <div class="row g-2">
        <div class="col-12 col-md-2"><label class="form-label small fw-bold">ID</label><input type="text" class="form-control form-control-sm" value="${seccion}" disabled></div>
        <div class="col-12 col-md-2"><label class="form-label small fw-bold">Sección</label><select class="form-select form-select-sm seccion-select" data-tipos-url="/legajo/api/tipos_documento/por_seccion/0"><option value="0">-- Seleccionar --</option></select></div>
        <div class="col-12 col-md-3"><label class="form-label small fw-bold">Tipo Documento</label><select class="form-select form-select-sm tipo-documento"><option value="0">-- Seleccione sección --</option></select></div>
        <div class="col-12 col-md-2"><label class="form-label small fw-bold">Descripción</label><input type="text" class="form-control form-control-sm descripcion" value="${datos.descripcion}"></div>
        <div class="col-12 col-md-1"><label class="form-label small fw-bold">Inicio</label><input type="number" class="form-control form-control-sm page-start" value="${datos.pagina_inicio}" min="1"></div>
        <div class="col-12 col-md-1"><label class="form-label small fw-bold">Fin</label><input type="number" class="form-control form-control-sm page-end" value="${datos.pagina_fin}" min="1"></div>
        <div class="col-12 col-md-1 d-flex align-items-end gap-1"><button type="button" class="btn btn-sm btn-outline-primary flex-grow-1 btn-actualizar-fila" title="Guardar"><i class="bi bi-check"></i></button><button type="button" class="btn btn-sm btn-outline-danger btn-eliminar-fila" title="Eliminar"><i class="bi bi-trash"></i></button></div>
      </div>
    </div>
  `;
  
  const seccionSelect = card.querySelector('.seccion-select');
  const tipoSelect = card.querySelector('.tipo-documento');
  
  // Usar el cache de secciones en lugar de hacer un fetch
  seccionesCache.forEach(sec => {
    const opt = document.createElement('option');
    opt.value = sec.id;
    opt.textContent = sec.nombre;
    if (sec.id === datos.id_seccion) opt.selected = true;
    seccionSelect.appendChild(opt);
  });
  
  // Agregar event listeners de forma segura (sin inline)
  const btnActualizar = card.querySelector('.btn-actualizar-fila');
  const btnEliminar = card.querySelector('.btn-eliminar-fila');
  
  btnActualizar.addEventListener('click', () => actualizarFila(card));
  btnEliminar.addEventListener('click', () => eliminarFila(card));
  seccionSelect.addEventListener('change', () => actualizarTiposDocumento(seccionSelect));
  
  // Si ya hay una sección seleccionada, cargar los tipos de documento automáticamente
  if (datos.id_seccion && datos.id_seccion !== 0) {
    actualizarTiposDocumento(seccionSelect);
  }
  
  formulario.appendChild(card);
}

function actualizarTiposDocumento(selectElement) {
  const card = selectElement.closest('.card');
  const seccionId = selectElement.value;
  const tipoSelect = card.querySelector('.tipo-documento');
  tipoSelect.innerHTML = '<option value="0">Cargando...</option>';
  tipoSelect.disabled = true;

  if (seccionId && seccionId !== '0') {
    const url = selectElement.getAttribute('data-tipos-url').replace('/0', `/${seccionId}`);
    
    // Debounce para evitar demasiadas peticiones
    if (card.fetchTimeout) clearTimeout(card.fetchTimeout);
    card.fetchTimeout = setTimeout(() => {
      fetch(url).then(r => r.json()).then(data => {
        tipoSelect.innerHTML = '<option value="0">-- Seleccionar --</option>';
        if (data && data.length > 0) {
          data.forEach(tipo => {
            const opt = document.createElement('option');
            opt.value = tipo.id;
            opt.textContent = tipo.nombre;
            tipoSelect.appendChild(opt);
          });
          tipoSelect.disabled = false;
        }
      }).catch(e => {
        tipoSelect.innerHTML = '<option value="0">Error</option>';
        tipoSelect.disabled = false;
      });
    }, 300);  // Espera 300ms antes de hacer la petición
  } else {
    tipoSelect.innerHTML = '<option value="0">-- Seleccione sección --</option>';
    tipoSelect.disabled = true;
  }
}

function actualizarFila(card) {
  const seccion = card.getAttribute('data-seccion');
  
  const seccionSelect = card.querySelector('.seccion-select');
  const seccionNumero = seccionSelect.value;
  
  // Obtener el nombre de la sección seleccionada
  const seccionNombre = seccionSelect.options[seccionSelect.selectedIndex]?.text || seccionNumero;
  
  const tipoDocumentoSelect = card.querySelector('.tipo-documento');
  
  // Obtener TANTO el id como el nombre del tipo de documento
  const tipoDocumentoId = tipoDocumentoSelect.value;
  const tipoDocumentoNombre = tipoDocumentoSelect.options[tipoDocumentoSelect.selectedIndex]?.text || tipoDocumentoSelect.value;
  
  const descripcion = card.querySelector('.descripcion').value;
  const pageStart = parseInt(card.querySelector('.page-start').value);
  const pageEnd = parseInt(card.querySelector('.page-end').value);

  if (!seccionNumero || seccionNumero === '0' || !tipoDocumentoId || tipoDocumentoId === '0') {
    alert('Por favor completa todos los campos');
    return;
  }
  
  // Validar que las páginas sean válidas
  if (isNaN(pageStart) || isNaN(pageEnd) || pageStart < 1 || pageEnd < 1) {
    alert('Las páginas deben ser números válidos mayores a 0');
    return;
  }

  console.log('[DEBUG] actualizarFila - Actualizando:', seccion);
  console.log('[DEBUG]   seccionNumero:', seccionNumero);
  console.log('[DEBUG]   tipoDocumentoNombre:', tipoDocumentoNombre);
  console.log('[DEBUG]   descripcion:', descripcion);
  console.log('[DEBUG]   paginas:', pageStart, '-', pageEnd);

  // Guardar el NOMBRE del tipo de documento, no el ID
  ESTRUCTURA_DEFAULT[seccion] = {
    id_seccion: parseInt(seccionNumero), 
    tipo_documento: tipoDocumentoNombre, 
    descripcion: descripcion, 
    pagina_inicio: pageStart, 
    pagina_fin: pageEnd
  };
  
  console.log('[DEBUG] ESTRUCTURA_DEFAULT actualizada:', ESTRUCTURA_DEFAULT[seccion]);
  console.log('[DEBUG] ESTRUCTURA_DEFAULT total de elementos:', Object.keys(ESTRUCTURA_DEFAULT).length);
  
  const tbody = document.getElementById('estructuraBody');
  
  // Actualizar la fila en la tabla
  const tableRow = tbody.querySelector(`tr[data-seccion="${seccion}"]`);
  if (tableRow) {
    const celdas = tableRow.querySelectorAll('td');
    celdas[0].textContent = seccionNombre;
    celdas[1].textContent = tipoDocumentoNombre;
    celdas[2].textContent = descripcion;
    celdas[3].textContent = pageStart === pageEnd ? pageStart : `${pageStart}-${pageEnd}`;
  }

  const btn = card.querySelector('.btn-actualizar-fila');
  btn.classList.add('btn-success');
  btn.classList.remove('btn-outline-primary');
  setTimeout(() => {
    btn.classList.remove('btn-success');
    btn.classList.add('btn-outline-primary');
  }, 1000);
}

function eliminarFila(card) {
  if (confirm('¿Eliminar esta sección?')) {
    const seccion = card.getAttribute('data-seccion');
    delete ESTRUCTURA_DEFAULT[seccion];
    card.remove();
    const tr = document.querySelector(`tr[data-seccion="${seccion}"]`);
    if (tr) tr.remove();
  }
}
