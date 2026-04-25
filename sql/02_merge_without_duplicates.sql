USE yolo_project;

INSERT OVERWRITE TABLE yolo_objects
SELECT
  detection_id, source_type, source_id, frame_number, local_object_id,
  class_id, class_name, confidence, x_min, y_min, x_max, y_max,
  width, height, area_pixels, frame_width, frame_height, bbox_area_ratio,
  center_x, center_y, center_x_norm, center_y_norm, position_region,
  dominant_color_name, dom_r, dom_g, dom_b, timestamp_sec, fps,
  ingestion_date, has_backpack, has_cellphone, nearby_objects_count,
  batch_window_start, batch_window_end
FROM (
  SELECT s.*,
         ROW_NUMBER() OVER (PARTITION BY detection_id ORDER BY ingestion_date DESC) AS rn
  FROM (
    SELECT * FROM yolo_objects
    UNION ALL
    SELECT * FROM yolo_objects_csv_stage
  ) s
) dedup
WHERE rn = 1;
