# Front Mission 3 - Traducción al Español

Traducción al español de Front Mission 3 (USA) para PlayStation 1.

## Estado del Proyecto

- **Fase actual**: Extracción de textos completada
- **Textos extraídos**: 28,884
- **Progreso de traducción por ia**: 0%
- **Progreso de revisión traducción**: 0%
- **Progreso de edición de imágenes**: 0%
- **Compilación**: Probada y funcional

## Estructura del Repositorio

```
front-mission-3-esp/
├── README.md                       # Este archivo
├── proceso_traduccion.md           # Guía detallada del proceso
├── layout.xml                      # Estructura ISO para reconstrucción
├── TraductorFM3.exe                # Herramienta gráfica de traducción
├── scripts/
│   ├── extraer_textos.py           # Extrae textos del juego a CSV
│   ├── traductor_fm3.py            # Código fuente de la herramienta
│   └── compilar.bat                # Genera TraductorFM3.exe
├── textos_extraidos/
│   ├── todos_los_textos.csv        # Todos los textos (28,884 entradas)
│   ├── stgdata_textos.csv          # Diálogos principales (26,827)
│   ├── ovl_textos.csv              # Menús y overlays (1,969)
│   └── slus_textos.csv             # Ejecutable (88)
└── tim_extraidos                   # Imágenes con textos pendientes de editar para reinsertar en ZDATA.BIN con tim2view_win32
```

## Inicio Rápido

### 1. Abrir la herramienta de traducción

Ejecutar `TraductorFM3.exe` y cargar `textos_extraidos/todos_los_textos.csv`.

### 2. Traducir

- **Columna "Traducción IA"**: Pegar traducciones generadas por IA
- **Columna "Traducción Revisada"**: Revisar y ajustar manualmente
- **Contador de caracteres**: Verificar que no exceda la longitud original

### 3. Guardar

Exportar el CSV con las traducciones finales.

## Herramienta de Traducción

`TraductorFM3.exe` incluye:

- Edición manual de traducciones
- Contador de caracteres con alertas visuales
- Búsqueda en tiempo real
- Filtros por tipo (diálogo, menú, misión, etc.)
- Barra de progreso de traducción
- Exportar/Importar CSV

Para regenerar el ejecutable:

```bash
cd scripts
compilar.bat
```

## Marcadores Especiales

Los textos contienen marcadores que **NO deben traducirse**:

| Marcador | Descripción |
|----------|-------------|
| `[NL]` | Salto de línea visual |
| `[NEWLINE]` | Nueva caja de diálogo |
| `[NAME_START][NAME_END]` | Nombre de personaje (runtime) |
| `[ITEM_START][ITEM_END]` | Nombre de item (runtime) |
| `[CMD]` | Comando del sistema |
| `[0xNN]` | Byte de control binario |

**Ejemplo**:

```
Original: We're ready on our side.[NL][NAME_START][NAME_END], activate the[NL]wanzer.
Traducción: Estamos listos por nuestro lado.[NL][NAME_START][NAME_END], activa el[NL]wanzer.
```

## Archivos del Juego

| Archivo | Textos | Contenido |
|---------|--------|-----------|
| STGDATA.BIN | 26,827 | Diálogos, historia, misiones, tutorial |
| OVL/*.BIN | 1,969 | Menús, correo, configuración, créditos |
| SLUS_010.11 | 88 | UI del ejecutable, opciones de batalla |
| ZDATA.BIN | - | Imagenes con las fuentes |

## Documentación Adicional

- [mkpsxiso](https://github.com/Lameguy64/mkpsxiso) - Herramientas ISO para PS1
- [tim2view_win32] - Extraer e insertar imágenes con las fuentes del juego.

## Licencia

Traducción fan sin fines de lucro. Front Mission 3 es propiedad de Square Enix.

---

**Última actualización**: 2026-06-27
