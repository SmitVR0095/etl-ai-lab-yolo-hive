# 🧠 Proyecto Final – Deep Learning, Visión por Computador y Big Data

## 👨‍💻 Creador del proyecto

**Smit Jonatan Villafranca Romero**

Proyecto desarrollado como una solución integral de detección de objetos usando técnicas de Deep Learning, visión por computador y almacenamiento analítico en Big Data.

---

## 🎯 1. Objetivo del proyecto

Construir una solución funcional que permita detectar objetos en **imágenes**, **videos** y **cámara en tiempo real** usando YOLOv8, registrar las detecciones en un archivo CSV local, cargar la información procesada en **HDFS** y exponerla en **Apache Hive** para su análisis mediante SQL.

El proyecto integra:

- 🧠 Deep Learning
- 👁️ Visión por computador
- 🐍 Python
- 🐘 Apache Hadoop / HDFS
- 🐝 Apache Hive
- 🌬️ Apache Airflow
- ⚡ Apache Spark
- 🛠️ Makefile
- 📲 Telegram para notificaciones opcionales

---

## 🧩 2. Arquitectura general

```text
Imágenes / Videos / Cámara
        ↓
YOLOv8 - Sistema de Clasificación
        ↓
CSV local de detecciones
data/staging/yolo_detections.csv
        ↓
Proceso Batch ETL en Python
        ↓
CSV por lotes / ventanas de procesamiento
data/processed/hive_batches/
        ↓
HDFS
/projects/yolo_objects/staging
        ↓
Apache Hive
yolo_project.yolo_objects
        ↓
Consultas SQL con Beeline
```

---

## 🗂️ 3. Estructura del proyecto

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
│   ├── staging/
│   │   ├── .gitkeep
│   │   └── yolo_detections.csv
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
├── checkpoints/
│   └── .gitkeep
│
├── models/
│   └── README.md
│
├── scripts/
│   ├── run_spark_local.sh
│   ├── setup_project_dirs.sh
│   ├── telegram_notify.py
│   └── run_with_telegram.sh
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
│   ├── sistema_clasificacion.py
│   ├── sistema_batch_etl.py
│   └── yolo_features.py
│
└── tests/
    ├── test_batch_etl.py
    └── test_yolo_features.py
```

---

## 📁 4. Carpetas principales

| Carpeta | Descripción |
|---|---|
| `src/` | Código principal de detección YOLO y carga batch a Hive |
| `sql/` | Scripts SQL para crear tablas y consultas Hive |
| `data/raw/images/` | Carpeta donde se colocan imágenes de entrada |
| `data/raw/videos/` | Carpeta donde se colocan videos de entrada |
| `data/staging/` | Carpeta donde se genera el CSV `yolo_detections.csv` |
| `data/processed/` | Carpeta para lotes procesados y salidas anotadas |
| `models/` | Carpeta esperada para el modelo `yolov8n.pt` |
| `scripts/` | Scripts auxiliares y notificaciones Telegram |
| `docs/` | Documentación del proyecto |
| `airflow/` | DAGs y configuración de Apache Airflow |
| `spark_jobs/` | Jobs Spark del proyecto |
| `checkpoints/` | Checkpoints de carga ETL |
| `logs/` | Logs de HiveServer2 y procesos auxiliares |

---

## 🧠 5. Sistema de clasificación YOLO

Archivo principal:

```text
src/sistema_clasificacion.py
```

Responsabilidades:

- Cargar el modelo `models/yolov8n.pt`.
- Procesar imágenes desde `data/raw/images/`.
- Procesar videos desde `data/raw/videos/`.
- Procesar cámara con `--mode camera`.
- Generar `data/staging/yolo_detections.csv`.
- Generar salidas anotadas en `data/processed/annotated/`.

Campos principales generados:

| Grupo | Campos |
|---|---|
| Identificación | `detection_id`, `source_type`, `source_id`, `frame_number` |
| Modelo | `class_id`, `class_name`, `confidence` |
| Bounding box | `x_min`, `y_min`, `x_max`, `y_max`, `width`, `height`, `area_pixels` |
| Posición | `center_x`, `center_y`, `center_x_norm`, `center_y_norm`, `position_region` |
| Color dominante | `dominant_color_name`, `dom_r`, `dom_g`, `dom_b` |
| Video | `timestamp_sec`, `fps` |
| Enriquecimiento | `has_backpack`, `has_cellphone`, `nearby_objects_count` |

---

## 🔄 6. Sistema Batch ETL

Archivo principal:

```text
src/sistema_batch_etl.py
```

Responsabilidades:

- Leer el CSV generado por YOLO.
- Validar columnas.
- Eliminar duplicados por `detection_id`.
- Limpiar datos inválidos.
- Generar lotes de carga.
- Subir archivos a HDFS.
- Cargar información en Hive.
- Mantener checkpoint local.

Checkpoint:

```text
checkpoints/yolo_hive_checkpoint.json
```

---

## 🐝 7. Hive

Base de datos usada:

```sql
yolo_project
```

Tablas principales:

| Tabla | Descripción |
|---|---|
| `yolo_objects_csv_stage` | Tabla staging sobre archivos CSV |
| `yolo_objects` | Tabla final consultable desde Hive |

Scripts:

```text
sql/01_create_yolo_objects_tables.sql
sql/02_merge_without_duplicates.sql
sql/03_analytics_queries.sql
```

---

## 🛠️ 8. Automatización con Makefile

El proyecto cuenta con un `Makefile` para automatizar el flujo completo.

Ver comandos disponibles:

```bash
make help
```

Documento detallado del Makefile:

```text
docs/README_MAKEFILE.md
```

---

## 🚀 9. Ejecución rápida

### Ejecutar todo el flujo completo

```bash
make run-review
```

Este comando:

1. Valida rutas.
2. Levanta Hadoop/YARN.
3. Levanta HiveServer2.
4. Crea tablas Hive.
5. Limpia estado anterior.
6. Procesa imágenes.
7. Procesa videos.
8. Carga CSV a HDFS/Hive.
9. Valida resultados en Hive.
10. Cuenta registros desde HDFS.

---

## 🖼️ 10. Procesar solo imágenes

Cuando se agregan o reemplazan imágenes en:

```text
data/raw/images/
```

ejecutar:

```bash
make refresh-images
```

---

## 🎬 11. Procesar solo videos

Cuando se agregan o reemplazan videos en:

```text
data/raw/videos/
```

ejecutar:

```bash
make refresh-videos
```

---

## 📲 12. Ejecución con Telegram

Configurar:

```bash
cp .env.telegram.example .env.telegram
nano .env.telegram
```

Completar:

```text
TELEGRAM_BOT_TOKEN=<TOKEN_TELEGRAM>
TELEGRAM_CHAT_ID=<CHAT_ID>
```

Probar:

```bash
make telegram-test
```

Ejecutar flujo completo con notificaciones:

```bash
make run-review-notify
```

---

## 📦 13. Dataset multimedia

Las imágenes y videos originales **no se incluyen directamente en GitHub** para evitar subir archivos pesados.

El dataset multimedia se entrega como archivo comprimido aparte.

Después de descomprimirlo, debe quedar así:

```text
data/raw/images/
data/raw/videos/
```

Fuentes:

- Imágenes públicas desde Pexels:  
  https://www.pexels.com/es-es/buscar/datos/

- Videos públicos desde Pixabay:  
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
source_id              class_name    confidence
Amiga_Giane_001.jpg    person        0.916737
Amiga_Giane_002.jpg    person        0.883236
Equipo_Darwin.jpg      person        0.859373
```

---

## 🧪 15. Pruebas

Ejecutar pruebas unitarias:

```bash
pytest tests/
```

---

## ✅ 16. Resultado final

El proyecto demuestra un flujo integral:

```text
YOLOv8 detecta objetos
        ↓
Python genera CSV
        ↓
ETL procesa lotes
        ↓
HDFS almacena archivos
        ↓
Hive expone tabla consultable
        ↓
Beeline valida resultados
        ↓
Makefile automatiza el flujo
        ↓
Telegram notifica eventos opcionales
```

---

## 📌 17. Revisión rápida del profesor

Sin Telegram:

```bash
make run-review
```

Con Telegram:

```bash
make run-review-notify
```
