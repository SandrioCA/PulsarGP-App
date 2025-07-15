import os
import yaml
from datetime import datetime
from main.backend import load_toas, compute_residuals, frequency_residuals_func, crear_txt

def test_integration_generate_txt_from_residuals():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.yaml"))
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    files_dir = os.path.abspath(config["paths"]["files_dir"])
    logs_dir = os.path.abspath(os.path.join(config["paths"]["logs_dir"], "test_integration_generate_txt_from_residuals"))
    txt_dir = os.path.abspath(os.path.join(config["paths"]["txt_outputs_dir"], "test_integration_generate_txt_from_residuals"))

    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(txt_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(logs_dir, f"log_generate_txt_{timestamp}.txt")
    output_txt_path = os.path.join(txt_dir, f"residuos_freq_{timestamp}.txt")

    log_lines = []

    tim_path = os.path.join(files_dir, "psr04.tim")
    par_path = os.path.join(files_dir, "psr04.par")

    try:
        assert os.path.exists(tim_path), f"Archivo .tim no encontrado: {tim_path}"
        assert os.path.exists(par_path), f"Archivo .par no encontrado: {par_path}"
        log_lines.append("Archivos de entrada encontrados.")

        mjds, toas = load_toas(tim_path, return_also_mjds=True)
        residuals = compute_residuals(par_path, toas)

        phase_resids = residuals.phase_resids.value
        freq_resids = frequency_residuals_func(mjds.value, phase_resids)

        nombre_base = os.path.splitext(output_txt_path)[0]
        generado = crear_txt(nombre_base, mjds.value, phase_resids, freq_resids)

        assert os.path.exists(generado), "No se generó el archivo .txt."
        log_lines.append("Prueba de integración completa: Archivo .txt generado correctamente desde residuos.")

    except Exception as e:
        log_lines.append(f"Error durante la prueba de integración: {str(e)}")
        raise

    finally:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))
