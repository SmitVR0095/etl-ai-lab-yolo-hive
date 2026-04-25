USE yolo_project;

-- 1. Conteo de objetos por clase
SELECT class_name, COUNT(*) AS total_objects
FROM yolo_objects
GROUP BY class_name
ORDER BY total_objects DESC;

-- 2. Número de personas por video
SELECT source_id, COUNT(*) AS total_persons
FROM yolo_objects
WHERE source_type = 'video' AND class_name = 'person'
GROUP BY source_id
ORDER BY total_persons DESC;

-- 3. Área promedio de bounding boxes por clase
SELECT class_name, ROUND(AVG(area_pixels), 2) AS avg_bbox_area
FROM yolo_objects
GROUP BY class_name
ORDER BY avg_bbox_area DESC;

-- 4. Distribución de colores dominantes por clase
SELECT class_name, dominant_color_name, COUNT(*) AS total
FROM yolo_objects
GROUP BY class_name, dominant_color_name
ORDER BY class_name, total DESC;

-- 5. Número de objetos por ventana de 10 segundos en cada video
SELECT source_id, batch_window_start, batch_window_end, COUNT(*) AS total_objects
FROM yolo_objects
WHERE source_type = 'video'
GROUP BY source_id, batch_window_start, batch_window_end
ORDER BY source_id, batch_window_start;
