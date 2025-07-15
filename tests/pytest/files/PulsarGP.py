import os
import backend as be
import customtkinter as ctk
from astropy.time import Time
from matplotlib.figure import Figure
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class App(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master, fg_color="#357878")

        self.vista_actual = "residuos"

        self.tiempo_resultado = None
        self.frecuencias_resultado = None
        self.derfrecuencias_resultado = None
        self.toas_object_full = None

        self.plot_figure = None
        self.plot_canvas = None

        self.tim_file_path = None
        self.par_file_path = None

        params_frame = ctk.CTkFrame(self, fg_color="#88b0b0", corner_radius=10)
        params_frame.place(relx=0.03, rely=0.05, relwidth=0.45, relheight=0.9)

        results_frame = ctk.CTkFrame(self, fg_color="#88b0b0", corner_radius=10)
        results_frame.place(relx=0.52, rely=0.05, relwidth=0.45, relheight=0.9)

        HEADER_HEIGHT = 30
        TITLE_FONT_SIZE = 30

        header_container = ctk.CTkFrame(master=results_frame, fg_color="transparent", height=HEADER_HEIGHT)
        header_container.place(relx=0.5, rely=0.05, relwidth=0.9, anchor="n")
        header_container.grid_columnconfigure(0, weight=1) # Columna del título (expandible)
        header_container.grid_columnconfigure(1, weight=0) # Columna de los botones (fija)
        header_container.grid_rowconfigure(0, weight=1)
        
        results_title_button = ctk.CTkButton(
            master=header_container,
            text="Resultados",
            font=("Baloo", TITLE_FONT_SIZE, "bold"),
            fg_color="#b8cfcf",
            border_width=3,
            border_color="#418080",
            corner_radius=10,
            text_color="#418080",
            text_color_disabled="#418080",
            state="disabled"
        )
        results_title_button.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        action_buttons_frame = ctk.CTkFrame(master=header_container, fg_color="transparent")
        action_buttons_frame.grid(row=0, column=1, sticky="e")

        self.toggle_plot_button = ctk.CTkButton(
            master=action_buttons_frame,
            text="Ver Análisis GP",
            font=("Baloo", 14),
            height=HEADER_HEIGHT,
            width=HEADER_HEIGHT,
            fg_color="#b8cfcf",
            text_color="#418080",
            hover_color="#a8bebe",
            border_width=3,
            border_color="#418080",
            corner_radius=10,
            command=self.toggle_vista_grafico
        )
        self.toggle_plot_button.pack(side="left", padx=(0, 10))

        self.new_window_button = ctk.CTkButton(
            master=action_buttons_frame,
            text="Abrir en Ventanas",
            font=("Baloo", 14),
            height=HEADER_HEIGHT,
            width=HEADER_HEIGHT,
            fg_color="#b8cfcf",
            text_color="#418080",
            hover_color="#a8bebe",
            border_width=3,
            border_color="#418080",
            corner_radius=10,
            command=self.abrir_graficos_en_ventanas
        )
        self.new_window_button.pack(side="left", padx=(0, 10))

        self.download_button = ctk.CTkButton(
            master=action_buttons_frame, # Su 'master' ahora es action_buttons_frame
            text="↓",
            font=("Arial", 20, "bold"),
            height=HEADER_HEIGHT,
            width=HEADER_HEIGHT,
            fg_color="#b8cfcf",
            text_color="#418080",
            hover_color="#a8bebe",
            border_width=3,
            border_color="#418080",
            corner_radius=10,
            command=self.guardar_archivo_txt
        )
        self.download_button.pack(side="left")

        self.plot_frame = ctk.CTkFrame(
            master=results_frame,
            fg_color="#acc7c7",
            corner_radius=10
        )
        self.plot_frame.place(
            relx=0.5,
            rely=0.18,
            relwidth=0.9,
            relheight=0.78,
            anchor="n"
        )

        self.plot_frame.bind("<Configure>", self.on_plot_resize)



        params_title_button = ctk.CTkButton(
            master=params_frame,
            text="Parametros",
            font=("Baloo", TITLE_FONT_SIZE, "bold"),
            height=HEADER_HEIGHT,
            fg_color="#b8cfcf",
            border_width=3,
            border_color="#418080",
            corner_radius=10,
            text_color="#418080",
            state="disabled",
            text_color_disabled="#418080" 
        )
        params_title_button.place(relx=0.5, rely=0.05, relwidth=0.9, anchor="n")

        select_file_bubble = ctk.CTkButton(
            master=params_frame,
            text="Seleccione los archivos",
            font=("Baloo", 24, "bold"),
            fg_color="#b8cfcf",
            border_width=3,
            border_color="#418080",
            corner_radius=10,
            text_color="#418080",
            text_color_disabled="#418080",
            state="disabled"
        )
        select_file_bubble.place(relx=0.5, rely=0.20, relwidth=0.7, anchor="n")

        self.tim_button = ctk.CTkButton(
            master=params_frame,
            text=".tim",
            font=("Baloo", 20, "bold"),
            height=40,
            command=self.seleccionar_archivo_tim,
            fg_color="#b8cfcf",
            border_width=3,
            border_color="#418080",
            corner_radius=10,
            text_color="#418080",
            hover_color="#a8bebe"
        )
        self.tim_button.place(relx=0.5, rely=0.30, relwidth=0.5, anchor="n")

        self.par_button = ctk.CTkButton(
            master=params_frame,
            text=".par",
            font=("Baloo", 20, "bold"),
            height=40,
            command=self.seleccionar_archivo_par,
            fg_color="#b8cfcf",
            border_width=3,
            border_color="#418080",
            corner_radius=10,
            text_color="#418080",
            hover_color="#a8bebe"
        )
        self.par_button.place(relx=0.5, rely=0.38, relwidth=0.5, anchor="n")

        self.tim_button.drop_target_register(DND_FILES)
        self.par_button.drop_target_register(DND_FILES)
        self.tim_button.dnd_bind('<<Drop>>', self.soltar_archivo_tim)
        self.par_button.dnd_bind('<<Drop>>', self.soltar_archivo_par)

        generate_row_container = ctk.CTkFrame(master=params_frame, fg_color="transparent")
        generate_row_container.place(relx=0.5, rely=0.50, relwidth=0.9, anchor="n")

        generate_row_container.grid_columnconfigure(0, weight=1)
        generate_row_container.grid_columnconfigure(1, weight=0)
        generate_row_container.grid_columnconfigure(2, weight=2)

        generate_file_bubble = ctk.CTkButton(
            master=generate_row_container,
            text="¿Generar archivo?",
            font=("Baloo", 17, "bold"),
            fg_color="#b8cfcf",
            border_width=3,
            border_color="#418080",
            corner_radius=10,
            text_color="#418080",
            text_color_disabled="#418080",
            state="disabled"
        )
        generate_file_bubble.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=5)

        self.generate_file_switch = ctk.CTkSwitch(
            master=generate_row_container,
            text="",
            progress_color="#418080",
            button_color="#b8cfcf",
            button_hover_color="#a8bebe"
        )
        self.generate_file_switch.grid(row=0, column=1, padx=(0, 10), pady=5)

        self.filename_entry = ctk.CTkEntry(
            master=generate_row_container,
            placeholder_text="Nombre del archivo",
            font=("Baloo", 17, "bold"),
            fg_color="#b8cfcf",
            border_width=3,
            border_color="#418080",
            corner_radius=10,
            text_color="#418080",
            placeholder_text_color="#7a9e9e"
        )
        self.filename_entry.grid(row=0, column=2, sticky="ew", pady=5)

        time_unit_container = ctk.CTkFrame(master=params_frame, fg_color="transparent")
        time_unit_container.place(relx=0.5, rely=0.60, relwidth=0.9, anchor="n")
        time_unit_container.grid_columnconfigure(0, weight=1)

        time_unit_label = ctk.CTkButton(
            master=time_unit_container,
            text="Unidad de tiempo",
            font=("Baloo", 17, "bold"),
            fg_color="#b8cfcf",
            border_width=3,
            border_color="#418080",
            corner_radius=10,
            text_color="#418080",
            text_color_disabled="#418080",
            state="disabled"
        )
        time_unit_label.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        self.time_unit_menu = ctk.CTkOptionMenu(
            master=time_unit_container,
            font=("Baloo", 17, "bold"),
            fg_color="#b8cfcf",
            button_color="#b8cfcf",
            button_hover_color="#a8bebe",
            text_color="#418080",
            dropdown_fg_color="#b8cfcf",
            dropdown_text_color="#418080",
            dropdown_hover_color="#a8bebe",
            values=["Segundo", "Milisegundo", "Microsegundo", "Nanosegundo"]
        )
        self.time_unit_menu.set("Segundo")
        self.time_unit_menu.grid(row=1, column=0, sticky="ew")

        date_range_container = ctk.CTkFrame(master=params_frame, fg_color="transparent")
        date_range_container.place(relx=0.5, rely=0.75, relwidth=0.9, anchor="n")
        date_range_container.grid_columnconfigure((0, 1), weight=1)

        start_label = ctk.CTkLabel(master=date_range_container, text="Inicio del intervalo (MJD):", font=("Baloo", 20), text_color="#418080")
        start_label.grid(row=0, column=0, sticky="w", pady=(0,5))
        
        self.start_mjd_entry = ctk.CTkEntry(
            master=date_range_container,
            font=("Baloo", 14),
            fg_color="#b8cfcf",
            border_width=2,
            border_color="#418080",
            text_color="#418080"
        )
        self.start_mjd_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        
        end_label = ctk.CTkLabel(master=date_range_container, text="Final del intervalo (MJD):", font=("Baloo", 20), text_color="#418080")
        end_label.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(0,5))

        self.end_mjd_entry = ctk.CTkEntry(
            master=date_range_container,
            font=("Baloo", 14),
            fg_color="#b8cfcf",
            border_width=2,
            border_color="#418080",
            text_color="#418080"
        )
        self.end_mjd_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0))


        execute_container = ctk.CTkFrame(master=params_frame, fg_color="transparent")
        execute_container.place(relx=0.5, rely=0.97, anchor="s")

        self.min_date_label = ctk.CTkLabel(
            master=execute_container,
            text="Min:",
            font=("Baloo", 24),
            text_color="#418080"
        )
        self.min_date_label.pack(side="left", padx=10)

        self.execute_button = ctk.CTkButton(
            master=execute_container,
            text="►",
            font=("Arial", 30, "bold"),
            width=50,
            height=50,
            fg_color="#418080",
            hover_color="#357878",
            command=self.ejecutar_proceso
        )
        self.execute_button.pack(side="left", padx=10)

        self.max_date_label = ctk.CTkLabel(
            master=execute_container,
            text="Max:",
            font=("Baloo", 24),
            text_color="#418080"
        )
        self.max_date_label.pack(side="left", padx=10)

    def ejecutar_proceso(self):
        """
        Función principal que ejecuta toda la cadena de procesamiento y muestra el gráfico inicial.
        """
        if self.toas_object_full is None or not self.par_file_path:
            messagebox.showwarning("Archivos Faltantes", "Por favor, selecciona los archivos .tim y .par.")
            return

        print("Iniciando procesamiento completo con el backend...")
        try:
            # Guardamos los datos en variables de instancia para que sean accesibles por otras funciones
            toas_object = self.toas_object_full
            mjds = toas_object.get_mjds()
            self.residuals_object, self.model_object = be.compute_residuals(self.par_file_path, toas_object)
            
            self.clean_toas, clean_phase_res = be.eliminar_duplicados(mjds.value, self.residuals_object.phase_resids.value)
            norm_toas, _, _ = be.normalizar_tiempos(self.clean_toas)
            _, f_resid, df_resid, d2f_resid = be.frequency_residuals_func(self.clean_toas, clean_phase_res, n_points=norm_toas.size)
            
            self.f_res_Hz = f_resid / 86400.0
            df_res_Hz = df_resid / (86400.0 ** 2)
            d2f_res_Hz = d2f_resid / (86400.0 ** 3)

            self.f_gp_model = be.entrenamiento_gp_model(norm_toas, self.f_res_Hz)
            df_gp_model = be.entrenamiento_gp_model(norm_toas, df_res_Hz)
            d2f_gp_model = be.entrenamiento_gp_model(norm_toas, d2f_res_Hz)

            f_base = self.model_object.F0.value
            self.f_total, self.f_err_up, self.f_err_down = be.obtener_frecuencia_total_y_errores(norm_toas, self.f_gp_model, f_base)
            self.df_total, self.df_err_up, self.df_err_down = be.obtener_frecuencia_total_y_errores(norm_toas, df_gp_model, f_base=0.0)
            self.d2f_total, self.d2f_err_up, self.d2f_err_down = be.obtener_frecuencia_total_y_errores(norm_toas, d2f_gp_model, f_base=0.0)

            self.tiempo_resultado = self.clean_toas
            self.frecuencias_resultado = self.f_total
            self.derfrecuencias_resultado = self.df_total

            self.selected_unit = self.time_unit_menu.get()
            self.unit_map = {"Segundo": "s", "Milisegundo": "ms", "Microsegundo": "us", "Nanosegundo": "ns"}
            unit_symbol = self.unit_map.get(self.selected_unit, "s")
            
            fig = be.plot_residuals(self.residuals_object, self.model_object, unit=unit_symbol)
            self._draw_plot(fig)
            self.toggle_plot_button.configure(text="Ver Modelo GP")
            self.vista_actual = "residuos"

            messagebox.showinfo("Proceso Completo", "Análisis finalizado. Se muestra el gráfico de residuos.")

        except Exception as e:
            messagebox.showerror("Error en el Backend", f"Ocurrió un error durante el procesamiento:\n{e}")
            print(f"Error en el backend: {e}")

    def validate_digits(self, text, max_length):
        return text.isdigit() and len(text) <= max_length
    
    def validate_date_entry(self, entry_widget, max_length):
        current_text = entry_widget.get()
        new_text = "".join(filter(str.isdigit, current_text))[:max_length]
        if new_text != current_text:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, new_text)

    def guardar_archivo_txt(self):
        """
        Verifica el estado del toggle, abre un diálogo "Guardar como..." 
        y escribe los resultados en un archivo .txt.
        """
        if self.generate_file_switch.get() == 0:
            messagebox.showinfo(
                "Función Desactivada", 
                "Para guardar el archivo, activa primero el interruptor de '¿Generar archivo?'."
            )
            return

        if self.tiempo_resultado is None:
            messagebox.showwarning("Sin Datos", "Primero debes ejecutar el proceso para generar los datos.")
            return

        suggested_name = self.filename_entry.get()
        if not suggested_name:
            suggested_name = "resultados_pulsar.txt"
        else:
            if not suggested_name.lower().endswith('.txt'):
                suggested_name += ".txt"

        try:
            filepath = filedialog.asksaveasfilename(
                initialfile=suggested_name,
                title="Guardar archivo de resultados",
                defaultextension=".txt",
                filetypes=(("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*"))
            )

            if filepath:
                with open(filepath, mode="w") as archivo:
                    archivo.write(f"{'Tiempo':<10} {'Frecuencia':<12} {'Derivada de Frecuencia':<25}\n")
                    valores = zip(self.tiempo_resultado, self.frecuencias_resultado, self.derfrecuencias_resultado)
                    for Tiempos, Frecuencias, dFrecuencias in valores:
                        archivo.write(f"{Tiempos:<10.3f} {Frecuencias:<12.3f} {dFrecuencias:<25.3f}\n")
                
                messagebox.showinfo("Éxito", f"Archivo guardado correctamente en:\n{filepath}")

        except Exception as e:
            messagebox.showerror("Error al Guardar", f"Ocurrió un error al intentar guardar el archivo:\n{e}")

    def on_plot_resize(self, event):
        """
        Se ejecuta cada vez que el plot_frame cambia de tamaño.
        Ajusta el tamaño de la fuente del gráfico de forma proporcional.
        """
        if self.plot_figure is None:
            return

        new_width = event.width

        title_fontsize = new_width / 45
        label_fontsize = new_width / 55
        ticks_fontsize = new_width / 65

        ax = self.plot_figure.get_axes()[0]

        ax.set_title(ax.get_title(), fontsize=title_fontsize)
        ax.set_xlabel(ax.get_xlabel(), fontsize=label_fontsize)
        ax.set_ylabel(ax.get_ylabel(), fontsize=label_fontsize)
        ax.tick_params(axis='both', which='major', labelsize=ticks_fontsize)
        
        self.plot_canvas.draw()

    def procesar_seleccion_archivo(self, widget, ruta_archivo, tipo_archivo):
        if ruta_archivo:
            nombre_archivo = os.path.basename(ruta_archivo)
            widget.configure(text=nombre_archivo)
            if tipo_archivo == 'tim':
                self.tim_file_path = ruta_archivo
            elif tipo_archivo == 'par':
                self.par_file_path = ruta_archivo

    def load_and_display_tim_info(self, filepath):
        """Carga el archivo .tim, extrae las fechas min/max y actualiza la UI."""
        try:
            print(f"Cargando archivo .tim: {filepath}")
            self.tim_file_path = filepath
            mjds, _ = be.load_toas(self.tim_file_path, return_also_mjds=True)

            min_date = Time(mjds.min(), format='mjd').to_datetime().strftime('%d-%m-%Y')
            max_date = Time(mjds.max(), format='mjd').to_datetime().strftime('%d-%m-%Y')

            self.min_date_label.configure(text=f"Min: {min_date}")
            self.max_date_label.configure(text=f"Max: {max_date}")

            self.procesar_seleccion_archivo(self.tim_button, filepath, 'tim')
            print("Fechas de TOAs actualizadas en la UI.")

        except Exception as e:
            messagebox.showerror("Error al Cargar Archivo", f"No se pudo procesar el archivo .tim:\n{e}")
            self.tim_file_path = None

    def seleccionar_archivo_tim(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo .tim", filetypes=(("TIM files", "*.tim"), ("All files", "*.*"))
        )
        if ruta and ruta.lower().endswith('.tim'):
            self.procesar_seleccion_archivo(self.tim_button, ruta, 'tim')
            self._check_and_update_date_info()
        elif ruta:
            messagebox.showerror("Error de Archivo", "El archivo seleccionado no es un archivo .tim válido.")

    def seleccionar_archivo_par(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo .par", filetypes=(("PAR files", "*.par"), ("All files", "*.*"))
        )
        if ruta and ruta.lower().endswith('.par'):
            self.procesar_seleccion_archivo(self.par_button, ruta, 'par')
            self._check_and_update_date_info()
        elif ruta:
            messagebox.showerror("Error de Archivo", "El archivo seleccionado no es un archivo .par válido.")

    def soltar_archivo_tim(self, event):
        ruta = event.data.strip('{}')
        if ruta.lower().endswith('.tim'):
            self.procesar_seleccion_archivo(self.tim_button, ruta, 'tim')
            self._check_and_update_date_info()

    def soltar_archivo_par(self, event):
        ruta = event.data.strip('{}')
        if ruta.lower().endswith('.par'):
            self.procesar_seleccion_archivo(self.par_button, ruta, 'par')
            self._check_and_update_date_info()

    def _check_and_update_date_info(self):
        """
        Verifica si ambos archivos están listos, extrae las fechas MJD min/max,
        y actualiza la interfaz.
        """
        if not self.tim_file_path or not self.par_file_path:
            return

        print("Ambos archivos seleccionados. Actualizando rango de fechas MJD...")
        try:
            mjds, self.toas_object_full = be.load_toas(self.tim_file_path)

            if len(self.toas_object_full) == 0: return

            min_mjd = mjds.min().value
            max_mjd = mjds.max().value
            
            self.min_date_label.configure(text=f"Min: {min_mjd:.4f}")
            self.max_date_label.configure(text=f"Max: {max_mjd:.4f}")

            self.start_mjd_entry.delete(0, "end")
            self.end_mjd_entry.delete(0, "end")
            self.start_mjd_entry.insert(0, f"{min_mjd:.4f}")
            self.end_mjd_entry.insert(0, f"{max_mjd:.4f}")
            
            print("Rango de fechas MJD y campos de texto actualizados.")

        except Exception as e:
            messagebox.showerror("Error al Cargar Archivo .tim", f"No se pudo procesar el archivo para obtener las fechas:\n{e}")
            self.tim_file_path = None
            self.toas_object_full = None

    def _draw_plot(self, fig):
        """Función auxiliar para limpiar y dibujar una figura en el canvas."""
        # Limpiar cualquier widget anterior
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        
        # Guardar la figura y el lienzo para la función de redimensionamiento
        self.plot_figure = fig
        self.plot_canvas = FigureCanvasTkAgg(self.plot_figure, master=self.plot_frame)
        self.plot_canvas.draw()
        
        # Añadir la barra de herramientas
        toolbar = NavigationToolbar2Tk(self.plot_canvas, self.plot_frame)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")
        
        # Añadir el lienzo del gráfico
        self.plot_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

# Dentro de tu clase App, reemplaza estos dos métodos completos

    def toggle_vista_grafico(self):
        """Alterna el gráfico INCURSTADO entre residuos y el modelo GP."""
        if not hasattr(self, 'model_object'):
            messagebox.showinfo("Información", "Primero debes ejecutar el proceso principal.")
            return

        try:
            # Si estamos viendo los residuos, cambiamos al gráfico de 3 paneles
            if self.vista_actual == "residuos":
                print("Cambiando a vista de Análisis GP (incrustado)...")
                # Llamamos a la función SIN que muestre una ventana nueva
                fig = be.big_beautiful_graph_frecuencys_err(
                    self.clean_toas, self.f_total, self.df_total, self.d2f_total,
                    self.f_err_up, self.f_err_down, self.df_err_up, self.df_err_down,
                    self.d2f_err_up, self.d2f_err_down, show_window=False
                )
                self._draw_plot(fig)
                self.toggle_plot_button.configure(text="Ver Residuos")
                self.vista_actual = "gp"
            
            # Si estamos viendo el GP, cambiamos al gráfico de residuos
            else:
                print("Cambiando a vista de Residuos (incrustado)...")
                unit_symbol = self.unit_map.get(self.selected_unit, "us")
                # Llamamos a la función SIN que muestre una ventana nueva
                fig = be.plot_residuals(self.residuals_object, self.model_object, unit=unit_symbol, show_window=False)
                self._draw_plot(fig)
                self.toggle_plot_button.configure(text="Ver Análisis GP")
                self.vista_actual = "residuos"
        except Exception as e:
            messagebox.showerror("Error al Graficar", f"No se pudo generar el nuevo gráfico:\n{e}")

    def abrir_graficos_en_ventanas(self):
        """Llama al backend para que muestre los gráficos en ventanas nuevas."""
        if not hasattr(self, 'model_object'):
            messagebox.showinfo("Información", "Primero debes ejecutar el proceso principal.")
            return
        
        try:
            print("Abriendo gráficos en ventanas emergentes...")
            # 1. Gráfico de Residuos
            unit_symbol = self.unit_map.get(self.selected_unit, "us")
            be.plot_residuals(self.residuals_object, self.model_object, unit=unit_symbol, show_window=True)
            
            # 2. Gráfico de 3 paneles
            be.big_beautiful_graph_frecuencys_err(
                self.clean_toas, self.f_total, self.df_total, self.d2f_total,
                self.f_err_up, self.f_err_down, self.df_err_up, self.df_err_down,
                self.d2f_err_up, self.d2f_err_down, show_window=True
            )
        except Exception as e:
            messagebox.showerror("Error al Graficar", f"No se pudo generar los gráficos:\n{e}")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    root.title("PulsarGP")
    root.geometry("1280x720")
    root.configure(bg="#357878")

    ctk.set_appearance_mode("Dark")

    app = App(master=root)
    app.pack(expand=True, fill="both")

    root.mainloop()