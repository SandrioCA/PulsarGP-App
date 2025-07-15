import os
import yaml
from datetime import datetime
from main.backend import load_toas, compute_residuals

def test_integration_toas_to_residuals():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.yaml"))
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    files_dir = os.path.abspath(config["paths"]["files_dir"])
    logs_dir = os.path.abspath(os.path.join(config["paths"]["logs_dir"], "test_integration_toas_to_residuals"))
    os.makedirs(logs_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(logs_dir, f"log_toas_to_residuals_{timestamp}.txt")
    log_lines = []

    tim_path = os.path.join(files_dir, "psr04.tim")
    par_path = os.path.join(files_dir, "psr04.par")

    try:
        assert os.path.exists(tim_path), f"Archivo .tim no encontrado: {tim_path}"
        assert os.path.exists(par_path), f"Archivo .par no encontrado: {par_path}"
        log_lines.append("Archivos .tim y .par encontrados correctamente.")

        toas = load_toas(tim_path, return_also_mjds=False)
        residuals = compute_residuals(par_path, toas)

        assert hasattr(residuals, "time_resids"), "El objeto residuals no contiene 'time_resids'."
        assert residuals.time_resids is not None, "Los residuos de tiempo están vacíos o son None."
        assert residuals.time_resids.shape[0] > 0, "No se encontraron residuos de tiempo."

        log_lines.append(f"Se calcularon {residuals.time_resids.shape[0]} residuos exitosamente.")
        log_lines.append("Prueba de integración completa: Flujo TOAs → Residuals ejecutado con éxito.")

    except Exception as e:
        log_lines.append(f"Error durante la prueba de integración: {str(e)}")
        raise

    finally:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))
