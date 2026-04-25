# Guía paso a paso: Proyecto YOLO + HDFS + Hive + Makefile + Telegram

## 1. Objetivo del documento

Esta guía explica cómo preparar y ejecutar el proyecto desde el momento en que se descomprime el archivo `.zip` hasta dejar funcional el flujo completo usando `Makefile`.

El flujo automatizado del proyecto es:

```text
Imágenes / Videos / Cámara
        ↓
YOLOv8 detecta objetos
        ↓
Se genera CSV local
        ↓
Se suben lotes a HDFS
        ↓
Hive expone la tabla yolo_objects
        ↓
Beeline permite validar resultados con SQL
        ↓
Telegram puede notificar inicio, fin y errores
```

---

## 2. Supuestos del ambiente

El proyecto puede ejecutarse en dos escenarios:

### Escenario A: ambiente ya preparado

Se asume que ya están instalados y configurados:

- Ubuntu 24.04 en WSL.
- Python 3.12.
- Entorno virtual `etl-ai-lab`.
- Java 17.
- Apache Spark 3.5.2.
- Apache Hadoop.
- Apache Hive 4.1.0.
- Apache Airflow.
- Modelo YOLO `yolov8n.pt`.

### Escenario B: ambiente no preparado

Si el ambiente no está preparado, primero deben ejecutarse las guías de instalación base:

1. Instalación de Ubuntu 24.04 en WSL.
2. Creación del entorno virtual Python.
3. Instalación de Java 17.
4. Instalación de Spark.
5. Instalación/configuración de Hadoop e Hive.
6. Instalación/configuración de Airflow.

La ruta esperada del proyecto es:

```bash
/home/smit_vr/cursobsgetl/codigo/etl-ai-lab
```

El entorno virtual esperado es:

```bash
/home/smit_vr/cursobsgetl/ambientes/etl-ai-lab
```

---

## 3. Descomprimir el proyecto base

Ubicarse en la carpeta del proyecto:

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab
```

Si se tiene el archivo comprimido del proyecto:

```bash
ls -lh etl_ai_lab_yolo_hive_project.zip
```

Descomprimir:

```bash
unzip -o etl_ai_lab_yolo_hive_project.zip -d .
```

Validar que se hayan creado carpetas como:

```bash
ls
ls src
ls sql
ls models
ls data
```

Resultado esperado:

```text
src/
sql/
data/
models/
tests/
checkpoints/
```

---

## 4. Crear carpetas faltantes

Ejecutar desde la raíz del proyecto:

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab

mkdir -p airflow/{dags,plugins,include,data,logs,tests,runtime}
mkdir -p airflow/data/out_parquet/{sales_by_country_year,sales_by_dealsize,sales_by_product}
mkdir -p configs docker scripts spark_jobs/utils
mkdir -p src sql tests
mkdir -p data/raw/images data/raw/videos data/staging
mkdir -p data/processed/hive_batches data/processed/annotated/images data/processed/annotated/videos
mkdir -p checkpoints models logs docs detections/images
```

Validar estructura:

```bash
tree -L 3
```

Si `tree` no existe:

```bash
sudo apt update
sudo apt install tree -y
```

---

## 5. Activar entorno virtual

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab
source ~/cursobsgetl/ambientes/etl-ai-lab/bin/activate
```

Validar:

```bash
which python
python --version
```

---

## 6. Instalar dependencias Python del proyecto

Actualizar herramientas base respetando compatibilidad con Torch:

```bash
pip install --upgrade pip wheel
pip install "setuptools<82"
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Validar librerías principales:

```bash
python -c "import cv2, pandas, torch; from ultralytics import YOLO; print('python ok'); print('cv2:', cv2.__version__); print('torch:', torch.__version__); print('cuda:', torch.cuda.is_available()); print('ultralytics ok')"
```

Nota: `cuda: False` no impide ejecutar el proyecto. Significa que YOLO usará CPU.

---

## 7. Configurar hive-site.xml

El archivo se encuentra en:

```bash
~/bigdata/hive/conf/hive-site.xml
```

Hacer backup:

```bash
cp ~/bigdata/hive/conf/hive-site.xml ~/bigdata/hive/conf/hive-site.xml.bak
```

Editar:

```bash
nano ~/bigdata/hive/conf/hive-site.xml
```

Configuración recomendada para este proyecto local:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>

  <property>
    <name>hive.metastore.warehouse.dir</name>
    <value>/user/hive/warehouse</value>
  </property>

  <property>
    <name>hive.server2.thrift.port</name>
    <value>10000</value>
  </property>

  <property>
    <name>hive.server2.thrift.bind.host</name>
    <value>0.0.0.0</value>
  </property>

  <property>
    <name>hive.server2.authentication</name>
    <value>NONE</value>
  </property>

  <property>
    <name>hive.server2.enable.doAs</name>
    <value>false</value>
  </property>

  <property>
    <name>hive.server2.support.dynamic.service.discovery</name>
    <value>false</value>
  </property>

  <property>
    <name>hive.server2.active.passive.ha.enable</name>
    <value>false</value>
  </property>

  <property>
    <name>javax.jdo.option.ConnectionURL</name>
    <value>jdbc:derby:;databaseName=/home/smit_vr/bigdata/hive/metastore_db;create=true</value>
  </property>

  <property>
    <name>javax.jdo.option.ConnectionDriverName</name>
    <value>org.apache.derby.jdbc.EmbeddedDriver</value>
  </property>

  <property>
    <name>javax.jdo.option.ConnectionUserName</name>
    <value>APP</value>
  </property>

  <property>
    <name>javax.jdo.option.ConnectionPassword</name>
    <value>mine</value>
  </property>

  <property>
    <name>hive.metastore.event.db.notification.api.auth</name>
    <value>false</value>
  </property>

  <property>
    <name>hive.notification.event.poll.interval</name>
    <value>0s</value>
  </property>

</configuration>
```

Importante: en este modo local no se debe levantar un Metastore separado en `9083`. El flujo funcional usa HiveServer2 con Derby embebido.

No debe quedar activo este bloque:

```xml
<property>
  <name>hive.metastore.uris</name>
  <value>thrift://localhost:9083</value>
</property>
```

---

## 8. Instalar paquete Makefile + Telegram

Si se tiene el archivo:

```bash
yolo_hive_make_telegram_pack.zip
```

Descomprimir directamente en la raíz del proyecto:

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab
unzip -o yolo_hive_make_telegram_pack.zip
```

Esto debe crear o actualizar:

```text
Makefile
scripts/telegram_notify.py
scripts/run_with_telegram.sh
docs/INSTRUCCIONES_MAKE_TELEGRAM.md
.env.telegram.example
```

Asignar permisos:

```bash
chmod +x scripts/telegram_notify.py
chmod +x scripts/run_with_telegram.sh
```

Eliminar metadata de Windows si aparece:

```bash
rm -f "yolo_hive_make_telegram_pack.zip:Zone.Identifier"
```

---

## 9. Correcciones necesarias del Makefile

Durante las pruebas se detectaron dos ajustes importantes:

### 9.1. Corregir target test-python

El target `test-python` debe usar una línea simple de Python para evitar errores de tabulación en Makefile.

Debe quedar conceptualmente así:

```makefile
test-python:
	@cd $(PROJECT_DIR) && $(PYTHON) -c "import cv2, pandas, torch; from ultralytics import YOLO; print('python ok'); print('cv2:', cv2.__version__); print('torch:', torch.__version__); print('cuda:', torch.cuda.is_available()); print('ultralytics ok')"
```

### 9.2. Corregir start-hive para no matar el proceso Makefile

No usar `pkill -f "hiveserver2"` de forma directa dentro del Makefile, porque puede terminar matando el propio proceso de `make`.

La lógica recomendada es:

1. Si el puerto `10000` ya está activo, no reiniciar Hive.
2. Si no está activo, buscar procesos Java `RunJar` asociados a HiveServer2/Metastore.
3. Levantar HiveServer2.
4. Esperar hasta que el puerto `10000` responda.
5. Validar con Beeline.

---

## 10. Validar comandos disponibles del Makefile

```bash
make help
```

Comandos principales esperados:

```text
make install-deps
make install-telegram-deps
make test-python
make check-paths
make start-hadoop
make status-hadoop
make stop-hadoop
make start-hive
make status-hive
make stop-hive
make hive-init
make hive-final-textfile
make detect-images
make detect-videos
make detect-camera
make detect-all
make load-hive
make validate-hive
make count-hdfs
make list-hdfs
make telegram-test
make detect-images-notify
make detect-videos-notify
make load-hive-notify
make run-review
make run-review-notify
```

---

## 11. Validaciones iniciales con Makefile

Validar rutas:

```bash
make check-paths
```

Validar dependencias Python:

```bash
make test-python
```

Resultado esperado:

```text
python ok
cv2: 4.13.0
torch: 2.11.0+cu130
cuda: False
ultralytics ok
```

---

## 12. Levantar Hadoop y YARN

```bash
make start-hadoop
```

Validar:

```bash
make status-hadoop
```

Deben aparecer procesos:

```text
NameNode
DataNode
SecondaryNameNode
ResourceManager
NodeManager
```

---

## 13. Levantar HiveServer2

```bash
make start-hive
```

Validar:

```bash
make status-hive
```

Resultado esperado:

```text
LISTEN *:10000
LISTEN *:10002
Connected to: Apache Hive
```

Ejemplo de base de datos esperada:

```text
default
demo
yolo_project
```

---

## 14. Inicializar tablas Hive

```bash
make hive-init
```

Esto crea:

```text
yolo_project.yolo_objects_csv_stage
yolo_project.yolo_objects
```

Después se recomienda recrear la tabla final como `TEXTFILE` apuntando a la ruta staging de HDFS:

```bash
make hive-final-textfile
```

Esto evita depender de agregaciones MapReduce o conversiones Parquet durante la revisión.

---

## 15. Ejecutar testeo con imágenes

Colocar imágenes en:

```text
data/raw/images/
```

Ejecutar con Makefile:

```bash
make detect-images
```

Equivalente manual:

```bash
python src/sistema_clasificacion.py --mode images --model models/yolov8n.pt
```

El resultado se genera en:

```text
data/staging/yolo_detections.csv
```

Validar:

```bash
head -n 5 data/staging/yolo_detections.csv
```

---

## 16. Ejecutar testeo con videos

Colocar videos en:

```text
data/raw/videos/
```

Ejecutar con Makefile:

```bash
make detect-videos
```

Equivalente manual:

```bash
python src/sistema_clasificacion.py --mode videos --model models/yolov8n.pt
```

Si se desea procesar menos frames:

```bash
python src/sistema_clasificacion.py --mode videos --model models/yolov8n.pt --every-n-frames 5
```

---

## 17. Cargar detecciones a HDFS y Hive

```bash
make load-hive
```

Este comando realiza:

1. Lee `data/staging/yolo_detections.csv`.
2. Genera lotes en `data/processed/hive_batches/`.
3. Sube archivos a HDFS.
4. Carga datos a `yolo_objects_csv_stage`.
5. Actualiza `checkpoints/yolo_hive_checkpoint.json`.

---

## 18. Validar resultados en Hive

```bash
make validate-hive
```

Consulta esperada:

```sql
SELECT source_id, class_name, confidence
FROM yolo_objects
LIMIT 20;
```

Salida esperada:

```text
Amiga_Giane_001.jpg | person | 0.916737
Amiga_Giane_001.jpg | person | 0.902459
Equipo_Darwin.jpg   | person | 0.859373
```

---

## 19. Contar registros sin COUNT(*)

Debido a que `COUNT(*)` puede lanzar trabajos MapReduce y fallar según la configuración local, se recomienda contar desde HDFS:

```bash
make count-hdfs
```

Equivalente manual:

```bash
hdfs dfs -cat /projects/yolo_objects/staging/* | wc -l
```

Listar archivos:

```bash
make list-hdfs
```

---

## 20. Ejecutar flujo completo sin Telegram

Para que el profesor revise todo el flujo sin notificaciones:

```bash
make run-review
```

Este comando debe ejecutar:

```text
check-paths
start-hadoop
start-hive
hive-init
detect-images
detect-videos
load-hive
hive-final-textfile
validate-hive
count-hdfs
```

Resultado esperado:

- Hadoop activo.
- HiveServer2 activo en `10000`.
- Detección YOLO ejecutada en imágenes y videos.
- CSV generado.
- Datos cargados a HDFS.
- Tabla `yolo_objects` consultable desde Hive.

---

## 21. Configurar Telegram

Crear archivo local:

```bash
cp .env.telegram.example .env.telegram
nano .env.telegram
```

Completar con valores reales:

```bash
TELEGRAM_BOT_TOKEN=TU_TOKEN_REAL
TELEGRAM_CHAT_ID=TU_CHAT_ID_REAL
```

No subir `.env.telegram` a repositorios.

Probar Telegram:

```bash
make telegram-test
```

---

## 22. Ejecutar flujo completo con Telegram

```bash
make run-review-notify
```

Este flujo debe enviar notificaciones de inicio, fin o error durante la ejecución.

También se pueden ejecutar pasos individuales con notificación:

```bash
make detect-images-notify
make detect-videos-notify
make load-hive-notify
```

---

## 23. Ejecución por partes si se desea depurar

```bash
make check-paths
make status-hadoop
make status-hive
make hive-init
make hive-final-textfile
make detect-images
make detect-videos
make load-hive
make validate-hive
make count-hdfs
```

---

## 24. Errores comunes y solución

### 24.1. `Makefile: missing separator`

Causa: comandos del Makefile sin tabulación real.

Solución: revisar que las líneas de comandos dentro de cada target empiecen con TAB.

### 24.2. HiveServer2 no responde

Validar:

```bash
ss -ltnp | grep -E "10000|10002"
tail -n 120 logs/hiveserver2.log
```

Reiniciar:

```bash
make stop-hive
make start-hive
```

### 24.3. `COUNT(*)` falla

Usar:

```bash
make count-hdfs
```

### 24.4. `torch requires setuptools<82`

Ejecutar:

```bash
pip install "setuptools<82" --force-reinstall
```

### 24.5. No se detectan videos

Validar:

```bash
ls -lh data/raw/videos/
```

Ejecutar manual:

```bash
python src/sistema_clasificacion.py --mode videos --model models/yolov8n.pt
```

### 24.6. No se detectan imágenes

Validar:

```bash
ls -lh data/raw/images/
```

Ejecutar manual:

```bash
python src/sistema_clasificacion.py --mode images --model models/yolov8n.pt
```

---

## 25. Evidencia esperada para revisión

El profesor debe poder observar:

1. `make help` mostrando comandos disponibles.
2. `make test-python` validando YOLO/Torch/OpenCV.
3. `make status-hive` conectando a Hive.
4. `make detect-images` generando detecciones.
5. `make detect-videos` generando detecciones.
6. `make load-hive` cargando CSV a HDFS/Hive.
7. `make validate-hive` mostrando resultados SQL.
8. `make count-hdfs` mostrando cantidad de registros almacenados.

---

## 26. Comandos mínimos para revisión rápida

Sin Telegram:

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab
source ~/cursobsgetl/ambientes/etl-ai-lab/bin/activate
make run-review
```

Con Telegram:

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab
source ~/cursobsgetl/ambientes/etl-ai-lab/bin/activate
cp .env.telegram.example .env.telegram
nano .env.telegram
make telegram-test
make run-review-notify
```

---

## 27. Resultado final del proyecto

El resultado final es un pipeline funcional:

```text
YOLOv8 + Python
   ↓
CSV de detecciones
   ↓
HDFS
   ↓
Hive External Table
   ↓
Consultas SQL con Beeline
   ↓
Automatización con Makefile
   ↓
Notificaciones opcionales con Telegram
```
