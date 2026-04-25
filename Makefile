# =============================================================================
# Makefile — Proyecto YOLO + HDFS + Hive + Telegram
# Autor: Smit Villafranca
# Uso general:
#   make help
#   make run-review
#   make run-review-notify
# =============================================================================

.DEFAULT_GOAL := help
SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

# -----------------------------------------------------------------------------
# Variables principales del proyecto
# -----------------------------------------------------------------------------
PROJECT_DIR ?= /home/smit_vr/cursobsgetl/codigo/etl-ai-lab
VENV_DIR    ?= /home/smit_vr/cursobsgetl/ambientes/etl-ai-lab
PYTHON      ?= $(VENV_DIR)/bin/python
PIP         ?= $(VENV_DIR)/bin/pip
USER_HIVE   ?= smit_vr

MODEL       ?= models/yolov8n.pt
CONF        ?= 0.35
EVERY_N     ?= 5
CAMERA_IDX  ?= 0

CSV_STAGE   ?= data/staging/yolo_detections.csv
BATCH_DIR   ?= data/processed/hive_batches
CHECKPOINT  ?= checkpoints/yolo_hive_checkpoint.json
HDFS_IN     ?= /projects/yolo_objects/incoming
HDFS_STAGE  ?= /projects/yolo_objects/staging
HIVE_DB     ?= yolo_project
HIVE_URL    ?= jdbc:hive2://localhost:10000/$(HIVE_DB)
DEFAULT_URL ?= jdbc:hive2://localhost:10000/default

NOTIFIER    ?= scripts/telegram_notify.py
WRAPPER     ?= scripts/run_with_telegram.sh

GREEN  := \033[0;32m
YELLOW := \033[1;33m
CYAN   := \033[0;36m
RED    := \033[0;31m
RESET  := \033[0m

.PHONY: help check-paths install install-deps install-telegram-deps test test-python \
        start-hadoop stop-hadoop status-hadoop \
        start-hive stop-hive status-hive test-hive hive-init hive-create hive-final-textfile hive-merge \
        detect-images detect-videos detect-camera detect-all classify-all \
        clean-yolo-state refresh-images refresh-videos \
        load-hive etl-hive validate-hive validate-hive-sample count-hdfs list-hdfs \
        telegram-test telegram-start telegram-ok telegram-error \
        detect-images-notify detect-videos-notify load-hive-notify \
        run-review run-review-notify airflow-start airflow-stop clean clean-runtime

help:
	@echo ""
	@printf "$(CYAN)╔════════════════════════════════════════════════════════════╗$(RESET)\n"
	@printf "$(CYAN)║ Proyecto YOLO + HDFS + Hive + Telegram — comandos Makefile ║$(RESET)\n"
	@printf "$(CYAN)╚════════════════════════════════════════════════════════════╝$(RESET)\n"
	@echo ""
	@printf "$(YELLOW)Instalación y validación:$(RESET)\n"
	@echo "  make install                 Alias de install-deps"
	@echo "  make install-deps            Instala dependencias Python del proyecto"
	@echo "  make install-telegram-deps   Instala requests para Telegram"
	@echo "  make test                    Alias de test-python"
	@echo "  make test-python             Valida imports: torch, ultralytics, cv2, pandas"
	@echo "  make check-paths             Valida rutas principales del proyecto"
	@echo ""
	@printf "$(YELLOW)Servicios Big Data:$(RESET)\n"
	@echo "  make start-hadoop            Levanta HDFS y YARN"
	@echo "  make status-hadoop           Muestra JPS, nodos YARN y raíz HDFS"
	@echo "  make stop-hadoop             Detiene HDFS y YARN"
	@echo "  make start-hive              Levanta HiveServer2 en puerto 10000"
	@echo "  make status-hive             Valida puertos 10000/10002 y conexión Beeline"
	@echo "  make stop-hive               Detiene HiveServer2/Metastore"
	@echo "  make test-hive               Alias de status-hive"
	@echo ""
	@printf "$(YELLOW)Hive / SQL:$(RESET)\n"
	@echo "  make hive-init               Crea base y tablas Hive"
	@echo "  make hive-create             Alias de hive-init"
	@echo "  make hive-final-textfile     Recrea yolo_objects como EXTERNAL TEXTFILE funcional"
	@echo "  make hive-merge              Alias de hive-final-textfile"
	@echo ""
	@printf "$(YELLOW)Detección YOLO:$(RESET)\n"
	@echo "  make detect-images           Ejecuta detección en imágenes"
	@echo "  make detect-videos           Ejecuta detección en videos"
	@echo "  make detect-camera           Ejecuta detección en cámara"
	@echo "  make detect-all              Ejecuta imágenes y videos"
	@echo "  make classify-all            Alias de detect-all"
	@echo ""
	@printf "$(YELLOW)Refresco de datos:$(RESET)\n"
	@echo "  make clean-yolo-state        Limpia CSV, checkpoint, lotes y HDFS staging"
	@echo "  make refresh-images          Limpia estado, procesa solo imágenes, carga a Hive y valida"
	@echo "  make refresh-videos          Limpia estado, procesa solo videos, carga a Hive y valida"
	@echo ""
	@printf "$(YELLOW)Carga y validación Hive:$(RESET)\n"
	@echo "  make load-hive               Carga CSV/lotes a HDFS y Hive staging"
	@echo "  make etl-hive                Alias de load-hive"
	@echo "  make validate-hive           Consulta yolo_objects LIMIT 20"
	@echo "  make validate-hive-sample    Consulta yolo_objects LIMIT 5 con todos los campos"
	@echo "  make count-hdfs              Cuenta registros desde HDFS sin COUNT(*)"
	@echo "  make list-hdfs               Lista archivos en HDFS staging"
	@echo ""
	@printf "$(YELLOW)Telegram:$(RESET)\n"
	@echo "  make telegram-test           Envía mensaje de prueba Telegram"
	@echo "  make telegram-start          Envía notificación de inicio"
	@echo "  make telegram-ok             Envía notificación de finalización correcta"
	@echo "  make telegram-error          Envía notificación de error"
	@echo "  make detect-images-notify    Detecta imágenes con notificación inicio/fin"
	@echo "  make detect-videos-notify    Detecta videos con notificación inicio/fin"
	@echo "  make load-hive-notify        Carga a Hive con notificación inicio/fin"
	@echo ""
	@printf "$(YELLOW)Flujos completos:$(RESET)\n"
	@echo "  make run-review              Levanta servicios, limpia estado, detecta, carga y valida"
	@echo "  make run-review-notify       Igual que run-review, con Telegram"
	@echo ""
	@printf "$(YELLOW)Airflow y limpieza:$(RESET)\n"
	@echo "  make airflow-start           Inicia webserver y scheduler de Airflow"
	@echo "  make airflow-stop            Detiene procesos de Airflow"
	@echo "  make clean                   Limpia __pycache__ y *.pyc"
	@echo "  make clean-runtime           Limpia salidas locales procesadas"
	@echo ""

check-paths:
	cd $(PROJECT_DIR)
	@echo "Proyecto: $$(pwd)"
	test -d src
	test -d sql
	test -d data/raw/images
	test -d data/raw/videos
	test -f $(MODEL)
	@printf "$(GREEN)Rutas principales OK.$(RESET)\n"

install-deps:
	cd $(PROJECT_DIR)
	$(PIP) install --upgrade pip wheel
	$(PIP) install "setuptools<82" --force-reinstall
	$(PIP) install -r requirements.txt
	$(PIP) install requests
	@printf "$(GREEN)Dependencias Python instaladas.$(RESET)\n"

install-telegram-deps:
	$(PIP) install requests
	@printf "$(GREEN)Dependencias Telegram instaladas.$(RESET)\n"

test-python:
	@cd $(PROJECT_DIR) && $(PYTHON) -c "import cv2, pandas, torch; from ultralytics import YOLO; print('python ok'); print('cv2:', cv2.__version__); print('torch:', torch.__version__); print('cuda:', torch.cuda.is_available()); print('ultralytics ok')"

start-hadoop:
	start-dfs.sh || true
	start-yarn.sh || true
	$(MAKE) status-hadoop

stop-hadoop:
	stop-yarn.sh || true
	stop-dfs.sh || true

status-hadoop:
	jps -l
	yarn node -list || true
	hdfs dfs -ls / || true

start-hive:
	@cd $(PROJECT_DIR) && mkdir -p logs
	@if ss -ltnp | grep -q ":10000"; then \
	  echo "HiveServer2 ya está activo en puerto 10000. No se reinicia."; \
	  $(MAKE) status-hive; \
	  exit 0; \
	fi
	@echo "Deteniendo HiveServer2/Metastore previos de forma segura..."
	@for pid in $$(jps -l | awk '/org.apache.hadoop.util.RunJar/ {print $$1}'); do \
	  cmd=$$(ps -p $$pid -o args=); \
	  echo "$$cmd" | grep -E "hiveserver2|HiveServer2|metastore|HiveMetaStore" >/dev/null 2>&1 && kill $$pid || true; \
	done
	@sleep 8
	@rm -f logs/hiveserver2.log
	@echo "Levantando HiveServer2 en puerto 10000..."
	@nohup hive --service hiveserver2 \
	  --hiveconf hive.server2.thrift.bind.host=0.0.0.0 \
	  --hiveconf hive.server2.thrift.port=10000 \
	  --hiveconf hive.server2.authentication=NONE \
	  --hiveconf hive.server2.enable.doAs=false \
	  > logs/hiveserver2.log 2>&1 &
	@echo "Esperando puerto 10000..."
	@for i in $$(seq 1 36); do \
	  if ss -ltnp | grep -q ":10000"; then \
	    echo "HiveServer2 activo en puerto 10000."; \
	    break; \
	  fi; \
	  echo "Esperando HiveServer2... intento $$i/36"; \
	  sleep 5; \
	done
	@ss -ltnp | grep -E "10000|10002" || \
	  (echo "HiveServer2 no levantó. Últimas líneas del log:" && tail -n 120 logs/hiveserver2.log && exit 1)
	@$(MAKE) status-hive

stop-hive:
	@echo "Deteniendo HiveServer2/Metastore de forma segura..."
	@for pid in $$(jps -l | awk '/org.apache.hadoop.util.RunJar/ {print $$1}'); do \
	  cmd=$$(ps -p $$pid -o args=); \
	  echo "$$cmd" | grep -E "hiveserver2|HiveServer2|metastore|HiveMetaStore" >/dev/null 2>&1 && kill $$pid || true; \
	done
	@sleep 5
	@ss -ltnp | grep -E "9083|10000|10002" || true

status-hive:
	@echo "Validando puertos HiveServer2..."
	@ss -ltnp | grep -E "10000|10002" || true
	@echo "Validando conexión Beeline..."
	@for i in $$(seq 1 24); do \
	  if beeline -u $(DEFAULT_URL) -n $(USER_HIVE) -e "SHOW DATABASES;" >/tmp/beeline_status_hive.log 2>&1; then \
	    cat /tmp/beeline_status_hive.log; \
	    echo "HiveServer2 responde correctamente."; \
	    exit 0; \
	  fi; \
	  echo "Esperando respuesta de HiveServer2... intento $$i/24"; \
	  sleep 5; \
	done; \
	cat /tmp/beeline_status_hive.log || true; \
	echo "HiveServer2 no respondió por Beeline."; \
	exit 1

test-hive: status-hive

hive-init:
	cd $(PROJECT_DIR)
	beeline -u $(DEFAULT_URL) -n $(USER_HIVE) -f sql/01_create_yolo_objects_tables.sql
	beeline -u $(HIVE_URL) -n $(USER_HIVE) -e "SHOW TABLES;"

hive-final-textfile:
	beeline -u $(HIVE_URL) -n $(USER_HIVE) -e "\
DROP TABLE IF EXISTS yolo_objects; \
CREATE EXTERNAL TABLE yolo_objects ( \
  detection_id STRING, source_type STRING, source_id STRING, frame_number INT, local_object_id INT, \
  class_id INT, class_name STRING, confidence DOUBLE, x_min INT, y_min INT, x_max INT, y_max INT, \
  width INT, height INT, area_pixels INT, frame_width INT, frame_height INT, bbox_area_ratio DOUBLE, \
  center_x DOUBLE, center_y DOUBLE, center_x_norm DOUBLE, center_y_norm DOUBLE, position_region STRING, \
  dominant_color_name STRING, dom_r INT, dom_g INT, dom_b INT, timestamp_sec DOUBLE, fps DOUBLE, \
  ingestion_date STRING, has_backpack BOOLEAN, has_cellphone BOOLEAN, nearby_objects_count INT, \
  batch_window_start INT, batch_window_end INT \
) ROW FORMAT DELIMITED FIELDS TERMINATED BY ',' STORED AS TEXTFILE LOCATION '$(HDFS_STAGE)';"
	@printf "$(GREEN)Tabla final yolo_objects apuntando a $(HDFS_STAGE).$(RESET)\n"

detect-images:
	cd $(PROJECT_DIR)
	$(PYTHON) src/sistema_clasificacion.py --mode images --model $(MODEL) --conf $(CONF)

detect-videos:
	cd $(PROJECT_DIR)
	$(PYTHON) src/sistema_clasificacion.py --mode videos --model $(MODEL) --conf $(CONF) --every-n-frames $(EVERY_N)

detect-camera:
	cd $(PROJECT_DIR)
	$(PYTHON) src/sistema_clasificacion.py --mode camera --model $(MODEL) --conf $(CONF) --every-n-frames $(EVERY_N) --camera-index $(CAMERA_IDX)

detect-all: detect-images detect-videos

clean-yolo-state:
	@echo "🧹 Limpiando estado YOLO/Hive para una ejecución fresca..."
	@cd $(PROJECT_DIR) && rm -f $(CSV_STAGE)
	@cd $(PROJECT_DIR) && rm -f $(CHECKPOINT)
	@cd $(PROJECT_DIR) && rm -rf $(BATCH_DIR)/*
	@cd $(PROJECT_DIR) && rm -rf data/processed/annotated/images/*
	@cd $(PROJECT_DIR) && rm -rf data/processed/annotated/videos/*
	@hdfs dfs -rm -r -f $(HDFS_STAGE) >/dev/null 2>&1 || true
	@hdfs dfs -mkdir -p $(HDFS_STAGE) >/dev/null 2>&1 || true
	@echo "✅ Estado limpiado: CSV, checkpoint, lotes locales y HDFS staging."

refresh-images: check-paths start-hadoop start-hive hive-init clean-yolo-state detect-images load-hive hive-final-textfile validate-hive count-hdfs
	@printf "\033[0;32m✅ Flujo de imágenes actualizado correctamente.\033[0m\n"

refresh-videos: check-paths start-hadoop start-hive hive-init clean-yolo-state detect-videos load-hive hive-final-textfile validate-hive count-hdfs
	@printf "\033[0;32m✅ Flujo de videos actualizado correctamente.\033[0m\n"

load-hive:
	cd $(PROJECT_DIR)
	$(PYTHON) src/sistema_batch_etl.py \
	  --input-csv $(CSV_STAGE) \
	  --output-dir $(BATCH_DIR) \
	  --checkpoint $(CHECKPOINT) \
	  --hdfs-dir $(HDFS_IN) \
	  --table yolo_objects_csv_stage \
	  --beeline-url $(HIVE_URL)

validate-hive:
	beeline -u $(HIVE_URL) -n $(USER_HIVE) -e "SELECT source_id, class_name, confidence FROM yolo_objects LIMIT 20;"

validate-hive-sample:
	beeline -u $(HIVE_URL) -n $(USER_HIVE) -e "SELECT * FROM yolo_objects LIMIT 5;"

count-hdfs:
	hdfs dfs -cat $(HDFS_STAGE)/* | wc -l

list-hdfs:
	hdfs dfs -ls $(HDFS_STAGE)

telegram-test:
	cd $(PROJECT_DIR)
	$(PYTHON) $(NOTIFIER) --message "✅ Prueba Telegram YOLO + Hive correcta"

telegram-start:
	cd $(PROJECT_DIR)
	$(PYTHON) $(NOTIFIER) --optional --message "🚀 Iniciando flujo YOLO + Hive"

telegram-ok:
	cd $(PROJECT_DIR)
	$(PYTHON) $(NOTIFIER) --optional --message "✅ Flujo YOLO + Hive finalizado correctamente"

telegram-error:
	cd $(PROJECT_DIR)
	$(PYTHON) $(NOTIFIER) --optional --message "❌ Error en flujo YOLO + Hive"

# Targets con notificación inicio/fin mediante wrapper.
detect-images-notify:
	cd $(PROJECT_DIR)
	bash $(WRAPPER) "Detección YOLO en imágenes" $(PYTHON) src/sistema_clasificacion.py --mode images --model $(MODEL) --conf $(CONF)
	LATEST=$$(find data/processed/annotated/images -type f \( -iname '*.jpg' -o -iname '*.png' -o -iname '*.jpeg' \) -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-); \
	if [ -n "$$LATEST" ]; then $(PYTHON) $(NOTIFIER) --optional --photo "$$LATEST" --caption "📸 Muestra de imagen anotada"; fi

detect-videos-notify:
	cd $(PROJECT_DIR)
	bash $(WRAPPER) "Detección YOLO en videos" $(PYTHON) src/sistema_clasificacion.py --mode videos --model $(MODEL) --conf $(CONF) --every-n-frames $(EVERY_N)
	LATEST=$$(find data/processed/annotated/videos -type f \( -iname '*.mp4' -o -iname '*.avi' -o -iname '*.mov' \) -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-); \
	if [ -n "$$LATEST" ]; then $(PYTHON) $(NOTIFIER) --optional --document "$$LATEST" --caption "🎞️ Video anotado generado"; fi

load-hive-notify:
	cd $(PROJECT_DIR)
	bash $(WRAPPER) "Carga CSV a HDFS/Hive" $(PYTHON) src/sistema_batch_etl.py --input-csv $(CSV_STAGE) --output-dir $(BATCH_DIR) --checkpoint $(CHECKPOINT) --hdfs-dir $(HDFS_IN) --table yolo_objects_csv_stage --beeline-url $(HIVE_URL)

run-review: check-paths start-hadoop start-hive hive-init clean-yolo-state detect-images detect-videos load-hive hive-final-textfile validate-hive count-hdfs
	@printf "\033[0;32m✅ Flujo completo ejecutado correctamente con datos actualizados.\033[0m\n"

run-review-notify:
	$(MAKE) telegram-start
	$(MAKE) run-review && $(MAKE) telegram-ok || { $(MAKE) telegram-error; exit 1; }

airflow-start:
	cd $(PROJECT_DIR)
	bash start_webserver.sh &
	bash start_scheduler.sh &
	@printf "$(GREEN)Airflow iniciado. URL: http://localhost:8080$(RESET)\n"

airflow-stop:
	pkill -9 -f "airflow scheduler" || true
	pkill -9 -f "airflow webserver" || true
	pkill -9 -f "airflow" || true

clean:
	cd $(PROJECT_DIR)
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@printf "$(GREEN)Limpieza Python completada.$(RESET)\n"

clean-runtime:
	cd $(PROJECT_DIR)
	rm -rf data/processed/annotated/* data/processed/hive_batches/*
	@printf "$(YELLOW)Se limpiaron salidas procesadas locales.$(RESET)\n"

# -----------------------------------------------------------------------------
# Aliases de compatibilidad documental
# -----------------------------------------------------------------------------
install: install-deps

test: test-python

hive-create: hive-init

classify-all: detect-all

etl-hive: load-hive

hive-merge: hive-final-textfile
