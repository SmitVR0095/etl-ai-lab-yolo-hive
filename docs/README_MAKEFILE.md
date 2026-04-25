# 🛠️ Instructivo profesional del Makefile – Proyecto YOLO + HDFS + Hive + Telegram

## 👨‍💻 Autor

**Smit Jonatan Villafranca Romero**

Este documento describe las funcionalidades configuradas en el `Makefile` del proyecto **YOLO + HDFS + Hive + Telegram**, explica cuándo usar cada comando y propone una ruta recomendada para validar el ambiente, ejecutar la detección de objetos, cargar resultados en Hive y generar evidencias técnicas.

---

## 1. 🎯 Objetivo del Makefile

El `Makefile` automatiza el flujo completo del proyecto para reducir errores manuales y facilitar la revisión técnica:

```text
YOLOv8 → CSV local → Validación CSV → HDFS → Hive → Validación SQL → Reporte → Telegram opcional
```

Permite ejecutar tareas repetitivas con comandos simples como:

```bash
make demo
make run-review
make refresh-images
make validate-csv
make report-run
```

---

## 2. ✅ Requisitos previos

Antes de usar el Makefile, se espera que el ambiente base esté instalado y configurado:

| Componente | Uso en el proyecto |
|---|---|
| Python 3.12 | Ejecución de scripts YOLO y ETL |
| Entorno virtual `etl-ai-lab` | Aislamiento de dependencias |
| YOLOv8 / Ultralytics | Detección de objetos |
| OpenCV | Lectura y escritura de imágenes/videos |
| Hadoop / HDFS | Almacenamiento distribuido |
| Hive / HiveServer2 | Consulta SQL sobre datos procesados |
| Beeline | Cliente JDBC para Hive |
| Airflow | Orquestación opcional |
| Telegram Bot | Notificaciones opcionales |

Activar el entorno virtual:

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab
source ~/cursobsgetl/ambientes/etl-ai-lab/bin/activate
```

---

## 3. 📌 Comando base de ayuda

Para ver todos los comandos disponibles:

```bash
make help
```

Este comando es el punto de entrada recomendado porque muestra las categorías principales: instalación, Hadoop, Hive, detección YOLO, validación, reportes, Telegram y flujos completos.

---

## 4. 🚦 Comandos más importantes

| Prioridad | Comando | Uso recomendado |
|---:|---|---|
| 1 | `make preflight` | Diagnóstico general del ambiente antes de ejecutar el modelo |
| 2 | `make demo` | Prueba liviana con 2 imágenes y 2 videos para detectar errores rápidamente |
| 3 | `make run-review` | Ejecución completa del flujo para revisión final |
| 4 | `make refresh-images` | Reprocesar solo imágenes cuando se cambió `data/raw/images/` |
| 5 | `make refresh-videos` | Reprocesar solo videos cuando se cambió `data/raw/videos/` |
| 6 | `make validate-csv` | Validar estructura y contenido del CSV generado |
| 7 | `make validate-hive` | Validar que Hive lea correctamente los datos |
| 8 | `make report-run` | Generar reporte Markdown de la última ejecución |
| 9 | `make run-review-notify` | Ejecutar flujo completo con notificaciones Telegram |

---

## 5. 🔍 Diagnóstico del ambiente

### `make preflight`

Ejecuta una validación general del ambiente.

```bash
make preflight
```

Usar cuando:

- Se abre una nueva sesión de WSL.
- Se clona el repositorio por primera vez.
- Se sospecha que Hadoop, Hive o Python no están correctamente activos.
- Se desea detectar errores antes de correr YOLO.

Valida principalmente:

```text
Rutas del proyecto
Python y librerías principales
Hadoop / YARN
HiveServer2
Beeline
```

---

## 6. 🧪 Demo liviana del proyecto

### `make demo`

Ejecuta una prueba controlada y ligera usando **2 imágenes y 2 videos** seleccionados desde `data/raw/`.

```bash
make demo
```

Este comando es ideal para probar rápidamente si todo el pipeline funciona sin procesar todo el dataset.

Flujo ejecutado:

```text
check-paths
start-hadoop
start-hive
hive-init
clean-yolo-state
demo-prepare
detect-demo-images
detect-demo-videos
validate-csv
load-hive
hive-final-textfile
validate-hive
count-hdfs
report-run
```

Resultado esperado:

```text
✅ Dataset demo preparado correctamente.
✅ Detección YOLO finalizada correctamente.
✅ Validación CSV finalizada correctamente.
✅ Datos cargados en Hive.
✅ Reporte generado en reports/.
```

### `make demo-prepare`

Prepara el dataset demo copiando una muestra liviana:

```bash
make demo-prepare
```

Crea o actualiza:

```text
data/demo/images/
data/demo/videos/
```

### `make detect-demo-images`

Procesa solo las 2 imágenes de la demo:

```bash
make detect-demo-images
```

### `make detect-demo-videos`

Procesa solo los 2 videos de la demo y usa `--append-csv` para no borrar las detecciones de imágenes:

```bash
make detect-demo-videos
```

---

## 7. 📦 Instalación y validación Python

### `make install-deps`

Instala dependencias Python del proyecto:

```bash
make install-deps
```

Usar cuando:

- Se acaba de crear el entorno virtual.
- Se clonó el repositorio en otra máquina.
- Faltan librerías como `ultralytics`, `opencv`, `pandas`, `torch`, etc.

### `make install`

Alias de `install-deps`:

```bash
make install
```

### `make install-telegram-deps`

Instala dependencias para Telegram:

```bash
make install-telegram-deps
```

### `make test-python`

Valida que Python y las librerías principales funcionen:

```bash
make test-python
```

Resultado esperado:

```text
python ok
cv2: ...
torch: ...
cuda: False
ultralytics ok
```

> Nota: `cuda: False` no es un error. Solo indica que el procesamiento se hará por CPU.

### `make test`

Alias de `test-python`:

```bash
make test
```

---

## 8. 📁 Validación de rutas

### `make check-paths`

Valida que existan carpetas y archivos mínimos:

```bash
make check-paths
```

Valida:

```text
src/
sql/
data/raw/images/
data/raw/videos/
models/yolov8n.pt
```

Usar antes de cualquier ejecución si se movieron archivos o se descargó el proyecto desde GitHub.

---

## 9. 🐘 Hadoop y HDFS

### `make start-hadoop`

Levanta HDFS y YARN:

```bash
make start-hadoop
```

Internamente ejecuta:

```bash
start-dfs.sh
start-yarn.sh
```

### `make status-hadoop`

Valida el estado de Hadoop:

```bash
make status-hadoop
```

Procesos esperados:

```text
NameNode
DataNode
SecondaryNameNode
ResourceManager
NodeManager
```

### `make stop-hadoop`

Detiene HDFS y YARN:

```bash
make stop-hadoop
```

---

## 10. 🐝 Hive y Beeline

### `make start-hive`

Levanta HiveServer2 en el puerto `10000`:

```bash
make start-hive
```

El target está diseñado para **no reiniciar HiveServer2 si ya está activo**.

### `make status-hive`

Valida puertos y conexión Beeline:

```bash
make status-hive
```

Valida:

```text
Puerto 10000
Puerto 10002
SHOW DATABASES con Beeline
```

### `make test-hive`

Alias de `status-hive`:

```bash
make test-hive
```

### `make stop-hive`

Detiene HiveServer2/Metastore si existieran procesos activos:

```bash
make stop-hive
```

### `make hive-init`

Crea la base y las tablas iniciales:

```bash
make hive-init
```

Ejecuta:

```text
sql/01_create_yolo_objects_tables.sql
```

### `make hive-create`

Alias de `hive-init`:

```bash
make hive-create
```

### `make hive-final-textfile`

Recrea `yolo_objects` como tabla externa `TEXTFILE` apuntando a:

```text
/projects/yolo_objects/staging
```

```bash
make hive-final-textfile
```

Usar cuando:

- Se actualizó el dataset.
- Se quiere que Hive lea directamente los CSV en HDFS.
- Se desea evitar problemas con consultas que dependan de MapReduce.

### `make hive-merge`

Alias de `hive-final-textfile`:

```bash
make hive-merge
```

---

## 11. 🧠 Detección YOLO

### `make detect-images`

Procesa imágenes desde:

```text
data/raw/images/
```

```bash
make detect-images
```

Equivalente manual:

```bash
python src/sistema_clasificacion.py --mode images --model models/yolov8n.pt
```

### `make detect-videos`

Procesa videos desde:

```text
data/raw/videos/
```

```bash
make detect-videos
```

Equivalente manual:

```bash
python src/sistema_clasificacion.py --mode videos --model models/yolov8n.pt
```

### `make detect-camera`

Procesa cámara en tiempo real:

```bash
make detect-camera
```

Usar si WSL reconoce la cámara:

```bash
ls /dev/video*
```

### `make detect-all`

Procesa imágenes y videos sin perder el CSV de imágenes:

```bash
make detect-all
```

Este target debe procesar imágenes primero y luego videos usando modo append para conservar ambos resultados en `data/staging/yolo_detections.csv`.

### `make classify-all`

Alias de `detect-all`:

```bash
make classify-all
```

---

## 12. 🧹 Limpieza y refresco de datos

### `make clean-yolo-state`

Limpia el estado del flujo YOLO/Hive:

```bash
make clean-yolo-state
```

Elimina:

```text
data/staging/yolo_detections.csv
checkpoints/yolo_hive_checkpoint.json
data/processed/hive_batches/*
data/processed/annotated/images/*
data/processed/annotated/videos/*
/projects/yolo_objects/staging en HDFS
```

No borra los archivos originales de:

```text
data/raw/images/
data/raw/videos/
```

### `make clean-all-runtime`

Limpia el estado completo de ejecución, incluyendo reportes y logs runtime:

```bash
make clean-all-runtime
```

Usar cuando se quiere una ejecución completamente nueva sin tocar el dataset original.

### `make refresh-images`

Flujo recomendado si solo se cambiaron imágenes:

```bash
make refresh-images
```

Ejecuta limpieza, detección de imágenes, validación CSV, carga a Hive, validación SQL y reporte.

### `make refresh-videos`

Flujo recomendado si solo se cambiaron videos:

```bash
make refresh-videos
```

Ejecuta limpieza, detección de videos, validación CSV, carga a Hive, validación SQL y reporte.

---

## 13. 📄 CSV, carga a Hive y validaciones

### `make validate-csv`

Valida el CSV generado por YOLO:

```bash
make validate-csv
```

Revisa:

```text
Existencia del archivo
Lectura correcta con pandas
Columnas obligatorias
Cantidad de registros
Duplicados en detection_id
Clases detectadas
Fuentes procesadas
```

Archivo validado:

```text
data/staging/yolo_detections.csv
```

### `make load-hive`

Carga el CSV a HDFS/Hive:

```bash
make load-hive
```

Este comando:

1. Lee `data/staging/yolo_detections.csv`.
2. Genera lotes en `data/processed/hive_batches/`.
3. Sube archivos a HDFS.
4. Carga registros en `yolo_objects_csv_stage`.

### `make etl-hive`

Alias de `load-hive`:

```bash
make etl-hive
```

### `make validate-hive`

Consulta datos desde Hive:

```bash
make validate-hive
```

Consulta esperada:

```sql
SELECT source_id, class_name, confidence
FROM yolo_objects
LIMIT 20;
```

### `make validate-hive-sample`

Muestra una muestra completa de registros:

```bash
make validate-hive-sample
```

### `make count-hdfs`

Cuenta registros directamente desde HDFS:

```bash
make count-hdfs
```

Equivalente:

```bash
hdfs dfs -cat /projects/yolo_objects/staging/* | wc -l
```

### `make list-hdfs`

Lista archivos cargados en HDFS:

```bash
make list-hdfs
```

---

## 14. 📊 Reportes automáticos

### `make report-run`

Genera un reporte Markdown de la última ejecución:

```bash
make report-run
```

Salida esperada:

```text
reports/resumen_ejecucion_YYYYMMDD_HHMMSS.md
reports/hive_sample_YYYYMMDD_HHMMSS.txt
```

El reporte incluye:

```text
Fecha de ejecución
Total de imágenes/videos disponibles
Filas del CSV
Clases detectadas
Fuentes procesadas
Conteo desde HDFS
Muestra de Hive
```

Este comando es útil para dejar evidencia técnica de cada corrida.

---

## 15. 📲 Telegram

### `make telegram-test`

Envía un mensaje de prueba:

```bash
make telegram-test
```

Configurar previamente:

```bash
cp .env.telegram.example .env.telegram
nano .env.telegram
```

Contenido esperado:

```text
TELEGRAM_BOT_TOKEN=<TOKEN_TELEGRAM>
TELEGRAM_CHAT_ID=<CHAT_ID>
```

### `make telegram-start`

Envía notificación de inicio:

```bash
make telegram-start
```

### `make telegram-ok`

Envía notificación de éxito:

```bash
make telegram-ok
```

### `make telegram-error`

Envía notificación de error:

```bash
make telegram-error
```

### `make detect-images-notify`

Detecta imágenes y notifica por Telegram:

```bash
make detect-images-notify
```

### `make detect-videos-notify`

Detecta videos y notifica por Telegram:

```bash
make detect-videos-notify
```

### `make load-hive-notify`

Carga a Hive y notifica:

```bash
make load-hive-notify
```

---

## 16. 🚀 Flujos completos

### `make run-review`

Ejecuta el flujo completo sin Telegram:

```bash
make run-review
```

Incluye:

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

Usar para la revisión principal del proyecto.

### `make run-review-notify`

Ejecuta el flujo completo con Telegram:

```bash
make run-review-notify
```

Usar cuando se desea recibir notificaciones de inicio, finalización o error.

---

## 17. 🌬️ Airflow y limpieza Python

### `make airflow-start`

Inicia Airflow Webserver y Scheduler:

```bash
make airflow-start
```

URL esperada:

```text
http://localhost:8080
```

### `make airflow-stop`

Detiene procesos Airflow:

```bash
make airflow-stop
```

### `make clean`

Limpia archivos Python temporales:

```bash
make clean
```

Elimina:

```text
__pycache__/
*.pyc
```

### `make clean-runtime`

Limpia salidas procesadas locales:

```bash
make clean-runtime
```

---

## 18. 🧭 Recomendaciones de uso

| Escenario | Comando recomendado |
|---|---|
| Quiero ver todos los comandos | `make help` |
| Quiero diagnosticar ambiente | `make preflight` |
| Quiero probar rápido con pocos archivos | `make demo` |
| Quiero ejecutar el proyecto completo | `make run-review` |
| Cambié solo imágenes | `make refresh-images` |
| Cambié solo videos | `make refresh-videos` |
| Quiero validar CSV | `make validate-csv` |
| Quiero validar Hive | `make validate-hive` |
| Quiero generar evidencia | `make report-run` |
| Quiero usar Telegram | `make run-review-notify` |
| Quiero limpiar ejecución | `make clean-yolo-state` |
| Quiero apagar Hive | `make stop-hive` |
| Quiero apagar Hadoop | `make stop-hadoop` |

---

## 19. 🧑‍🏫 Flujo recomendado para revisión

### Revisión rápida

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab
source ~/cursobsgetl/ambientes/etl-ai-lab/bin/activate
make demo
```

### Revisión completa

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab
source ~/cursobsgetl/ambientes/etl-ai-lab/bin/activate
make run-review
```

### Revisión con Telegram

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab
source ~/cursobsgetl/ambientes/etl-ai-lab/bin/activate
cp .env.telegram.example .env.telegram
nano .env.telegram
make telegram-test
make run-review-notify
```

---

## 20. ⚠️ Buenas prácticas

- Ejecutar `make preflight` antes de la revisión final.
- Usar `make demo` para detectar errores rápidamente.
- Usar `make run-review` para validar todo el pipeline.
- No subir imágenes/videos originales al repositorio si son pesados.
- Entregar multimedia como comprimido aparte.
- No subir `.env.telegram` ni tokens reales a GitHub.
- Conservar los reportes en `reports/` como evidencia técnica.
- Usar `make clean-yolo-state` cuando se reemplacen imágenes o videos.

---

## 21. ✅ Resumen operativo

```text
Ambiente nuevo       → make install-deps
Diagnóstico          → make preflight
Demo rápida          → make demo
Solo imágenes        → make refresh-images
Solo videos          → make refresh-videos
Flujo completo       → make run-review
Con Telegram         → make run-review-notify
Reporte evidencia    → make report-run
```

Este instructivo permite usar el Makefile como una consola operativa profesional para ejecutar, validar, depurar y documentar el flujo completo del proyecto._久久爱_FINAL답 needs provide updated file maybe. Use uploaded existing cite. Must create file. Could write to /mnt/data README_MAKEFILE_actualizado.md maybe already did in analysis, but not zip. Need maybe mention based on current file. We need produce link. Already generated file in analysis. Could make zip too. Need final concise with link. Need cite file. Since cite uploaded. Ensure file exists. Use container maybe zip. Also maybe mention copy commands. Need maybe include 
