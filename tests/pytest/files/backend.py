import pint.toa as toa_module
import pint.models
import pint.residuals as res
import numpy as np
import GPy
import astropy.units as u
from astropy.time import Time
import matplotlib.pyplot as plt

from scipy.interpolate import make_interp_spline #la gran G

# ------ Referente a PINT ----------

def load_toas(timFile, show_summary=False, return_also_mjds=True):
    """
    Carga los Tiempos de Arribo (TOAs) desde un archivo .tim.

    Parámetros:
    ----------
    timFile : str
        Ruta al archivo .tim que contiene los datos de TOAs del púlsar.
    show_summary : bool, opcional
        Si es True, imprime un resumen de los TOAs cargados.
    return_in_mjds : bool, opcional
        Si es True, retorna también los valores de tiempo en unidades MJD.

    Retorna:
    -------
        Si return_also_mjds es True, retorna ---> mjds, toas
        donde mjds es un arreglo de tiempos en MJD y toas es el objeto TOAs completo.

        Si return_also_mjds es False, retorna solo el objeto TOAs.
    """

    toas_object = toa_module.get_TOAs(timFile, planets=True)

    if show_summary:
        toas_object.print_summary()
        
    if return_also_mjds:

        toa_array = toas_object.get_mjds()

        return toa_array, toas_object
    
    return toas_object

def compute_residuals(parFile, toas_object):
    """
    Calcula los residuos temporales entre los TOAs observados y el modelo de tiempo del púlsar.

    Parámetros:
    ----------
    parFile : str
        Ruta al archivo .par que define el modelo de temporización del púlsar.
    toas : pint.toa.TOAs
        Objeto TOAs obtenido, por ejemplo, mediante la función `load_toas(..., return_in_mjds=False)`.

    Retorna:
    -------
    pint.residuals.Residuals
        Objeto que contiene los residuos de temporización (observado - modelo) en unidades de tiempo.
    """

    model = pint.models.get_model(parFile)
    phase_residuals_object = res.Residuals(toas_object, model)

    return phase_residuals_object, model

# ------- referente a GPy -----------

def entrenamiento_gp_model(toas_array, frecuency_residuals):
    """
    Función para entrenar el modelo del la Regresión Gaussiana

    Parámetros:
    -----------
    toas : list or array
        tiempo de llegada de las frecuencias
    residuos : list or array
        lista con los residuos de frecuencias

    Retorna:
    -----------
    modelo : GPy.models.GPRegression
        modelo optimizado de la regresión gaussiana
    """

    #Convertir entradas a vectores
    toas = np.array(toas_array)
    residuos = np.array(frecuency_residuals)
    
    #Reajuste a columnas
    toas_ver = toas.reshape(-1, 1)
    res_ver = residuos.reshape(-1, 1)

    #Se define el kernel RBF
    kernel = GPy.kern.RBF(input_dim=1, variance=1., lengthscale=np.ptp(toas)/10)


    #Entrenamiento del modelo
    modelo = GPy.models.GPRegression(toas_ver, res_ver, kernel)
    modelo.optimize()

    return modelo

def obtener_frecuencia_total_y_errores(toas_array, modelo_gp, f_base):
    """
    Calcula la frecuencia total del púlsar como la suma del modelo base con los residuos predichos por GP.

    Parámetros:
    - toas_array : array
        Tiempos de llegada (TOAs), normalizados (X)
    - modelo_gp : GPy.models.GPRegression
        Modelo GP entrenado sobre residuos de frecuencia (en Hz)
    - f_base : float
        Frecuencia base del pulsar, extraída previamente del archivo .par

    Retorna:
    - f_total : array
        Frecuencia total predicha por el modelo en Hz
    - err_arriba : array
        Parte superior de la banda de error
    - err_abajo : array
        Parte inferior de la banda de error
    - f_base : float
        Valor de la frecuencia base
    """
    toas = np.array(toas_array).reshape(-1, 1)

    # Predicción del GP
    delta_f, varianza_f = modelo_gp.predict(toas)
    desv_estandar = np.sqrt(varianza_f)

    # Banda de error
    err_arriba = f_base + delta_f.flatten() + desv_estandar.flatten()
    err_abajo  = f_base + delta_f.flatten() - desv_estandar.flatten()

    # Frecuencia total = modelo base + predicción GP
    f_total = f_base + delta_f.flatten()

    return f_total, err_arriba, err_abajo
# ------ Calculos ------------------

def frequency_residuals_func(toas_array, phase_residuals, n_points=100, method='spline'):
    """
    Computes frequency residuals and derivatives using interpolation.
    
    Parameters:
    ----------
    toas : array_like
        Times of arrival (TOAs).
    phase_residuals : array_like
        Phase residuals.
    n_points : int
        Number of uniform evaluation points.
    method : str
        Interpolation method ('lagrange' or 'spline').

    Returns:
    -------
    t_uniforme : np.ndarray
        Uniform time grid.
    frec_res : np.ndarray
        Frequency residuals (1st derivative).
    dfrec_res : np.ndarray
        Frequency derivative (2nd derivative).
    d2frec_res : np.ndarray
        Second frequency derivative (3rd derivative).
    """
    # Input validation
    toas = np.asarray(toas_array)
    phase_residuals = np.asarray(phase_residuals)
    if len(toas) != len(phase_residuals):
        raise ValueError("toas and phase_residuals must have the same length.")

    # Interpolation
    if method == 'spline':
        interp = make_interp_spline(toas, phase_residuals, k=2)
        
    else:  # Lagrange (fallback)
        from scipy.interpolate import lagrange
        interp = lagrange(toas, phase_residuals)
    
    # Derivatives
    t_uniforme = np.linspace(toas[0], toas[-1], n_points)
    frec_res = interp(t_uniforme, 1)  # 1st derivative
    dfrec_res = interp(t_uniforme, 2)  # 2nd derivative
    d2frec_res = interp(t_uniforme, 3)  # 3rd derivative
    
    return t_uniforme, frec_res, dfrec_res, d2frec_res

def func_braking_index(f, df, d2f):
    """
    Función que retorna el índice de frenado según las listas ingresadas

    Parámetros:
    ------------
    - f : list
        lista de frecuencias
    - df : list 
        lista con derivadas de f
    - d2f : list 
        lista con las dobles derivadas de f

    Retorna:
    ------------
    - n : np.array 
        lista con los índices de frenado respectivos
    """

    #Se concatenan las listas
    v = zip(f, df, d2f)

    #Lista para lso índices de frenado
    n = []

    #Ciclo for para calcular los índices
    for fi, dfi, d2fi in v:

        #Condicionales para evitar dividir por 0
        if dfi != 0:
            n.append(fi * d2fi / (dfi**2))
        else:
            n.append(float("nan"))

    return np.array(n)

def eliminar_duplicados(x, y):
    """
    Elimina duplicados en el array x y mantiene la correspondencia con y.
    Solo conserva la primera aparición de cada valor en x.
    
    Parámetros:
    ----------
    x : array_like
        Array de valores independientes (por ejemplo, tiempos).
    y : array_like
        Array de valores dependientes (por ejemplo, residuales de fase).
        
    Devuelve:
    --------
    x_unicos : np.ndarray
        Array de x sin duplicados, ordenado crecientemente.
    y_unicos : np.ndarray
        y correspondiente a los x únicos.
    """
    x = np.asarray(x)
    y = np.asarray(y)

    # Ordenar por x
    orden = np.argsort(x)
    x_ordenado = x[orden]
    y_ordenado = y[orden]

    # Eliminar duplicados conservando el primero
    x_unicos, indices = np.unique(x_ordenado, return_index=True)
    y_unicos = y_ordenado[indices]

    return x_unicos, y_unicos

def normalizar_tiempos(t):
    t_ref = t.min()        # origen del tiempo
    t_scale = t.max() - t.min()  # duración total
    t_norm = (t - t_ref) / t_scale

    t_normalized = t_norm.reshape(-1, 1)

    return t_normalized, t_ref, t_scale

def desnormalizar_tiempos(t_normalized, t_ref, t_scale): return t_normalized * t_scale + t_ref

# ------ Referente a Graficos ----------

def plot_residuals(residuals, model, show=True, save_path=None, if_grid=False):
    """
    Grafica los residuos de temporización (observado - modelo) de un púlsar.

    Parámetros:
    ----------
    residuals : pint.residuals.Residuals
        Objeto que contiene los residuos calculados.
    model : pint.models.timing_model.TimingModel
        Modelo de temporización del púlsar (archivo .par cargado).

    show : bool, opcional
        Si es True, muestra el gráfico en pantalla.
    save_path : str o None, opcional
        Si se especifica una ruta, guarda la figura como imagen en ese archivo.

    Retorna:
    -------
    None
    """
    pulsar_name = model.PSR.value
    x = residuals.toas.get_mjds()
    x_label = "MJD"
    y = residuals.time_resids.to(u.us).value
    y_err = residuals.toas.get_errors().to(u.us).value

    plt.figure(figsize=(10, 5))
    plt.errorbar(x, y, yerr=y_err, fmt="x", color="blue", ecolor="gray", capsize=2)

    plt.title(f"Residuos Pre-Fit del Púlsar {pulsar_name}")
    plt.xlabel(x_label)
    plt.ylabel("Residuos (μs)")

    if if_grid:
        plt.grid(True)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close()

def big_beautiful_graph(MJD,df,d2f,braking_index):
    """
    Crea un grafico con 3 paneles comparitendo el eje x, en los cuales se muestra la derivada de la 
    frecuencia, su segunda derivada y el braking index.

    Parámetros:
    ----------
    MJD : array
        array que contiene el tiempo en mjd

    df : array
        Derivada de la frecuencia
    
    d2f : array
         Segunda derivada de la frecuencia
    
    braking_index : Numpy array
         Representa el indice de frenado de un pulsar
    Retorna:
    -------
    pint.residuals.Residuals
        Objeto que contiene los residuos de temporización (observado - modelo) en unidades de tiempo.
    """
    # Crear figura con 3 subplots alineados verticalmente que comparten eje X
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, figsize=(6, 8), dpi=100)

    # Primer panel: \dot{\nu}

    # ACLARACIÓN: Todas las unidades acá son placeHolders todavía estoy intentando hacer una función que te tire
    # las unidades con astropy
    ax1.plot(MJD, df, 'k.', markersize=2)

    mgnitude_df = orden_magnitud(df)
    ax1.set_ylabel(rf"$\dot{{\nu}}$ ($10^{{{mgnitude_df}}}$ Hz s$^{{-1}}$)")

    # Segundo panel: \ddot{\nu}
    ax2.plot(MJD, d2f * 1e-20, 'k.', markersize=2)

    mgnitude_d2f = orden_magnitud(d2f)
    ax2.set_ylabel(rf"$\ddot{{\nu}}$ ($10^{{{mgnitude_d2f}}}$ Hz s$^{{-2}}$)")

    # Tercer panel: índice de frenado
    ax3.plot(MJD, braking_index, 'k.', markersize=2)
    ax3.set_ylabel("Braking index")
    ax3.set_xlabel("MJD (d)")

    ax1_top = ax1.secondary_xaxis('top', functions=(mjd_to_year, year_to_mjd))
    ax1_top.set_xlabel("Year")

    # Ajustar espacio vertical
    plt.tight_layout()
    plt.show()

    return fig

def big_beautiful_graph_frecuencys(MJD, frecuency, df, d2f):
    """
    Crea un grafico con 3 paneles comparitendo el eje x, en los cuales se muestra la derivada de la 
    frecuencia, su segunda derivada y el braking index.

    Parámetros:
    ----------
    MJD : array
        array que contiene el tiempo en mjd

    frecuency : array
        array de la frecuencia
    
    df : array
         array de la derivada de frecuencia
    
    d2f : array like
         array de la segunda derivada de la frecuencia
    Retorna:
    -------
        Gráficos con los 3 array
    """
    # Crear figura con 3 subplots alineados verticalmente que comparten eje X
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, figsize=(6, 8), dpi=100)

    # Primer panel: \dot{\nu}

    # ACLARACIÓN: Todas las unidades acá son pre-puestas, todavía estoy intentando hacer una función que te tire
    # las unidades con astropy
    ax1.plot(MJD, frecuency, 'k.', markersize=2)

    mgnitude_f = orden_magnitud(frecuency)
    ax1.set_ylabel(rf"${{\nu}}$ ($10^{{{mgnitude_f}}}$ Hz)")

    # Segundo panel: \ddot{\nu}
    ax2.plot(MJD, df * 1e-20, 'k.', markersize=2)

    mgnitude_df = orden_magnitud(d2f)
    ax2.set_ylabel(rf"$\dot{{\nu}}$ ($10^{{{mgnitude_df}}}$ Hz s$^{{-1}}$)")

    # Tercer panel: índice de frenado
    ax3.plot(MJD, d2f * 1e-20, 'k.', markersize=2)

    mgnitude_d2f = orden_magnitud(d2f)
    ax3.set_ylabel(rf"$\ddot{{\nu}}$ ($10^{{{mgnitude_d2f}}}$ Hz s$^{{-2}}$)")

    ax1_top = ax1.secondary_xaxis('top', functions=(mjd_to_year, year_to_mjd))
    ax1_top.set_xlabel("Year")

    # Ajustar espacio vertical
    plt.tight_layout()
    plt.show() 

    return fig

def big_beautiful_graph_frecuencys_err(MJD, frecuency, df, d2f,
                                   freq_err_arriba=None, freq_err_abajo=None,
                                   df_err_arriba=None, df_err_abajo=None,
                                   d2f_err_arriba=None, d2f_err_abajo=None):
    """
    Gráfico con frecuencia, su derivada y segunda derivada, con errores opcionales.

    Parámetros:
    -----------
    MJD : array
        Tiempos en MJD
    frecuency, df, d2f : arrays
        Frecuencia y derivadas
    *_err_arriba, *_err_abajo : arrays (opcional)
        Límites superior e inferior del error para cada magnitud
    """
    import matplotlib.pyplot as plt

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, figsize=(6, 8), dpi=100)

    # -------- Panel 1: Frecuencia ----------
    mgnitude_f = orden_magnitud(frecuency)
    esc_f = 10 ** mgnitude_f
    ax1.plot(MJD, frecuency / esc_f, 'k.', markersize=2, label="ν")

    if freq_err_arriba is not None and freq_err_abajo is not None:
        freq_err = (freq_err_arriba - freq_err_abajo) / 2 / esc_f
        ax1.fill_between(MJD, (frecuency - freq_err) / esc_f, (frecuency + freq_err) / esc_f,
                         color='gray', alpha=0.3)

    ax1.set_ylabel(rf"${{\nu}}$ ($10^{{{mgnitude_f}}}$ Hz)")

    # -------- Panel 2: Derivada de frecuencia ----------
    mgnitude_df = orden_magnitud(df)
    esc_df = 10 ** mgnitude_df
    ax2.plot(MJD, df / esc_df, 'k.', markersize=2, label="ν̇")

    if df_err_arriba is not None and df_err_abajo is not None:
        df_err = (df_err_arriba - df_err_abajo) / 2 / esc_df
        ax2.fill_between(MJD, (df - df_err) / esc_df, (df + df_err) / esc_df,
                         color='gray', alpha=0.3)

    ax2.set_ylabel(rf"$\dot{{\nu}}$ ($10^{{{mgnitude_df}}}$ Hz s$^{{-1}}$)")

    # -------- Panel 3: Segunda derivada ----------
    mgnitude_d2f = orden_magnitud(d2f)
    esc_d2f = 10 ** mgnitude_d2f
    ax3.plot(MJD, d2f / esc_d2f, 'k.', markersize=2, label="ν̈")

    if d2f_err_arriba is not None and d2f_err_abajo is not None:
        d2f_err = (d2f_err_arriba - d2f_err_abajo) / 2 / esc_d2f
        ax3.fill_between(MJD, (d2f - d2f_err) / esc_d2f, (d2f + d2f_err) / esc_d2f,
                         color='gray', alpha=0.3)

    ax3.set_ylabel(rf"$\ddot{{\nu}}$ ($10^{{{mgnitude_d2f}}}$ Hz s$^{{-2}}$)")

    # Eje de años
    ax1_top = ax1.secondary_xaxis('top', functions=(mjd_to_year, year_to_mjd))
    ax1_top.set_xlabel("Año")

    plt.tight_layout()
    plt.show()

    return fig 

# ---------------- Funciones Auxiliares Graficos -----------------
def mjd_to_year(mjd):
    """
    Convierte MJD (o array de MJDs) a año decimal usando astropy.
    Compatible con funciones vectorizadas de matplotlib.
    """
    t = Time(mjd, format='mjd')
    return np.asarray(t.decimalyear)

def year_to_mjd(year):
    """
    Convierte Años (o array de años) a MJD usando astropy, 
    (es una funcion vectoriazda)
    """
    t = Time(year, format='decimalyear')
    return np.asarray(t.mjd)

def orden_magnitud(array):
    """
    Obtiene el oreden de magnitud del arreglo

    Parámetros:
    lista/array like
        calquier cosa con núeros manito (sin nans porfa)
    -----------

    Retorna
    -----------
    
    numero : int
        numero que representa el orden de magnitud
    """

    array = np.asarray(array)           # Asegura que sea un array de NumPy
    nonzero = array[np.nonzero(array)]  # Filtra ceros (evita log10(0))
    if nonzero.size == 0:
        return 0                        # Si todo es cero, retorna 0
    
    magnitude = int(np.floor(np.log10(np.abs(nonzero).max()))) 
    return magnitude  # Orden de magnitud del valor absoluto más grande

# ------------------------------------------------------------------

# ------------- Archivo ------------
def crear_txt(nombre, tiempo, frecuencias, derfrecuencias):
    """
    Crea un archivo de texto con tres columnas: tiempo, frecuencia y derivada de frecuencia.

    Los datos se escriben en formato de tabla con encabezado y alineación fija para mejor legibilidad.
    El archivo se sobrescribe si ya existe.

    Parámetros:
    ------------
    nombre : str
        Nombre base del archivo (sin extensión .txt).
    tiempo : list or float
        Lista de valores de tiempo.
    frecuencias : list or float
        Lista de valores de frecuencia.
    derfrecuencias : list or float
        Lista de derivadas de frecuencia.

    Retorna:
    ------------
    nombre_archivo : str
        Nombre del archivo generado (con extensión .txt).
    """
    valores = zip(tiempo, frecuencias, derfrecuencias)

    nombre_archivo = f"{nombre}.txt"
    with open(nombre_archivo, mode="w") as archivo:
        archivo.write(f"{'Tiempo':<10} {'Frecuencia':<12} {'Derivada de Frecuencia':<25}\n")

        for Tiempos, Frecuencias, dFrecuencias in valores:
            archivo.write(f"{Tiempos:<10.3f} {Frecuencias:<12.3f} {dFrecuencias:<25.3f}\n")
    return nombre_archivo