import os
import yaml
from datetime import datetime
from main.backend import crear_txt

def test_crear_txt():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.yaml"))
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    logs_dir = os.path.abspath(os.path.join(config["paths"]["logs_dir"], "crear_txt"))
    os.makedirs(logs_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_path = os.path.join(logs_dir, f"log_crear_txt_{timestamp}.txt")
    log_lines = []

    try:
        tiempo = [1.0, 2.0, 3.0]
        frecuencias = [10.0, 20.0, 30.0]
        derfrecuencias = [0.1, 0.2, 0.3]

        output_dir = os.path.abspath(config["paths"]["txt_outputs_dir"])
        os.makedirs(output_dir, exist_ok=True)

        nombre_base = os.path.join(output_dir, f"archivo_prueba_{timestamp}")
        archivo_generado = crear_txt(nombre_base, tiempo, frecuencias, derfrecuencias)

        assert os.path.exists(archivo_generado), "El archivo de texto no fue creado."

        with open(archivo_generado, "r") as f:
            lineas = f.readlines()
            assert lineas[0].strip().startswith("Tiempo"), "Encabezado incorrecto en el archivo."
            assert len(lineas) == 4, "El archivo no contiene las 3 líneas esperadas de datos."

        log_lines.append("El archivo fue creado correctamente y tiene el formato esperado.")
        log_lines.append("La función crear_txt pasó la prueba unitaria.")

    except AssertionError as e:
        log_lines.append(str(e))
        raise
    finally:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))

        if os.path.exists(archivo_generado):
            os.remove(archivo_generado)
