# app/application/services/pdf_split_service.py
"""
Servicio para separar archivos PDF grandes en múltiples documentos
basándose en rangos de páginas. Útil para procesar legajos completos.
"""

import os
import logging
from pypdf import PdfReader, PdfWriter
from datetime import datetime

logger = logging.getLogger(__name__)


class PdfSplitService:
    """
    Servicio para dividir PDFs grandes en archivos separados por tipo de documento.
    """

    def __init__(self, temp_folder="temp_pdfs"):
        """
        Args:
            temp_folder: Carpeta donde se guardarán los PDFs temporales
        """
        self.temp_folder = temp_folder
        if not os.path.exists(self.temp_folder):
            os.makedirs(self.temp_folder)
            logger.info(f"Carpeta temporal creada: {self.temp_folder}")

    def separar_legajo(self, archivo_origen, estructura_legajo, id_personal=None):
        """
        Separa un PDF grande en varios archivos basándose en rangos de páginas.

        Args:
            archivo_origen: Ruta al PDF completo
            estructura_legajo: Diccionario con formato:
                {
                    "Nombre_Documento": {"pagina_inicio": 1, "pagina_fin": 1, ...},
                    o formato antiguo: "Nombre_Documento": (1, 1),
                    ...
                }
            id_personal: ID del personal (opcional, para logging)

        Returns:
            Diccionario con los archivos generados:
            {
                "nombre_doc": {"archivo": ruta, "paginas": (inicio, fin), "exito": True/False}
            }
        """
        resultados = {}

        # Verificar que el archivo existe
        if not os.path.exists(archivo_origen):
            logger.error(f"Archivo no encontrado: {archivo_origen}")
            return {"error": f"Archivo '{archivo_origen}' no encontrado"}

        try:
            # Leer el PDF original
            reader = PdfReader(archivo_origen)
            total_paginas = len(reader.pages)
            logger.info(
                f"[ID {id_personal}] Procesando PDF: {archivo_origen} "
                f"({total_paginas} páginas)"
            )

            # Procesar cada documento según la estructura
            for nombre_doc, valor in estructura_legajo.items():
                try:
                    # Soportar dos formatos: tupla (antiguo) o diccionario (nuevo)
                    if isinstance(valor, dict):
                        # Formato nuevo: {"pagina_inicio": 1, "pagina_fin": 1, ...}
                        inicio = valor.get('pagina_inicio')
                        fin = valor.get('pagina_fin')
                    else:
                        # Formato antiguo: (1, 1)
                        inicio, fin = valor
                    
                    # Validar rangos
                    if inicio < 1 or fin > total_paginas or inicio > fin:
                        logger.warning(
                            f"[ID {id_personal}] Rango inválido para '{nombre_doc}': "
                            f"({inicio}-{fin}), total={total_paginas}"
                        )
                        resultados[nombre_doc] = {
                            "archivo": None,
                            "paginas": (inicio, fin),
                            "exito": False,
                            "error": "Rango de páginas inválido",
                        }
                        continue

                    # Crear writer para el nuevo PDF
                    writer = PdfWriter()

                    # Python cuenta desde 0, ajustamos
                    idx_inicio = inicio - 1
                    idx_fin = fin

                    # Agregar páginas al nuevo PDF
                    for i in range(idx_inicio, idx_fin):
                        writer.add_page(reader.pages[i])

                    # Generar nombre de archivo único
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nombre_archivo = (
                        f"{nombre_doc}_{id_personal}_{timestamp}.pdf"
                        if id_personal
                        else f"{nombre_doc}_{timestamp}.pdf"
                    )
                    ruta_archivo = os.path.join(self.temp_folder, nombre_archivo)

                    # Guardar el archivo
                    with open(ruta_archivo, "wb") as output_pdf:
                        writer.write(output_pdf)

                    logger.info(
                        f"[ID {id_personal}] Generado: {nombre_archivo} "
                        f"(págs {inicio}-{fin})"
                    )
                    resultados[nombre_doc] = {
                        "archivo": ruta_archivo,
                        "paginas": (inicio, fin),
                        "exito": True,
                        "nombre_archivo": nombre_archivo,
                    }

                except Exception as e:
                    logger.error(
                        f"[ID {id_personal}] Error procesando '{nombre_doc}': {e}"
                    )
                    resultados[nombre_doc] = {
                        "archivo": None,
                        "paginas": None,
                        "exito": False,
                        "error": str(e),
                    }

            return resultados

        except Exception as e:
            logger.error(f"[ID {id_personal}] Error general al procesar PDF: {e}")
            return {"error": f"Error al procesar PDF: {str(e)}"}

    def limpiar_temporales(self):
        """
        Elimina todos los archivos temporales (opcional).
        """
        try:
            import shutil

            if os.path.exists(self.temp_folder):
                shutil.rmtree(self.temp_folder)
                os.makedirs(self.temp_folder)
                logger.info("Archivos temporales limpiados")
        except Exception as e:
            logger.error(f"Error al limpiar temporales: {e}")
