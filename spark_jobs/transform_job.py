import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, sum as spark_sum, round as spark_round, count


def log_step(icon: str, message: str):
    """Imprime mensajes con formato uniforme para seguir la secuencia del ETL."""
    print(f"{icon} {message}")


def show_section(title: str):
    """Imprime un separador visual para cada sección."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main(input_path: str, output_path: str):
    spark = SparkSession.builder.appName("ETL Spark SQL").getOrCreate()

    try:
        show_section("🚀 INICIO DEL PROCESO ETL")
        log_step("📥", f"Leyendo archivo CSV desde: {input_path}")

        # Leer CSV
        df = (
            spark.read
            .option("header", True)
            .option("inferSchema", True)
            .csv(input_path)
        )

        log_step("✅", "Archivo cargado correctamente en DataFrame")

        # Validar columnas requeridas
        required_columns = {
            "SALES", "STATUS", "PRODUCTLINE", "ORDERNUMBER",
            "COUNTRY", "YEAR_ID", "DEALSIZE"
        }
        existing_columns = set(df.columns)
        missing_columns = required_columns - existing_columns

        if missing_columns:
            raise ValueError(
                f"❌ Faltan columnas requeridas en el archivo: {sorted(missing_columns)}"
            )

        # Mostrar esquema y muestra
        show_section("🧱 ESQUEMA DEL DATASET")
        df.printSchema()

        show_section("🔍 MUESTRA DE DATOS CRUDOS")
        df.show(5, truncate=False)

        total_records = df.count()
        log_step("📊", f"Total de registros leídos: {total_records}")

        # Limpiar: solo registros con SALES > 0 y STATUS = 'Shipped'
        show_section("🧹 LIMPIEZA DE DATOS")
        log_step("⚙️", "Aplicando filtro: SALES > 0 y STATUS = 'Shipped'")

        df_clean = df.filter(
            (col("SALES") > 0) & (col("STATUS") == "Shipped")
        )

        clean_records = df_clean.count()
        removed_records = total_records - clean_records

        log_step("✅", f"Registros después de limpieza: {clean_records}")
        log_step("🗑️", f"Registros descartados: {removed_records}")

        # Transformación 1: ventas totales por PRODUCTLINE
        show_section("📦 TRANSFORMACIÓN 1: VENTAS POR LÍNEA DE PRODUCTO")
        sales_by_product = (
            df_clean.groupBy("PRODUCTLINE")
            .agg(
                spark_round(spark_sum("SALES"), 2).alias("total_sales"),
                spark_round(avg("SALES"), 2).alias("avg_sales"),
                count("ORDERNUMBER").alias("total_orders")
            )
            .orderBy(col("total_sales").desc())
        )

        log_step("📈", "Resultado de ventas por línea de producto:")
        sales_by_product.show(truncate=False)

        # Transformación 2: ventas por COUNTRY y YEAR_ID
        show_section("🌍 TRANSFORMACIÓN 2: VENTAS POR PAÍS Y AÑO")
        sales_by_country_year = (
            df_clean.groupBy("COUNTRY", "YEAR_ID")
            .agg(
                spark_round(spark_sum("SALES"), 2).alias("total_sales"),
                count("ORDERNUMBER").alias("total_orders")
            )
            .orderBy("YEAR_ID", col("total_sales").desc())
        )

        log_step("📈", "Resultado de ventas por país y año:")
        sales_by_country_year.show(truncate=False)

        # Transformación 3: ventas por DEALSIZE
        show_section("💼 TRANSFORMACIÓN 3: VENTAS POR TAMAÑO DE NEGOCIO")
        sales_by_dealsize = (
            df_clean.groupBy("DEALSIZE")
            .agg(
                spark_round(spark_sum("SALES"), 2).alias("total_sales"),
                count("ORDERNUMBER").alias("total_orders"),
                spark_round(avg("SALES"), 2).alias("avg_sales")
            )
            .orderBy(col("total_sales").desc())
        )

        log_step("📈", "Resultado de ventas por tamaño de negocio:")
        sales_by_dealsize.show(truncate=False)

        # Escritura de resultados
        show_section("💾 GUARDADO DE RESULTADOS EN PARQUET")

        path_product = f"{output_path}/sales_by_product"
        path_country_year = f"{output_path}/sales_by_country_year"
        path_dealsize = f"{output_path}/sales_by_dealsize"

        log_step("📝", f"Guardando sales_by_product en: {path_product}")
        sales_by_product.coalesce(1).write.mode("overwrite").parquet(path_product)

        log_step("📝", f"Guardando sales_by_country_year en: {path_country_year}")
        sales_by_country_year.coalesce(1).write.mode("overwrite").parquet(path_country_year)

        log_step("📝", f"Guardando sales_by_dealsize en: {path_dealsize}")
        sales_by_dealsize.coalesce(1).write.mode("overwrite").parquet(path_dealsize)

        show_section("🎉 PROCESO ETL FINALIZADO CORRECTAMENTE")
        log_step("📂", f"Resultados guardados en: {output_path}")

    except Exception as e:
        show_section("❌ ERROR EN LA EJECUCIÓN")
        log_step("🚨", f"Se produjo un error: {str(e)}")
        raise

    finally:
        log_step("🛑", "Cerrando sesión de Spark")
        spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Proceso ETL en PySpark para análisis de ventas")
    parser.add_argument("--input", required=True, help="Ruta del archivo CSV de entrada")
    parser.add_argument("--output", required=True, help="Ruta de salida para archivos Parquet")
    args = parser.parse_args()

    main(args.input, args.output)