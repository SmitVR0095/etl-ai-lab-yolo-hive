# Proyecto YOLOv8 + HDFS + Hive

Guia de instalacion, configuracion y ejecucion del proyecto de deteccion de objetos usando YOLOv8. El flujo final es:

```text
Imagen / Video / Camara -> YOLOv8 -> CSV -> HDFS -> Hive -> Consulta SQL con Beeline
```

## 1. Supuestos del proyecto

El proyecto puede revisarse de dos maneras:

1. **Ambiente ya preparado:** Python, Spark, Hadoop, Hive, Airflow y dependencias ya instaladas.
2. **Ambiente desde cero:** se deben instalar Ubuntu en WSL, Python 3.12, Java 17, Spark 3.5.2, Hadoop, Hive y Airflow.

> No guardar contrasenas reales dentro del repositorio. Usar variables de entorno o archivos `.env` locales.

## 2. Estructura esperada

```text
~/cursobsgetl/codigo/etl-ai-lab
|-- airflow/
|-- checkpoints/
|-- configs/
|-- data/
|   |-- raw/images/
|   |-- raw/videos/
|   |-- staging/yolo_detections.csv
|   `-- processed/
|-- logs/
|-- models/yolov8n.pt
|-- sql/
|   |-- 01_create_yolo_objects_tables.sql
|   |-- 02_merge_without_duplicates.sql
|   `-- 03_analytics_queries.sql
|-- src/
|   |-- sistema_clasificacion.py
|   |-- sistema_batch_etl.py
|   `-- yolo_features.py
|-- requirements.txt
`-- README.md
```

## 3. Activacion del entorno

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab
source ~/cursobsgetl/ambientes/etl-ai-lab/bin/activate

ls
ls src
ls sql
ls data/staging
ls models
```

## 4. Instalacion de dependencias Python

No usar `pip install --upgrade setuptools` sin restriccion, porque `torch` requiere `setuptools<82`.

```bash
python -m pip install --upgrade pip wheel
pip install "setuptools<82" --force-reinstall
pip install -r requirements.txt

python -c "import setuptools; print(setuptools.__version__)"
python -c "import torch; print(torch.__version__)"
```

## 5. Test de deteccion en imagenes

Colocar imagenes en:

```text
data/raw/images/
```

Ejecutar:

```bash
python src/sistema_clasificacion.py --mode images --model models/yolov8n.pt
```

Validar CSV:

```bash
ls -lh data/staging/
head -n 5 data/staging/yolo_detections.csv
```

## 6. Test de deteccion en videos

Colocar videos en:

```text
data/raw/videos/
```

Ejecutar:

```bash
python src/sistema_clasificacion.py --mode videos --model models/yolov8n.pt
```

Opcional para acelerar el procesamiento:

```bash
python src/sistema_clasificacion.py \
  --mode videos \
  --model models/yolov8n.pt \
  --conf 0.35 \
  --every-n-frames 5
```

## 7. Deteccion en tiempo real

Validar camara:

```bash
ls /dev/video*
```

Si aparece `/dev/video0`:

```bash
python src/sistema_clasificacion.py \
  --mode camera \
  --model models/yolov8n.pt \
  --camera-index 0 \
  --conf 0.35 \
  --every-n-frames 5
```

Para salir, presionar `q`.

## 8. Instalacion desde cero - WSL y Python

Desde PowerShell en Windows:

```powershell
wsl --list --online
wsl --install -d Ubuntu-24.04
```

En Ubuntu:

```bash
cd ~/
lsb_release -a
sudo apt-get update && sudo apt-get upgrade -y

mkdir -p /home/smit_vr/cursobsgetl/{codigo,ambientes}
cd /home/smit_vr/cursobsgetl/ambientes
sudo apt-get install python3.12-venv -y
python3 -m venv etl-ai-lab
source /home/smit_vr/cursobsgetl/ambientes/etl-ai-lab/bin/activate
```

## 9. Crear estructura base del proyecto

```bash
cd /home/smit_vr/cursobsgetl/codigo
mkdir -p etl-ai-lab/airflow/{dags,plugins,include,data,logs,tests}
mkdir -p etl-ai-lab/spark_jobs/utils
mkdir -p etl-ai-lab/configs etl-ai-lab/docker etl-ai-lab/scripts
mkdir -p etl-ai-lab/src etl-ai-lab/sql etl-ai-lab/models
mkdir -p etl-ai-lab/data/raw/images etl-ai-lab/data/raw/videos
mkdir -p etl-ai-lab/data/staging etl-ai-lab/data/processed
mkdir -p etl-ai-lab/checkpoints etl-ai-lab/logs
cd etl-ai-lab
find . -maxdepth 3 -type d | sort
```

## 10. Java 17 y Spark 3.5.2

```bash
sudo apt update
sudo apt install openjdk-17-jdk -y
java --version

cd /tmp
wget https://archive.apache.org/dist/spark/spark-3.5.2/spark-3.5.2-bin-hadoop3.tgz
tar -xvf spark-3.5.2-bin-hadoop3.tgz
sudo mv spark-3.5.2-bin-hadoop3 /opt/spark
rm spark-3.5.2-bin-hadoop3.tgz
```

Agregar en `~/.bashrc`:

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export SPARK_HOME=/opt/spark
export PATH=$PATH:$JAVA_HOME/bin:$SPARK_HOME/bin:$SPARK_HOME/sbin
```

Aplicar y validar:

```bash
source ~/.bashrc
spark-submit --version
```

## 11. Hadoop/HDFS/YARN

El proyecto requiere comandos `hdfs`, `start-dfs.sh` y `start-yarn.sh` disponibles en PATH.

Validar:

```bash
which hdfs
which start-dfs.sh
which start-yarn.sh
hadoop version
```

Variables sugeridas si Hadoop esta instalado en `~/bigdata/hadoop`:

```bash
export HADOOP_HOME=/home/smit_vr/bigdata/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
```

Levantar servicios:

```bash
start-dfs.sh
start-yarn.sh
jps -l
hdfs dfs -ls /
```

## 12. Configuracion final de Hive

En este proyecto se usa **HiveServer2 con Derby embebido**. No levantar `hive --service metastore`, porque puede bloquear `metastore_db`.

Editar:

```bash
cp ~/bigdata/hive/conf/hive-site.xml ~/bigdata/hive/conf/hive-site.xml.bak
nano ~/bigdata/hive/conf/hive-site.xml
```

Dentro de `<configuration>` debe existir esta configuracion:

```xml
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
```

No debe estar activo este bloque cuando se usa Derby embebido:

```xml
<property>
  <name>hive.metastore.uris</name>
  <value>thrift://localhost:9083</value>
</property>
```

## 13. Levantar HiveServer2

```bash
pkill -f "metastore" || true
pkill -f "HiveMetaStore" || true
pkill -f "hiveserver2" || true
pkill -f "HiveServer2" || true
sleep 8

cd ~/cursobsgetl/codigo/etl-ai-lab
mkdir -p logs
rm -f logs/hiveserver2.log

nohup hive --service hiveserver2 \
  --hiveconf hive.server2.thrift.bind.host=0.0.0.0 \
  --hiveconf hive.server2.thrift.port=10000 \
  --hiveconf hive.server2.authentication=NONE \
  --hiveconf hive.server2.enable.doAs=false \
  > logs/hiveserver2.log 2>&1 &

sleep 60
ss -ltnp | grep -E "10000|10002"
```

Probar conexion:

```bash
beeline -u jdbc:hive2://localhost:10000/default \
  -n smit_vr \
  -e "SHOW DATABASES;"
```

## 14. Crear tablas Hive

```bash
beeline -u jdbc:hive2://localhost:10000/default \
  -n smit_vr \
  -f sql/01_create_yolo_objects_tables.sql

beeline -u jdbc:hive2://localhost:10000/yolo_project \
  -n smit_vr \
  -e "SHOW TABLES;"
```

Debe mostrar:

```text
yolo_objects
yolo_objects_csv_stage
```

## 15. Cargar CSV a HDFS/Hive

```bash
python src/sistema_batch_etl.py \
  --input-csv data/staging/yolo_detections.csv \
  --output-dir data/processed/hive_batches \
  --checkpoint checkpoints/yolo_hive_checkpoint.json \
  --hdfs-dir /projects/yolo_objects/incoming \
  --table yolo_objects_csv_stage \
  --beeline-url jdbc:hive2://localhost:10000/yolo_project
```

## 16. Tabla final funcional

Si `COUNT(*)` o `GROUP BY` fallan por MapReduce/YARN, dejar `yolo_objects` como tabla externa TEXTFILE apuntando a los datos ya cargados:

```bash
beeline -u jdbc:hive2://localhost:10000/yolo_project \
  -n smit_vr \
  -e "
DROP TABLE IF EXISTS yolo_objects;
CREATE EXTERNAL TABLE yolo_objects (
  detection_id STRING,
  source_type STRING,
  source_id STRING,
  frame_number INT,
  local_object_id INT,
  class_id INT,
  class_name STRING,
  confidence DOUBLE,
  x_min INT,
  y_min INT,
  x_max INT,
  y_max INT,
  width INT,
  height INT,
  area_pixels INT,
  frame_width INT,
  frame_height INT,
  bbox_area_ratio DOUBLE,
  center_x DOUBLE,
  center_y DOUBLE,
  center_x_norm DOUBLE,
  center_y_norm DOUBLE,
  position_region STRING,
  dominant_color_name STRING,
  dom_r INT,
  dom_g INT,
  dom_b INT,
  timestamp_sec DOUBLE,
  fps DOUBLE,
  ingestion_date STRING,
  has_backpack BOOLEAN,
  has_cellphone BOOLEAN,
  nearby_objects_count INT,
  batch_window_start INT,
  batch_window_end INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/projects/yolo_objects/staging';
"
```

## 17. Validaciones finales

```bash
beeline -u jdbc:hive2://localhost:10000/yolo_project \
  -n smit_vr \
  -e "SELECT * FROM yolo_objects LIMIT 5;"

beeline -u jdbc:hive2://localhost:10000/yolo_project \
  -n smit_vr \
  -e "SELECT source_id, class_name, confidence FROM yolo_objects LIMIT 20;"
```

Contar registros sin `COUNT(*)`:

```bash
hdfs dfs -cat /projects/yolo_objects/staging/* | wc -l
hdfs dfs -ls /projects/yolo_objects/staging
```

## 18. Airflow opcional

```bash
source /home/smit_vr/cursobsgetl/ambientes/etl-ai-lab/bin/activate
export AIRFLOW_HOME=/home/smit_vr/cursobsgetl/codigo/etl-ai-lab/airflow

airflow db migrate

airflow users create \
  --username admin \
  --firstname Smit \
  --lastname Villafranca \
  --role Admin \
  --email admin@example.com \
  --password '<PASSWORD_LOCAL>'

# Terminal 1
bash /home/smit_vr/cursobsgetl/codigo/etl-ai-lab/start_webserver.sh

# Terminal 2
bash /home/smit_vr/cursobsgetl/codigo/etl-ai-lab/start_scheduler.sh
```

Ingresar a:

```text
http://localhost:8080
```

## 19. Troubleshooting

| Problema | Solucion |
|---|---|
| `torch requires setuptools<82` | `pip install "setuptools<82" --force-reinstall` |
| Beeline no conecta | Validar `ss -ltnp | grep 10000` y revisar `logs/hiveserver2.log` |
| Derby bloqueado | No levantar `hive --service metastore`; usar solo HiveServer2 |
| `COUNT(*)` falla | Validar con `LIMIT` y contar con `hdfs dfs -cat ... | wc -l` |
| Camara no aparece en WSL | Usar modo videos o configurar acceso USB/camara en WSL |
| No encuentra imagen/video | Validar `data/raw/images` y `data/raw/videos` |

## 20. Comandos minimos para revision del profesor

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab
source ~/cursobsgetl/ambientes/etl-ai-lab/bin/activate

start-dfs.sh
start-yarn.sh

nohup hive --service hiveserver2 \
  --hiveconf hive.server2.thrift.bind.host=0.0.0.0 \
  --hiveconf hive.server2.thrift.port=10000 \
  --hiveconf hive.server2.authentication=NONE \
  --hiveconf hive.server2.enable.doAs=false \
  > logs/hiveserver2.log 2>&1 &

sleep 60

beeline -u jdbc:hive2://localhost:10000/default -n smit_vr -e "SHOW DATABASES;"

python src/sistema_clasificacion.py --mode images --model models/yolov8n.pt
python src/sistema_clasificacion.py --mode videos --model models/yolov8n.pt

python src/sistema_batch_etl.py \
  --input-csv data/staging/yolo_detections.csv \
  --output-dir data/processed/hive_batches \
  --checkpoint checkpoints/yolo_hive_checkpoint.json \
  --hdfs-dir /projects/yolo_objects/incoming \
  --table yolo_objects_csv_stage \
  --beeline-url jdbc:hive2://localhost:10000/yolo_project

beeline -u jdbc:hive2://localhost:10000/yolo_project \
  -n smit_vr \
  -e "SELECT source_id, class_name, confidence FROM yolo_objects LIMIT 20;"
```

## 21. Resultado esperado

```text
source_id              class_name    confidence
Amiga_Giane_001.jpg    person        0.916737
Amiga_Giane_002.jpg    person        0.883236
Equipo_Darwin.jpg      person        0.859373
```

Con esto queda validado:

```text
YOLOv8 -> CSV -> HDFS -> Hive -> Consulta SQL
```
