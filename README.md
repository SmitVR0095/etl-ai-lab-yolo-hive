# 🧠 Proyecto Final – Deep Learning, Visión por Computador y Big Data

## 👨‍💻 Creador del proyecto

**Smit Jonatan Villafranca Romero**

Proyecto desarrollado como una solución integral de detección de objetos usando **Deep Learning**, **visión por computador** y herramientas de **Big Data** para almacenar, procesar y consultar resultados mediante Apache Hive.

---

## 🎯 1. Objetivo del proyecto

Construir una solución funcional que permita detectar objetos en **imágenes**, **videos** y **cámara en tiempo real** usando **YOLOv8**, registrar cada detección en un archivo CSV, procesar los resultados mediante un flujo Batch ETL, cargar la información en **HDFS** y exponerla en **Apache Hive** para análisis mediante SQL.

El proyecto está diseñado para ser ejecutado de forma manual o automatizada mediante **Makefile**, incluyendo flujos completos, flujos por tipo de dato, demo liviana, validaciones, reportes y notificaciones opcionales por Telegram.

---

## 🧩 2. Tecnologías utilizadas

| Tecnología | Uso dentro del proyecto |
|---|---|
| 🐍 Python | Desarrollo de scripts de clasificación, ETL, validación y reportes |
| 🧠 YOLOv8 / Ultralytics | Detección de objetos en imágenes, videos y cámara |
| 👁️ OpenCV | Lectura, procesamiento y anotación de imágenes/videos |
| 🐼 Pandas | Manipulación y validación del CSV de detecciones |
| 🐘 Apache Hadoop / HDFS | Almacenamiento distribuido de lotes CSV |
| 🐝 Apache Hive | Consulta analítica de detecciones mediante SQL |
| ⚡ Apache Spark | Componente Big Data complementario del entorno |
| 🌬️ Apache Airflow | Orquestación del pipeline mediante DAGs |
| 🛠️ Makefile | Automatización de instalación, validación, ejecución y limpieza |
| 📲 Telegram | Notificaciones opcionales de ejecución |

---

## 🏗️ 3. Arquitectura general

```text
Imágenes / Videos / Cámara
        ↓
Sistema de Clasificación YOLOv8
        ↓
CSV local de detecciones
        data/staging/yolo_detections.csv
        ↓
Proceso Batch ETL en Python
        ↓
Lotes CSV procesados
        data/processed/hive_batches/
        ↓
HDFS
        /projects/yolo_objects/staging
        ↓
Apache Hive
        yolo_project.yolo_objects
        ↓
Consultas SQL con Beeline
        ↓
Reporte automático de ejecución
        reports/resumen_ejecucion_*.md
```

---

## 🗂️ 4. Estructura actual del proyecto

```text
etl-ai-lab/
├── Makefile
├── README.md
├── requirements.txt
├── .env.example
├── .env.telegram.example
├── .gitignore
├── airflow_env.sh
├── start_webserver.sh
├── start_scheduler.sh
│
├── airflow/
│   ├── dags/
│   │   ├── etl_pipeline_demo.py
│   │   └── yolo_hive_pipeline_dag.py
│   ├── data/
│   ├── logs/
│   ├── plugins/
│   ├── runtime/
│   └── tests/
│
├── configs/
│   ├── spark-defaults.conf
│   └── spark-env.sh
│
├── data/
│   ├── raw/
│   │   ├── images/
│   │   │   └── .gitkeep
│   │   └── videos/
│   │       └── .gitkeep
│   │
│   ├── demo/
│   │   ├── images/
│   │   │   └── .gitkeep
│   │   └── videos/
│   │       └── .gitkeep
│   │
│   ├── staging/
│   │   ├── .gitkeep
│   │   └── yolo_detections.csv
│   │
│   └── processed/
│       ├── hive_batches/
│       └── annotated/
│           ├── images/
│           └── videos/
│
├── docs/
│   ├── GUIA_PROYECTO_FINAL_ES.md
│   ├── README_MAKEFILE.md
│   ├── FUENTES_DATOS_MULTIMEDIA.md
│   ├── INSTRUCCIONES_MAKE_TELEGRAM.md
│   └── evidencias/
│       └── .gitkeep
│
├── docker/
│   └── docker-compose.yml
│
├── logs/
│   └── hiveserver2.log
│
├── reports/
│   ├── resumen_ejecucion_*.md
│   └── hive_sample_*.txt
│
├── checkpoints/
│   └── .gitkeep
│
├── models/
│   └── README.md
│
├── scripts/
│   ├── generate_run_report.py
│   ├── run_spark_local.sh
│   ├── run_with_telegram.sh
│   ├── setup_project_dirs.sh
│   ├── telegram_notify.py
│   └── validate_yolo_csv.py
│
├── spark_jobs/
│   ├── transform_job.py
│   └── utils/
│
├── sql/
│   ├── 01_create_yolo_objects_tables.sql
│   ├── 02_merge_without_duplicates.sql
│   └── 03_analytics_queries.sql
│
├── src/
│   ├── console_utils.py
│   ├── sistema_clasificacion.py
│   ├── sistema_batch_etl.py
│   └── yolo_features.py
│
└── tests/
    ├── test_batch_etl.py
    └── test_yolo_features.py
```

---

## 📁 5. Carpetas principales

| Carpeta | Descripción |
|---|---|
| `src/` | Código principal de detección YOLO, ETL y utilidades de consola |
| `scripts/` | Scripts auxiliares, validación CSV, reportes y Telegram |
| `sql/` | Scripts SQL para crear tablas y consultas Hive |
| `data/raw/images/` | Carpeta donde se colocan imágenes originales de entrada |
| `data/raw/videos/` | Carpeta donde se colocan videos originales de entrada |
| `data/demo/images/` | Carpeta temporal con 2 imágenes seleccionadas para demo liviana |
| `data/demo/videos/` | Carpeta temporal con 2 videos seleccionados para demo liviana |
| `data/staging/` | Carpeta donde se genera `yolo_detections.csv` |
| `data/processed/hive_batches/` | Lotes CSV generados para carga a HDFS/Hive |
| `data/processed/annotated/` | Imágenes y videos anotados por YOLO |
| `reports/` | Reportes automáticos de ejecución y muestras Hive |
| `models/` | Carpeta esperada para `yolov8n.pt` |
| `docs/` | Documentación técnica del proyecto |
| `airflow/` | DAGs y configuración de Airflow |
| `spark_jobs/` | Jobs Spark complementarios |
| `checkpoints/` | Control de registros procesados por el ETL |
| `logs/` | Logs de servicios y ejecución |

---

## 🧠 6. Sistema de clasificación YOLO

Archivo principal:

```text
src/sistema_clasificacion.py
```

Responsabilidades:

- Cargar el modelo `models/yolov8n.pt`.
- Procesar imágenes desde `data/raw/images/`.
- Procesar videos desde `data/raw/videos/`.
- Procesar cámara con `--mode camera`.
- Procesar carpetas personalizadas mediante parámetros `--images` y `--videos`.
- Regenerar el CSV en cada ejecución limpia.
- Permitir acumulación controlada con `--append-csv`.
- Generar imágenes/videos anotados en `data/processed/annotated/`.
- Mostrar mensajes interactivos con iconos y resumen final.

Campos principales generados:

| Grupo | Campos |
|---|---|
| Identificación | `detection_id`, `source_type`, `source_id`, `frame_number`, `local_object_id` |
| Modelo | `class_id`, `class_name`, `confidence` |
| Bounding box | `x_min`, `y_min`, `x_max`, `y_max`, `width`, `height`, `area_pixels` |
| Frame | `frame_width`, `frame_height`, `bbox_area_ratio` |
| Posición | `center_x`, `center_y`, `center_x_norm`, `center_y_norm`, `position_region` |
| Color dominante | `dominant_color_name`, `dom_r`, `dom_g`, `dom_b` |
| Video | `timestamp_sec`, `fps` |
| Enriquecimiento | `has_backpack`, `has_cellphone`, `nearby_objects_count` |
| Batch | `batch_window_start`, `batch_window_end` |

---

## 🔄 7. Sistema Batch ETL

Archivo principal:

```text
src/sistema_batch_etl.py
```

Responsabilidades:

- Leer el CSV generado por YOLO.
- Validar columnas obligatorias.
- Eliminar duplicados por `detection_id`.
- Limpiar datos inválidos.
- Generar lotes CSV.
- Subir lotes a HDFS.
- Cargar datos en Hive staging.
- Mantener checkpoint local.
- Mostrar mensajes interactivos con iconos, validaciones y resumen final.

Checkpoint:

```text
checkpoints/yolo_hive_checkpoint.json
```

---

## 🐝 8. Apache Hive

Base de datos usada:

```sql
yolo_project
```

Tablas principales:

| Tabla | Descripción |
|---|---|
| `yolo_objects_csv_stage` | Tabla externa staging sobre archivos CSV cargados en HDFS |
| `yolo_objects` | Tabla final consultable desde Hive |

Scripts SQL:

```text
sql/01_create_yolo_objects_tables.sql
sql/02_merge_without_duplicates.sql
sql/03_analytics_queries.sql
```

Validación manual:

```bash
beeline -u jdbc:hive2://localhost:10000/yolo_project \
  -n smit_vr \
  -e "SELECT source_id, class_name, confidence FROM yolo_objects LIMIT 20;"
```

---

## 🛠️ 9. Automatización con Makefile

El proyecto cuenta con un `Makefile` que automatiza instalación, validación, servicios Big Data, detección YOLO, carga a Hive, reportes, demo y notificaciones.

Ver comandos disponibles:

```bash
make help
```

Documento detallado:

```text
docs/README_MAKEFILE.md
```

---

## 🚀 10. Flujos principales de ejecución

### 10.1. Diagnóstico del ambiente

```bash
make preflight
```

Valida rutas, dependencias Python, Hadoop y Hive.

---

### 10.2. Demo liviana

```bash
make demo
```

Este flujo selecciona automáticamente:

```text
2 imágenes desde data/raw/images/
2 videos desde data/raw/videos/
```

y los copia temporalmente a:

```text
data/demo/images/
data/demo/videos/
```

Luego ejecuta el flujo real:

```text
YOLO → CSV → validación CSV → HDFS → Hive → validación Hive → reporte
```

La demo es útil para verificar rápidamente que todo funciona sin procesar el dataset completo.

---

### 10.3. Flujo completo

```bash
make run-review
```

Ejecuta:

```text
check-paths
start-hadoop
start-hive
hive-init
clean-yolo-state
detect-all
validate-csv
load-hive
hive-final-textfile
validate-hive
count-hdfs
report-run
```

Usar cuando se desea ejecutar el proyecto completo con imágenes y videos.

---

### 10.4. Solo imágenes

```bash
make refresh-images
```

Usar cuando se agregaron, eliminaron o reemplazaron imágenes en:

```text
data/raw/images/
```

Este comando limpia el estado anterior, procesa solo imágenes, valida CSV, carga a Hive y genera reporte.

---

### 10.5. Solo videos

```bash
make refresh-videos
```

Usar cuando se agregaron, eliminaron o reemplazaron videos en:

```text
data/raw/videos/
```

Este comando limpia el estado anterior, procesa solo videos, valida CSV, carga a Hive y genera reporte.

---

## ✅ 11. Validaciones y reportes

### Validar CSV

```bash
make validate-csv
```

Ejecuta:

```text
scripts/validate_yolo_csv.py
```

Valida que `data/staging/yolo_detections.csv` exista, tenga registros y contenga columnas obligatorias.

---

### Generar reporte automático

```bash
make report-run
```

Genera archivos en:

```text
reports/
```

Ejemplos:

```text
reports/resumen_ejecucion_YYYYMMDD_HHMMSS.md
reports/hive_sample_YYYYMMDD_HHMMSS.txt
```

Estos reportes documentan la ejecución, cantidad de registros, fuentes procesadas, clases detectadas y muestra de datos desde Hive.

---

### Contar registros desde HDFS

```bash
make count-hdfs
```

Cuenta registros directamente desde:

```text
/projects/yolo_objects/staging
```

---

## 📲 12. Ejecución con Telegram

Configurar credenciales:

```bash
cp .env.telegram.example .env.telegram
nano .env.telegram
```

Completar:

```text
TELEGRAM_BOT_TOKEN=<TOKEN_TELEGRAM>
TELEGRAM_CHAT_ID=<CHAT_ID>
```

Probar Telegram:

```bash
make telegram-test
```

Ejecutar flujo completo con notificaciones:

```bash
make run-review-notify
```

También existen comandos con notificación para procesos específicos:

```bash
make detect-images-notify
make detect-videos-notify
make load-hive-notify
```

---

## 📦 13. Dataset multimedia

Las imágenes y videos originales **no se incluyen directamente en GitHub** para evitar subir archivos pesados.

El dataset multimedia se entrega como archivo comprimido aparte. Después de descomprimirlo, debe quedar así:

```text
data/raw/images/
data/raw/videos/
```

Las fuentes públicas utilizadas fueron:

- Imágenes desde Pexels:  
  https://www.pexels.com/es-es/buscar/datos/

- Videos desde Pixabay:  
  https://pixabay.com/es/videos/search/personas/

Mayor detalle:

```text
docs/FUENTES_DATOS_MULTIMEDIA.md
```

---

## 📊 14. Evidencia esperada en Hive

Consulta de validación:

```bash
beeline -u jdbc:hive2://localhost:10000/yolo_project \
  -n smit_vr \
  -e "SELECT source_id, class_name, confidence FROM yolo_objects LIMIT 20;"
```

Ejemplo esperado:

```text
source_id                         class_name    confidence
pexels-alphatradezone-5831343.jpg person        0.91
10030-222013928.mp4               person        0.87
1643-148614430.mp4                person        0.82
```

---

## 🧪 15. Pruebas unitarias

Ejecutar pruebas:

```bash
pytest tests/
```

Archivos principales:

```text
tests/test_batch_etl.py
tests/test_yolo_features.py
```

---

## 🧹 16. Limpieza y mantenimiento

Limpiar estado YOLO/Hive:

```bash
make clean-yolo-state
```

Limpiar runtime completo sin borrar `data/raw`:

```bash
make clean-all-runtime
```

Limpiar archivos Python temporales:

```bash
make clean
```

---

## 📌 17. Casos de uso recomendados

| Escenario | Comando |
|---|---|
| Ver comandos disponibles | `make help` |
| Validar ambiente | `make preflight` |
| Probar rápido con 2 imágenes y 2 videos | `make demo` |
| Ejecutar todo el flujo | `make run-review` |
| Procesar solo imágenes | `make refresh-images` |
| Procesar solo videos | `make refresh-videos` |
| Validar CSV generado | `make validate-csv` |
| Cargar a Hive | `make load-hive` |
| Validar Hive | `make validate-hive` |
| Generar reporte | `make report-run` |
| Ejecutar con Telegram | `make run-review-notify` |
| Limpiar estado | `make clean-yolo-state` |

---

## ✅ 18. Resultado final

El proyecto demuestra un flujo integral de visión por computador y Big Data:

```text
YOLOv8 detecta objetos
        ↓
Python genera CSV estructurado
        ↓
Batch ETL valida y prepara lotes
        ↓
HDFS almacena resultados
        ↓
Hive expone tabla consultable
        ↓
Beeline valida los datos
        ↓
Makefile automatiza la ejecución
        ↓
Reportes documentan la corrida
        ↓
Telegram notifica eventos opcionales
```

---

## 🚦 19. Revisión rápida

Para revisión rápida del proyecto:

```bash
make demo
```

Para revisión completa:

```bash
make run-review
```

Para revisión completa con Telegram:

```bash
make run-review-notify
```
