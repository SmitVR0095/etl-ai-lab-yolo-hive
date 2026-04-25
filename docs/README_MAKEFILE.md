# 🛠️ Instructivo del Makefile – Proyecto YOLO + HDFS + Hive + Telegram

## 1. Objetivo

Este documento explica los comandos configurados en el `Makefile`, cuándo deben utilizarse y qué parte del flujo ejecuta cada uno.

El `Makefile` permite automatizar el proyecto completo:

```text
YOLOv8 → CSV → HDFS → Hive → Validación SQL → Telegram opcional
```

---

## 2. Ver comandos disponibles

```bash
make help
```

Este comando muestra todos los targets disponibles.

---

## 3. Comandos de instalación y validación

### `make install-deps`

Instala las dependencias Python del proyecto.

Usar cuando:

- Se acaba de clonar el repositorio.
- Se creó un entorno virtual nuevo.
- Faltan librerías como `ultralytics`, `opencv`, `pandas`, etc.

```bash
make install-deps
```

---

### `make install-telegram-deps`

Instala dependencias necesarias para Telegram, principalmente `requests`.

Usar cuando se desea activar notificaciones por Telegram.

```bash
make install-telegram-deps
```

---

### `make test-python`

Valida que las principales librerías Python funcionen correctamente.

```bash
make test-python
```

Valida:

- `cv2`
- `pandas`
- `torch`
- `ultralytics`

Resultado esperado:

```text
python ok
cv2: ...
torch: ...
cuda: False
ultralytics ok
```

---

### `make check-paths`

Valida que existan las rutas principales del proyecto.

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

Usar antes de ejecutar el flujo completo.

---

## 4. Comandos de Hadoop y YARN

### `make start-hadoop`

Levanta HDFS y YARN.

```bash
make start-hadoop
```

Internamente ejecuta:

```bash
start-dfs.sh
start-yarn.sh
```

Usar cuando:

- Se inicia WSL.
- Se reinició la máquina.
- Hadoop no está activo.

---

### `make status-hadoop`

Muestra el estado de Hadoop/YARN.

```bash
make status-hadoop
```

Valida:

- Procesos Java con `jps -l`.
- Nodos YARN con `yarn node -list`.
- Directorios HDFS con `hdfs dfs -ls /`.

Procesos esperados:

```text
NameNode
DataNode
SecondaryNameNode
ResourceManager
NodeManager
```

---

### `make stop-hadoop`

Detiene HDFS y YARN.

```bash
make stop-hadoop
```

Usar cuando se desea cerrar el ambiente Big Data.

---

## 5. Comandos de Hive

### `make start-hive`

Levanta HiveServer2 en el puerto `10000`.

```bash
make start-hive
```

Usar cuando:

- HiveServer2 no está activo.
- Se necesita conexión Beeline.
- Se va a cargar o consultar información en Hive.

El target está configurado para no reiniciar Hive si ya está activo.

---

### `make status-hive`

Valida HiveServer2.

```bash
make status-hive
```

Valida:

- Puerto `10000`.
- Puerto `10002`.
- Conexión Beeline.
- Ejecución de `SHOW DATABASES`.

---

### `make stop-hive`

Detiene HiveServer2 y Metastore si existieran procesos activos.

```bash
make stop-hive
```

Usar cuando:

- Hive quedó colgado.
- Se requiere reiniciar Hive.
- Se desea apagar servicios.

---

### `make hive-init`

Crea la base y tablas iniciales de Hive.

```bash
make hive-init
```

Ejecuta:

```text
sql/01_create_yolo_objects_tables.sql
```

Crea:

```text
yolo_project
yolo_objects_csv_stage
yolo_objects
```

---

### `make hive-final-textfile`

Recrea `yolo_objects` como tabla externa `TEXTFILE` apuntando a:

```text
/projects/yolo_objects/staging
```

```bash
make hive-final-textfile
```

Usar cuando:

- Se desea evitar problemas con `COUNT(*)` o MapReduce.
- Se quiere que Hive lea directamente los CSV cargados en HDFS.
- Se actualizó el dataset y se desea refrescar la tabla final.

---

## 6. Comandos de detección YOLO

### `make detect-images`

Ejecuta detección sobre imágenes.

```bash
make detect-images
```

Lee imágenes desde:

```text
data/raw/images/
```

Genera:

```text
data/staging/yolo_detections.csv
```

Equivalente manual:

```bash
python src/sistema_clasificacion.py --mode images --model models/yolov8n.pt
```

---

### `make detect-videos`

Ejecuta detección sobre videos.

```bash
make detect-videos
```

Lee videos desde:

```text
data/raw/videos/
```

Genera o actualiza:

```text
data/staging/yolo_detections.csv
```

Equivalente manual:

```bash
python src/sistema_clasificacion.py --mode videos --model models/yolov8n.pt
```

---

### `make detect-camera`

Ejecuta detección usando cámara.

```bash
make detect-camera
```

Usar si WSL reconoce la cámara en:

```text
/dev/video0
```

Validar cámara:

```bash
ls /dev/video*
```

---

### `make detect-all`

Ejecuta detección sobre imágenes y videos.

```bash
make detect-all
```

Usar cuando se desea procesar ambos tipos de archivo sin cargar todavía a Hive.

---

## 7. Comandos de limpieza y refresco

### `make clean-yolo-state`

Limpia el estado anterior del flujo YOLO/Hive.

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

Usar cuando:

- Se reemplazaron imágenes.
- Se reemplazaron videos.
- Se desea regenerar el CSV desde cero.
- Se desea actualizar Hive con solo el dataset actual.

---

### `make refresh-images`

Flujo recomendado cuando solo se cambiaron imágenes.

```bash
make refresh-images
```

Ejecuta:

```text
check-paths
start-hadoop
start-hive
hive-init
clean-yolo-state
detect-images
load-hive
hive-final-textfile
validate-hive
count-hdfs
```

Usar cuando:

```text
Solo se agregaron, borraron o reemplazaron imágenes en data/raw/images/
```

---

### `make refresh-videos`

Flujo recomendado cuando solo se cambiaron videos.

```bash
make refresh-videos
```

Ejecuta:

```text
check-paths
start-hadoop
start-hive
hive-init
clean-yolo-state
detect-videos
load-hive
hive-final-textfile
validate-hive
count-hdfs
```

Usar cuando:

```text
Solo se agregaron, borraron o reemplazaron videos en data/raw/videos/
```

---

## 8. Comandos de carga y validación Hive

### `make load-hive`

Carga el CSV de detecciones a HDFS/Hive.

```bash
make load-hive
```

Este comando:

1. Lee `data/staging/yolo_detections.csv`.
2. Genera lotes en `data/processed/hive_batches/`.
3. Sube lotes a HDFS.
4. Carga datos en `yolo_objects_csv_stage`.

---

### `make validate-hive`

Consulta registros desde Hive.

```bash
make validate-hive
```

Ejecuta una consulta tipo:

```sql
SELECT source_id, class_name, confidence
FROM yolo_objects
LIMIT 20;
```

Usar para confirmar que Hive puede leer las detecciones.

---

### `make count-hdfs`

Cuenta registros directamente desde HDFS.

```bash
make count-hdfs
```

Equivalente:

```bash
hdfs dfs -cat /projects/yolo_objects/staging/* | wc -l
```

Se usa porque `COUNT(*)` en Hive puede depender de MapReduce/YARN.

---

### `make list-hdfs`

Lista archivos cargados en HDFS.

```bash
make list-hdfs
```

Valida:

```text
/projects/yolo_objects/staging
```

---

## 9. Comandos de Telegram

### `make telegram-test`

Envía un mensaje de prueba a Telegram.

```bash
make telegram-test
```

Antes se debe configurar:

```bash
cp .env.telegram.example .env.telegram
nano .env.telegram
```

Con:

```text
TELEGRAM_BOT_TOKEN=<TOKEN_TELEGRAM>
TELEGRAM_CHAT_ID=<CHAT_ID>
```

---

### `make detect-images-notify`

Ejecuta detección en imágenes y notifica inicio/fin/error por Telegram.

```bash
make detect-images-notify
```

---

### `make detect-videos-notify`

Ejecuta detección en videos y notifica inicio/fin/error por Telegram.

```bash
make detect-videos-notify
```

---

### `make load-hive-notify`

Carga datos a Hive y notifica inicio/fin/error por Telegram.

```bash
make load-hive-notify
```

---

## 10. Flujos completos

### `make run-review`

Ejecuta todo el flujo completo sin Telegram.

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
detect-images
detect-videos
load-hive
hive-final-textfile
validate-hive
count-hdfs
```

Usar para la revisión principal del profesor.

---

### `make run-review-notify`

Ejecuta todo el flujo completo con notificaciones Telegram.

```bash
make run-review-notify
```

Usar cuando se desea recibir alertas de avance, finalización o error.

---

## 11. Casos de uso recomendados

| Caso | Comando recomendado |
|---|---|
| Primera validación del entorno | `make test-python` |
| Verificar estructura | `make check-paths` |
| Levantar Hadoop | `make start-hadoop` |
| Levantar Hive | `make start-hive` |
| Crear tablas Hive | `make hive-init` |
| Solo cambié imágenes | `make refresh-images` |
| Solo cambié videos | `make refresh-videos` |
| Cambié imágenes y videos | `make run-review` |
| Quiero limpiar todo antes | `make clean-yolo-state` |
| Quiero validar Hive | `make validate-hive` |
| Quiero contar registros | `make count-hdfs` |
| Quiero usar Telegram | `make run-review-notify` |

---

## 12. Flujo recomendado para el profesor

### Sin Telegram

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab
source ~/cursobsgetl/ambientes/etl-ai-lab/bin/activate

make run-review
```

### Con Telegram

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab
source ~/cursobsgetl/ambientes/etl-ai-lab/bin/activate

cp .env.telegram.example .env.telegram
nano .env.telegram

make telegram-test
make run-review-notify
```

---

## 13. Notas importantes

- Si se reemplazan imágenes o videos, usar `make refresh-images`, `make refresh-videos` o `make run-review`.
- El CSV `data/staging/yolo_detections.csv` debe regenerarse en cada ejecución limpia.
- La tabla Hive `yolo_objects` debe reflejar los archivos actuales cargados en HDFS.
- Las imágenes/videos originales no se suben a GitHub; se entregan como comprimido aparte.
- El repositorio conserva la estructura mediante archivos `.gitkeep`.
