/**
 * Handlers para upload_legajo.html
 * Maneja la carga de personal y estructura de legajo
 */

let listaPersonalCompleta = [];

document.addEventListener('DOMContentLoaded', function() {
  cargarListaPersonal();
  
  // Validar formulario antes de enviar
  const uploadForm = document.getElementById('uploadForm');
  if (uploadForm) {
    uploadForm.addEventListener('submit', function(e) {
      if (!this.checkValidity()) {
        e.preventDefault();
        e.stopPropagation();
      }
      this.classList.add('was-validated');
    });
  }

  // Event listener para cambios en el select
  const selectPersonal = document.getElementById('id_personal');
  if (selectPersonal) {
    selectPersonal.addEventListener('change', actualizarInfoPersonal);
  }

  // Event listener para búsqueda
  const buscarPersonal = document.getElementById('buscarPersonal');
  if (buscarPersonal) {
    buscarPersonal.addEventListener('input', filtrarPersonal);
  }
});

function cargarListaPersonal() {
  const urlAPI = document.querySelector('[data-personal-list-url]')?.getAttribute('data-personal-list-url') 
    || '/pdf/api/personal-list';
  
  console.log('Cargando personal desde:', urlAPI);
  
  fetch(urlAPI)
    .then(response => {
      console.log('Response status:', response.status);
      if (!response.ok) {
        throw new Error(`Error HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('✓ Datos recibidos:', data);
      
      if (data && data.error) {
        throw new Error('Error del servidor: ' + data.error);
      }
      
      if (!Array.isArray(data)) {
        console.warn('Datos recibidos no es un array:', typeof data);
        data = [];
      }
      
      if (data.length === 0) {
        console.warn('⚠ La lista de personal está vacía');
      } else {
        console.log(`✓ Se cargaron ${data.length} registros de personal`);
      }
      
      listaPersonalCompleta = data;
      actualizarSelectPersonal(data);
    })
    .catch(error => {
      console.error('✗ Error cargando personal:', error);
      const select = document.getElementById('id_personal');
      const option = document.createElement('option');
      option.value = '';
      option.textContent = '❌ Error: ' + error.message;
      option.disabled = true;
      option.selected = true;
      select.innerHTML = '';
      select.appendChild(option);
    });
}

function actualizarSelectPersonal(listaPersonal) {
  const select = document.getElementById('id_personal');
  select.innerHTML = '';
  
  if (!listaPersonal || listaPersonal.length === 0) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = '-- No hay personal disponible --';
    option.disabled = true;
    option.selected = true;
    select.appendChild(option);
    console.warn('La lista de personal está vacía');
    return;
  }
  
  const opcionDefault = document.createElement('option');
  opcionDefault.value = '';
  opcionDefault.textContent = '-- Seleccione un Personal --';
  select.appendChild(opcionDefault);
  
  listaPersonal.forEach(personal => {
    try {
      const option = document.createElement('option');
      option.value = personal.id;
      option.textContent = `${personal.nombre} (${personal.dni})`;
      option.dataset.dni = personal.dni;
      option.dataset.nombre = (personal.nombre || '').toLowerCase();
      select.appendChild(option);
    } catch (err) {
      console.error('Error al procesar personal:', personal, err);
    }
  });
}

function filtrarPersonal() {
  const termino = document.getElementById('buscarPersonal').value.toLowerCase().trim();
  
  if (!termino) {
    actualizarSelectPersonal(listaPersonalCompleta);
    return;
  }
  
  const filtrada = listaPersonalCompleta.filter(personal => {
    return personal.dni.toLowerCase().includes(termino) || 
           personal.nombre.toLowerCase().includes(termino);
  });
  
  actualizarSelectPersonal(filtrada);
}

function actualizarInfoPersonal() {
  const id_personal = document.getElementById('id_personal').value;
  
  if (!id_personal) {
    document.getElementById('personalInfo').style.display = 'none';
    document.getElementById('estructuraContainer').style.display = 'none';
    document.getElementById('noEstructura').style.display = 'block';
    return;
  }

  // Mostrar info del personal
  document.getElementById('personalInfo').style.display = 'block';
  
  // URL template desde el atributo data
  const urlTemplate = document.querySelector('[data-estructura-url]')?.getAttribute('data-estructura-url')
    || '/pdf/api/estructura-personal/0';
  
  // Cargar estructura personalizada
  fetch(urlTemplate.replace('/0', `/${id_personal}`))
    .then(response => {
      if (!response.ok) throw new Error('Error al cargar estructura');
      return response.json();
    })
    .then(data => {
      mostrarEstructura(data.estructura);
    })
    .catch(error => {
      console.error('Error:', error);
      document.getElementById('estructuraContainer').style.display = 'none';
      document.getElementById('noEstructura').style.display = 'block';
    });
}

function mostrarEstructura(estructura) {
  const tbody = document.getElementById('estructuraTable');
  tbody.innerHTML = '';
  
  let total = 0;
  for (const [seccion, info] of Object.entries(estructura)) {
    const tr = document.createElement('tr');
    const paginas = info.paginas || info;
    tr.innerHTML = `
      <td><strong>${seccion}</strong></td>
      <td>${paginas}</td>
    `;
    tbody.appendChild(tr);
    
    // Sumar páginas para validación
    if (Array.isArray(paginas)) {
      paginas.forEach(p => {
        if (p instanceof Array) {
          total += (p[1] - p[0] + 1);
        }
      });
    }
  }
  
  document.getElementById('estructuraContainer').style.display = 'block';
  document.getElementById('noEstructura').style.display = 'none';
}
