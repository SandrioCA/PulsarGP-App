import os
import yaml
import numpy as np
from datetime import datetime
from main.backend import frequency_residuals_func

def test_frequency_residuals_func():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config.yaml"))
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    logs_dir = os.path.abspath(os.path.join(config["paths"]["logs_dir"], "frequency_residuals_func"))
    os.makedirs(logs_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(logs_dir, f"log_frequency_residuals_{timestamp}.txt")
    log_lines = []

    try:
        toas = np.array([1, 2, 3, 4, 5])
        phase_resids = np.array([0.1, 0.15, 0.2, 0.18, 0.16])

        freq_resids = frequency_residuals_func(toas, phase_resids)

        assert isinstance(freq_resids, np.ndarray), "La salida no es un arreglo de numpy."
        assert freq_resids.shape == toas.shape, "La forma del arreglo no coincide con la de los TOAs."
        assert not np.isnan(freq_resids).any(), "Hay valores NaN en los resultados."

        log_lines.append("frequency_residuals_func ejecutada correctamente.")
        log_lines.append(f"Resultados: {freq_resids.tolist()}")
        log_lines.append("La función frequency_residuals_func pasó la prueba unitaria.")

    except AssertionError as e:
        log_lines.append(f"Error en la prueba: {str(e)}")
        raise

    finally:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))
