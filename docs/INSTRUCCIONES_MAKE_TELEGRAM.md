# Automatización con Makefile y Telegram — Proyecto YOLO + Hive

## 1. Archivos incluidos

Copiar estos archivos en la raíz del proyecto `etl-ai-lab`:

```text
Makefile
scripts/telegram_notify.py
scripts/run_with_telegram.sh
.env.telegram.example
```

## 2. Preparar Telegram

1. Crear un bot con BotFather.
2. Obtener el token del bot.
3. Obtener el `chat_id` del usuario o grupo.
4. Crear el archivo `.env.telegram`:

```bash
cp .env.telegram.example .env.telegram
nano .env.telegram
```

Contenido esperado:

```bash
TELEGRAM_BOT_TOKEN=TU_TOKEN_REAL
TELEGRAM_CHAT_ID=TU_CHAT_ID_REAL
```

No subir `.env.telegram` a repositorios.

## 3. Instalar dependencias

```bash
cd ~/cursobsgetl/codigo/etl-ai-lab
source ~/cursobsgetl/ambientes/etl-ai-lab/bin/activate
make install-deps
make install-telegram-deps
```

## 4. Probar Telegram

```bash
make telegram-test
```

## 5. Levantar servicios Big Data

```bash
make start-hadoop
make start-hive
make hive-init
```

## 6. Ejecutar detección

Imágenes:

```bash
make detect-images
```

Videos:

```bash
make detect-videos
```

Con notificaciones Telegram:

```bash
make detect-images-notify
make detect-videos-notify
```

## 7. Cargar a Hive

```bash
make load-hive
make hive-final-textfile
make validate-hive
make count-hdfs
```

## 8. Flujo completo para revisión del profesor

Sin Telegram:

```bash
make run-review
```

Con Telegram:

```bash
make run-review-notify
```

## 9. Observaciones

- `make start-hive` levanta solo HiveServer2 en `10000`; no levanta Metastore separado.
- La tabla final `yolo_objects` queda como tabla externa `TEXTFILE` apuntando a `/projects/yolo_objects/staging`.
- Para evitar problemas con `COUNT(*)` en MapReduce/YARN, se usa `make count-hdfs`.
- Las variables principales se pueden sobrescribir:

```bash
make detect-videos EVERY_N=10 CONF=0.45
make detect-camera CAMERA_IDX=1
```
