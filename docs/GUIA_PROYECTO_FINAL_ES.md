# Guía del Proyecto Final – Deep Learning, Visión por Computador y Big Data

## 1. Objetivo

Construir una solución que detecte objetos con YOLO en imágenes, videos y cámara, registre cada detección en CSV local y posteriormente cargue la información procesada en Apache Hive sin duplicados.

## 2. Flujo general

```text
Imágenes/Videos/Cámara
        ↓
Sistema de Clasificación YOLO
        ↓
CSV staging local
        ↓
Sistema Batch ETL Python
        ↓
CSV batch por ventana de 10 segundos
        ↓
HDFS + Hive staging
        ↓
Tabla final Hive sin duplicados
```

## 3. Sistema de Clasificación

Archivo principal: `src/sistema_clasificacion.py`.

Responsabilidades:

- Cargar `models/yolov8n.pt`.
- Procesar `data/raw/images` y `data/raw/videos`.
- Procesar cámara con `--mode camera`.
- Generar `data/staging/yolo_detections.csv`.
- Generar imágenes/videos anotados en `data/processed/annotated`.

Campos principales generados:

- Identificación: `detection_id`, `source_type`, `source_id`, `frame_number`.
- Modelo: `class_id`, `class_name`, `confidence`.
- Bounding box: coordenadas, ancho, alto, área y ratio.
- Posición: centro normalizado y región 3x3.
- Color dominante: nombre y componentes RGB.
- Video: `timestamp_sec`, `fps`.
- Personas: flags básicos opcionales.

## 4. Sistema Batch / ETL

Archivo principal: `src/sistema_batch_etl.py`.

Responsabilidades:

- Leer CSV de staging.
- Validar columnas.
- Eliminar duplicados por `detection_id`.
- Limpiar confidencias inválidas y bounding boxes inconsistentes.
- Crear ventanas `[0-10)`, `[10-20)`, etc. usando `timestamp_sec`.
- Cargar lotes a Hive vía `hdfs dfs` y `beeline`.
- Mantener checkpoint local en `checkpoints/yolo_hive_checkpoint.json`.

## 5. Hive

Scripts:

- `sql/01_create_yolo_objects_tables.sql`: crea base, tabla staging CSV y tabla final Parquet.
- `sql/02_merge_without_duplicates.sql`: consolida staging y final sin duplicados.
- `sql/03_analytics_queries.sql`: consultas analíticas requeridas.

## 6. Ejecución recomendada

```bash
make install
make test
make hive-create
make classify-all
make etl-hive
make hive-merge
```

## 7. Evidencias sugeridas

Incluye capturas de:

1. Carpeta con al menos 20 imágenes y 2 videos propios.
2. Ejecución de YOLO generando el CSV.
3. CSV de staging con detecciones.
4. Ejecución del ETL.
5. Tabla Hive poblada.
6. Consultas analíticas ejecutadas.
7. Pruebas unitarias pasando.
