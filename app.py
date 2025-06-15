import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta, time

# ==================== FUNCIONES PARA PROCESAMIENTO DE HORAS ====================

def convertir_a_str(hora):
    """Función para convertir hora a string si es necesario"""
    if isinstance(hora, time):
        return hora.strftime("%H:%M:%S")
    elif isinstance(hora, str):
        return hora
    return None

def calcular_horas(inicio_raw, fin_raw, refrigerio_inicio_raw=None, refrigerio_fin_raw=None):
    """Función principal de cálculo de horas laborales"""
    formato = "%H:%M:%S"
    inicio_str = convertir_a_str(inicio_raw)
    fin_str = convertir_a_str(fin_raw)
    refrigerio_inicio_str = convertir_a_str(refrigerio_inicio_raw)
    refrigerio_fin_str = convertir_a_str(refrigerio_fin_raw)

    if not inicio_str or not fin_str:
        return [0]*8

    try:
        inicio = datetime.strptime(inicio_str, formato)
        fin = datetime.strptime(fin_str, formato)
        if fin <= inicio:
            fin += timedelta(days=1)

        # Descontar refrigerio si es de 13:00 a 14:00
        descontar_refrigerio = False
        if refrigerio_inicio_str and refrigerio_fin_str:
            ri = datetime.strptime(refrigerio_inicio_str, formato).time()
            rf = datetime.strptime(refrigerio_fin_str, formato).time()
            if ri == time(13, 0) and rf == time(14, 0):
                descontar_refrigerio = True

        minutos_diurnos_total = 0
        minutos_nocturnos_total = 0

        actual = inicio
        while actual < fin:
            hora = actual.time()
            if time(6, 0) <= hora < time(22, 0):
                minutos_diurnos_total += 1
            else:
                minutos_nocturnos_total += 1
            actual += timedelta(minutes=1)

        total_minutos = minutos_diurnos_total + minutos_nocturnos_total

        # Descontar 1h de refrigerio si corresponde
        if descontar_refrigerio:
            if minutos_diurnos_total >= 60:
                minutos_diurnos_total -= 60
            else:
                restante = 60 - minutos_diurnos_total
                minutos_diurnos_total = 0
                minutos_nocturnos_total = max(0, minutos_nocturnos_total - restante)
            total_minutos -= 60

        # Normales y extras
        minutos_normales = min(total_minutos, 480)
        minutos_extras = max(0, total_minutos - 480)

        minutos_diurnos_normales = 0
        minutos_nocturnos_normales = 0
        actual = inicio
        minutos_asignados = 0
        while actual < fin and minutos_asignados < minutos_normales:
            hora = actual.time()
            if time(6, 0) <= hora < time(22, 0):
                minutos_diurnos_normales += 1
            else:
                minutos_nocturnos_normales += 1
            minutos_asignados += 1
            actual += timedelta(minutes=1)

        horas_diurnas = minutos_diurnos_normales / 60
        horas_nocturnas = minutos_nocturnos_normales / 60

        horas_extra_25 = min(minutos_extras, 120) / 60
        horas_extra_35 = max(minutos_extras - 120, 0) / 60

        horas_extra_25_nocturna = 0
        horas_extra_35_nocturna = 0

        if inicio.time() >= time(15, 0) and inicio.time() < time(20, 0):
            horas_extra_25_nocturna = horas_extra_25
            horas_extra_35_nocturna = round(horas_diurnas, 2) - horas_extra_25_nocturna 
            horas_extra_25 = 0
            horas_extra_35 = horas_extra_35 - horas_extra_35_nocturna

        if inicio.time() >= time(20, 0) and inicio.time() < time(22, 0):
            horas_extra_25_nocturna = round(horas_diurnas, 2)
            horas_extra_35_nocturna = 0
            horas_extra_25 = horas_extra_25 - horas_extra_25_nocturna
            horas_extra_35 = horas_extra_35

        total_horas = (minutos_diurnos_total + minutos_nocturnos_total) / 60

        return max(round(horas_diurnas, 2), 0), max(round(horas_nocturnas, 2), 0), \
               max(round(minutos_normales / 60, 2), 0), max(round(horas_extra_25, 2), 0), \
               max(round(horas_extra_35, 2), 0), max(round(horas_extra_25_nocturna, 2), 0), \
               max(round(horas_extra_35_nocturna, 2), 0), max(round(total_horas, 2), 0)

    except Exception as e:
        st.error(f"Error al procesar: {inicio_str} - {fin_str}. {e}")
        return [0]*8

def procesar_fila_horas(row):
    """Función para procesar cada fila del DataFrame de horas"""
    dia = str(row["DIA"]).strip().lower()
    dias_normales = ['lunes', 'martes', 'miércoles', 'miercoles', 'jueves', 'viernes', 'sábado', 'sabado']

    resultado = calcular_horas(
        row["Hora Inicio Labores"], 
        row["Hora Término Labores"], 
        row.get("Hora Inicio Refrigerio", None),
        row.get("Hora Término Refrigerio", None)
    )

    if dia in dias_normales:
        return {
            "Horas Diurnas": resultado[0],
            "Horas Nocturnas": resultado[1],
            "Horas Normales": resultado[2],
            "Extra 25%": resultado[3],
            "Extra 35%": resultado[4],
            "Extra 25% Nocturna": resultado[5],
            "Extra 35% Nocturna": resultado[6],
            "Total Horas": resultado[7],
            "Horas Domingo/Feriado": 0,
            "Horas Extra Domingo/Feriado": 0
        }
    else:  # Domingo o feriado
        total_horas = resultado[7]
        horas_base = min(total_horas, 8)
        horas_extra = max(total_horas - 8, 0)
        return {
            "Horas Diurnas": 0,
            "Horas Nocturnas": 0,
            "Horas Normales": 0,
            "Extra 25%": 0,
            "Extra 35%": 0,
            "Extra 25% Nocturna": 0,
            "Extra 35% Nocturna": 0,
            "Total Horas": total_horas,
            "Horas Domingo/Feriado": round(horas_base, 2),
            "Horas Extra Domingo/Feriado": round(horas_extra, 2)
        }

# ==================== FUNCIONES PARA CONTROL DE ASISTENCIA ====================

def procesar_tareo(df):
    """Función para procesar el tareo y calcular faltas"""
    try:
        # Crear tabla dinámica para consolidar horas por día
        tareo_pivot = df.pivot_table(
            index=["DNI", "Apellidos y Nombres"],
            columns="DIA",
            values="HORAS TRABAJ.",
            aggfunc="sum",
            fill_value=0
        ).reset_index()

        # Ordenar los días de la semana
        dias_orden = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        columnas = ["DNI", "Apellidos y Nombres"] + dias_orden

        # Agregar columnas que falten si algún día no apareció en el dataset
        for dia in dias_orden:
            if dia not in tareo_pivot.columns:
                tareo_pivot[dia] = 0

        # Calcular el total de horas semanales por trabajador
        tareo_pivot["Total Semanal"] = tareo_pivot[dias_orden].sum(axis=1)

        # Reordenar las columnas
        tareo_final = tareo_pivot[columnas + ["Total Semanal"]].copy()

        # Reemplazar 0 por 'F' en los días de lunes a sábado
        for dia in ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado"]:
            if dia in tareo_final.columns:
                tareo_final[dia] = tareo_final[dia].apply(lambda x: "F" if x == 0 else x)

        # Calcular el total de faltas por trabajador
        tareo_final["Total Faltas"] = tareo_final[dias_orden].apply(
            lambda row: sum(str(x).strip().upper() == "F" for x in row), axis=1
        )

        # Reordenar columnas finales
        columnas_finales = ["DNI", "Apellidos y Nombres"] + dias_orden + ["Total Semanal", "Total Faltas"]
        tareo_final = tareo_final[columnas_finales]

        return tareo_final

    except Exception as e:
        st.error(f"Error al procesar el tareo: {str(e)}")
        return None

def generar_reporte_tramos_faltas(tareo_final, fecha_inicio_semana):
    """Función para generar el segundo reporte de tramos de faltas con fechas"""
    try:
        # Días de la semana y su offset
        dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        offset_dias = {dia: fecha_inicio_semana + timedelta(days=i) for i, dia in enumerate(dias_semana)}

        # Lista para guardar tramos detectados
        tramos_faltas = []

        # Analizar por trabajador
        for _, fila in tareo_final.iterrows():
            dni = fila["DNI"]
            nombres = fila["Apellidos y Nombres"]
            tramo = []

            for dia in dias_semana:
                valor = str(fila.get(dia, "")).strip().upper()
                if valor == "F":
                    tramo.append(dia)
                else:
                    if tramo:
                        tramos_faltas.append({
                            "DNI": dni,
                            "Apellidos y Nombres": nombres,
                            "Fecha Inicial": offset_dias[tramo[0]].strftime("%d/%m/%Y"),
                            "Cantidad de Días": len(tramo),
                            "Fecha Final": offset_dias[tramo[-1]].strftime("%d/%m/%Y")
                        })
                        tramo = []

            # Si termina la semana con faltas
            if tramo:
                tramos_faltas.append({
                    "DNI": dni,
                    "Apellidos y Nombres": nombres,
                    "Fecha Inicial": offset_dias[tramo[0]].strftime("%d/%m/%Y"),
                    "Cantidad de Días": len(tramo),
                    "Fecha Final": offset_dias[tramo[-1]].strftime("%d/%m/%Y")
                })

        # Convertir resultado a DataFrame
        df_tramos = pd.DataFrame(tramos_faltas)
        
        return df_tramos

    except Exception as e:
        st.error(f"Error al generar reporte de tramos: {str(e)}")
        return None

# ==================== APLICACIÓN PRINCIPAL ====================

def main():
    st.set_page_config(
        page_title="Sistema Integral de Gestión Laboral",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Sistema Integral de Gestión Laboral")
    st.markdown("### Procesamiento de horas laborales y control de asistencia")
    
    # Sidebar para configuración
    st.sidebar.header("⚙️ Configuración")
    
    # Selector de módulo
    modulo = st.sidebar.selectbox(
        "Selecciona el módulo:",
        ["📈 Procesador de Horas Laborales", "👥 Control de Asistencia y Faltas", "🔄 Procesamiento Integral (3 Reportes)"]
    )
    
    if modulo == "📈 Procesador de Horas Laborales":
        procesar_modulo_horas()
    elif modulo == "👥 Control de Asistencia y Faltas":
        procesar_modulo_asistencia()
    else:
        procesar_modulo_integral()

def procesar_modulo_horas():
    """Módulo para procesamiento de horas laborales"""
    st.header("📈 Procesador de Horas Laborales")
    
    # Información sobre el formato esperado
    with st.expander("ℹ️ Formato de archivo esperado para horas"):
        st.markdown("""
        **El archivo Excel debe contener una hoja llamada 'Horas' con las siguientes columnas:**
        - `DIA`: Día de la semana (lunes, martes, miércoles, jueves, viernes, sábado, domingo)
        - `Hora Inicio Labores`: Hora de inicio en formato HH:MM:SS
        - `Hora Término Labores`: Hora de término en formato HH:MM:SS
        - `Hora Inicio Refrigerio`: (Opcional) Hora de inicio del refrigerio
        - `Hora Término Refrigerio`: (Opcional) Hora de término del refrigerio
        
        **Cálculos realizados:**
        - Horas diurnas (06:00-22:00) y nocturnas (22:00-06:00)
        - Horas normales (hasta 8 horas) y extras
        - Sobretiempo con recargo del 25% y 35%
        - Tratamiento especial para domingos y feriados
        - Descuento automático de refrigerio (13:00-14:00)
        """)
    
    # Upload file
    uploaded_file = st.file_uploader(
        "📁 Selecciona el archivo Excel con datos de horas",
        type=['xlsx', 'xls'],
        help="Sube un archivo Excel con los datos de horas laborales",
        key="horas_upload"
    )
    
    if uploaded_file is not None:
        try:
            # Read the Excel file
            with st.spinner("📖 Leyendo archivo Excel..."):
                df = pd.read_excel(uploaded_file, sheet_name="Horas")
            
            st.success(f"✅ Archivo cargado exitosamente. {len(df)} filas encontradas.")
            
            # Display original data
            st.subheader("📋 Datos originales")
            st.dataframe(df, use_container_width=True)
            
            # Process data
            if st.button("🔄 Procesar horas laborales", type="primary"):
                with st.spinner("⚙️ Procesando datos..."):
                    try:
                        # Apply processing to each row
                        resultados_dict = df.apply(procesar_fila_horas, axis=1, result_type="expand")
                        
                        # Combine original data with results
                        df_final = pd.concat([df, resultados_dict], axis=1)
                        
                        st.success("✅ Horas procesadas exitosamente!")
                        
                        # Display processed data
                        st.subheader("📊 Resultados de Horas Calculadas")
                        
                        # Show only the calculated columns for better readability
                        calculated_columns = [
                            "Horas Diurnas", "Horas Nocturnas", "Horas Normales",
                            "Extra 25%", "Extra 35%", "Extra 25% Nocturna", 
                            "Extra 35% Nocturna", "Total Horas",
                            "Horas Domingo/Feriado", "Horas Extra Domingo/Feriado"
                        ]
                        
                        # Display calculated results
                        st.dataframe(df_final[calculated_columns], use_container_width=True)
                        
                        # Summary statistics
                        st.subheader("📈 Resumen de Horas")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            total_horas_normales = df_final["Horas Normales"].sum()
                            st.metric("Total Horas Normales", f"{total_horas_normales:.2f}")
                        
                        with col2:
                            total_extra_25 = df_final["Extra 25%"].sum()
                            st.metric("Total Extra 25%", f"{total_extra_25:.2f}")
                        
                        with col3:
                            total_extra_35 = df_final["Extra 35%"].sum()
                            st.metric("Total Extra 35%", f"{total_extra_35:.2f}")
                        
                        with col4:
                            total_horas = df_final["Total Horas"].sum()
                            st.metric("Total Horas", f"{total_horas:.2f}")
                        
                        # Download processed file
                        st.subheader("💾 Descargar Resultado")
                        
                        # Create Excel file in memory
                        output = io.BytesIO()
                        df_final.to_excel(output, sheet_name='Horas_Procesadas', index=False, engine='openpyxl')
                        excel_data = output.getvalue()
                        
                        st.download_button(
                            label="📥 Descargar reporte de horas procesadas",
                            data=excel_data,
                            file_name="reporte_horas_procesado.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            help="Descarga el archivo Excel con todos los cálculos de horas realizados"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Error al procesar los datos: {str(e)}")
                        st.error("Verifica que el archivo tenga el formato correcto y las columnas requeridas.")
        
        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {str(e)}")
            st.error("Asegúrate de que el archivo tenga una hoja llamada 'Horas' con el formato correcto.")
    
    else:
        st.info("👆 Por favor, sube un archivo Excel para comenzar el procesamiento de horas.")

def procesar_modulo_asistencia():
    """Módulo para control de asistencia y faltas"""
    st.header("👥 Control de Asistencia y Faltas")
    
    # Configuración de fecha de inicio de semana
    fecha_inicio = st.sidebar.date_input(
        "Fecha de inicio de semana (Lunes)",
        value=datetime.now().date() - timedelta(days=datetime.now().weekday()),
        help="Selecciona el lunes de la semana que quieres analizar"
    )
    
    # Información sobre el formato esperado
    with st.expander("ℹ️ Formato de archivo esperado para asistencia"):
        st.markdown("""
        **El archivo Excel debe contener las siguientes columnas:**
        - `DNI`: Documento de identidad del trabajador
        - `Apellidos y Nombres`: Nombre completo del trabajador
        - `DIA`: Día de la semana (lunes, martes, miércoles, jueves, viernes, sábado, domingo)
        - `HORAS TRABAJ.`: Horas trabajadas en el día (número o 0 para ausencia)
        
        **Procesamiento realizado:**
        - Consolida horas trabajadas por día para cada empleado
        - Marca con "F" los días sin horas trabajadas (faltas)
        - Calcula total de horas semanales por empleado
        - Cuenta el total de faltas por empleado
        - Genera reporte de tramos de faltas consecutivas con fechas
        """)
    
    # Upload file
    uploaded_file = st.file_uploader(
        "📁 Selecciona el archivo Excel con datos de asistencia",
        type=['xlsx', 'xls'],
        help="Sube un archivo Excel con los datos de asistencia",
        key="asistencia_upload"
    )
    
    if uploaded_file is not None:
        try:
            # Read the Excel file
            with st.spinner("📖 Leyendo archivo Excel..."):
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Archivo cargado exitosamente. {len(df)} registros encontrados.")
            
            # Verificar columnas requeridas
            columnas_requeridas = ["DNI", "Apellidos y Nombres", "DIA", "HORAS TRABAJ."]
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                st.error(f"❌ Faltan las siguientes columnas: {', '.join(columnas_faltantes)}")
                st.info("Asegúrate de que el archivo tenga todas las columnas requeridas.")
                return
            
            # Display original data
            st.subheader("📋 Datos originales")
            st.dataframe(df, use_container_width=True)
            
            # Mostrar información básica
            col1, col2, col3 = st.columns(3)
            with col1:
                total_empleados = df["DNI"].nunique()
                st.metric("Total Empleados", total_empleados)
            with col2:
                total_registros = len(df)
                st.metric("Total Registros", total_registros)
            with col3:
                dias_unicos = df["DIA"].nunique()
                st.metric("Días Únicos", dias_unicos)
            
            # Process data
            if st.button("🔄 Procesar control de asistencia", type="primary"):
                with st.spinner("⚙️ Procesando datos de asistencia..."):
                    tareo_final = procesar_tareo(df)
                    
                    if tareo_final is not None:
                        st.success("✅ Datos de asistencia procesados exitosamente!")
                        
                        # Display processed data - Reporte 1
                        st.subheader("📊 Reporte 1: Asistencia Semanal Consolidada")
                        st.dataframe(tareo_final, use_container_width=True)
                        
                        # Summary statistics
                        st.subheader("📈 Resumen de Asistencia")
                        
                        # Estadísticas por empleado
                        empleados_con_faltas = len(tareo_final[tareo_final["Total Faltas"] > 0])
                        empleados_sin_faltas = len(tareo_final[tareo_final["Total Faltas"] == 0])
                        promedio_horas = tareo_final["Total Semanal"].mean()
                        total_faltas_general = tareo_final["Total Faltas"].sum()
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Empleados con Faltas", int(empleados_con_faltas))
                        
                        with col2:
                            st.metric("Empleados sin Faltas", int(empleados_sin_faltas))
                        
                        with col3:
                            st.metric("Promedio Horas/Semana", f"{promedio_horas:.1f}")
                        
                        with col4:
                            st.metric("Total Faltas General", int(total_faltas_general))
                        
                        # Empleados con más faltas
                        if empleados_con_faltas > 0:
                            st.subheader("⚠️ Empleados con Mayor Número de Faltas")
                            top_faltas = tareo_final[tareo_final["Total Faltas"] > 0].nlargest(5, "Total Faltas")[
                                ["Apellidos y Nombres", "DNI", "Total Faltas", "Total Semanal"]
                            ]
                            st.dataframe(top_faltas, use_container_width=True)
                        
                        # Análisis por día
                        st.subheader("📅 Análisis de Faltas por Día")
                        dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado"]
                        faltas_por_dia = {}
                        
                        for dia in dias_semana:
                            if dia in tareo_final.columns:
                                faltas_dia = sum(tareo_final[dia].astype(str).str.upper() == "F")
                                faltas_por_dia[dia.capitalize()] = faltas_dia
                        
                        if faltas_por_dia:
                            col1, col2 = st.columns(2)
                            with col1:
                                for i, (dia, faltas) in enumerate(list(faltas_por_dia.items())[:3]):
                                    st.metric(f"Faltas {dia}", int(faltas))
                            with col2:
                                for i, (dia, faltas) in enumerate(list(faltas_por_dia.items())[3:]):
                                    st.metric(f"Faltas {dia}", int(faltas))
                        
                        # Generar segundo reporte - Tramos de faltas
                        st.subheader("📊 Reporte 2: Tramos de Faltas con Fechas")
                        
                        fecha_inicio_datetime = datetime.combine(fecha_inicio, datetime.min.time())
                        df_tramos = generar_reporte_tramos_faltas(tareo_final, fecha_inicio_datetime)
                        
                        if df_tramos is not None and not df_tramos.empty:
                            st.dataframe(df_tramos, use_container_width=True)
                            
                            # Estadísticas del segundo reporte
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                total_tramos = len(df_tramos)
                                st.metric("Total Tramos de Faltas", total_tramos)
                            with col2:
                                if not df_tramos.empty:
                                    promedio_dias = df_tramos["Cantidad de Días"].mean()
                                    st.metric("Promedio Días por Tramo", f"{promedio_dias:.1f}")
                            with col3:
                                if not df_tramos.empty:
                                    max_dias = int(df_tramos["Cantidad de Días"].max())
                                    st.metric("Máximo Días Consecutivos", max_dias)
                        else:
                            st.info("✅ ¡Excelente! No se encontraron tramos de faltas consecutivas en esta semana.")
                        
                        # Download processed files
                        st.subheader("💾 Descargar Reportes de Asistencia")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Reporte 1: Tareo semanal
                            output1 = io.BytesIO()
                            tareo_final.to_excel(output1, sheet_name='Tareo_Semanal', index=False, engine='openpyxl')
                            excel_data1 = output1.getvalue()
                            
                            st.download_button(
                                label="📥 Reporte 1: Asistencia Semanal",
                                data=excel_data1,
                                file_name="tareo_semanal_consolidado.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                help="Descarga el reporte consolidado de asistencia semanal"
                            )
                        
                        with col2:
                            # Reporte 2: Tramos de faltas
                            if df_tramos is not None and not df_tramos.empty:
                                output2 = io.BytesIO()
                                df_tramos.to_excel(output2, sheet_name='Tramos_Faltas', index=False, engine='openpyxl')
                                excel_data2 = output2.getvalue()
                                
                                st.download_button(
                                    label="📥 Reporte 2: Tramos de Faltas",
                                    data=excel_data2,
                                    file_name="reporte_faltas_semanales_fechas.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    help="Descarga el reporte de tramos de faltas con fechas"
                                )
                            else:
                                st.info("No hay tramos de faltas para descargar")
        
        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {str(e)}")
            st.error("Asegúrate de que el archivo tenga el formato correcto y las columnas requeridas.")
    
    else:
        st.info("👆 Por favor, sube un archivo Excel para comenzar el procesamiento de asistencia.")

def procesar_modulo_integral():
    """Módulo para procesamiento integral que genera los 3 reportes simultáneamente"""
    st.header("🔄 Procesamiento Integral - 3 Reportes Automáticos")
    
    # Configuración de fecha de inicio de semana
    fecha_inicio = st.sidebar.date_input(
        "Fecha de inicio de semana (Lunes)",
        value=datetime.now().date() - timedelta(days=datetime.now().weekday()),
        help="Selecciona el lunes de la semana que quieres analizar"
    )
    
    # Información sobre el formato esperado
    with st.expander("ℹ️ Formato de archivo requerido para procesamiento integral"):
        st.markdown("""
        **El archivo Excel debe contener una hoja llamada 'Horas' con las siguientes columnas:**
        - `DNI`: Documento de identidad del trabajador
        - `Apellidos y Nombres`: Nombre completo del trabajador
        - `DIA`: Día de la semana (lunes, martes, miércoles, jueves, viernes, sábado, domingo)
        - `Hora Inicio Labores`: Hora de inicio en formato HH:MM:SS
        - `Hora Término Labores`: Hora de término en formato HH:MM:SS
        - `Hora Inicio Refrigerio`: (Opcional) Hora de inicio del refrigerio
        - `Hora Término Refrigerio`: (Opcional) Hora de término del refrigerio
        
        **Reportes generados automáticamente:**
        1. **Reporte de Horas Calculadas**: Horas diurnas, nocturnas, extras con recargos
        2. **Reporte de Asistencia Semanal**: Consolidado de faltas por empleado
        3. **Reporte de Tramos de Faltas**: Ausencias consecutivas con fechas
        """)
    
    # Upload file
    uploaded_file = st.file_uploader(
        "📁 Selecciona el archivo Excel para procesamiento integral",
        type=['xlsx', 'xls'],
        help="Sube un archivo Excel que se procesará para generar los 3 reportes",
        key="integral_upload"
    )
    
    if uploaded_file is not None:
        try:
            # Read the Excel file
            with st.spinner("📖 Leyendo archivo Excel..."):
                df = pd.read_excel(uploaded_file, sheet_name="Horas")
            
            st.success(f"✅ Archivo cargado exitosamente. {len(df)} registros encontrados.")
            
            # Verificar columnas requeridas
            columnas_requeridas = ["DNI", "Apellidos y Nombres", "DIA", "Hora Inicio Labores", "Hora Término Labores"]
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                st.error(f"❌ Faltan las siguientes columnas: {', '.join(columnas_faltantes)}")
                st.info("Asegúrate de que el archivo tenga todas las columnas requeridas.")
                return
            
            # Display original data
            st.subheader("📋 Datos originales")
            st.dataframe(df, use_container_width=True)
            
            # Mostrar información básica
            col1, col2, col3 = st.columns(3)
            with col1:
                total_empleados = df["DNI"].nunique()
                st.metric("Total Empleados", total_empleados)
            with col2:
                total_registros = len(df)
                st.metric("Total Registros", total_registros)
            with col3:
                dias_unicos = df["DIA"].nunique()
                st.metric("Días Únicos", dias_unicos)
            
            # Process data
            if st.button("🔄 Generar los 3 reportes automáticamente", type="primary"):
                with st.spinner("⚙️ Procesando datos para generar los 3 reportes..."):
                    try:
                        # ==================== REPORTE 1: HORAS CALCULADAS ====================
                        st.subheader("📊 Reporte 1: Horas Laborales Calculadas")
                        
                        # Procesar horas laborales
                        resultados_horas = df.apply(procesar_fila_horas, axis=1, result_type="expand")
                        df_horas_final = pd.concat([df, resultados_horas], axis=1)
                        
                        # Mostrar columnas calculadas de horas
                        calculated_columns_horas = [
                            "DNI", "Apellidos y Nombres", "DIA",
                            "Horas Diurnas", "Horas Nocturnas", "Horas Normales",
                            "Extra 25%", "Extra 35%", "Extra 25% Nocturna", 
                            "Extra 35% Nocturna", "Total Horas",
                            "Horas Domingo/Feriado", "Horas Extra Domingo/Feriado"
                        ]
                        
                        st.dataframe(df_horas_final[calculated_columns_horas], use_container_width=True)
                        
                        # Métricas de horas
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            total_horas_normales = df_horas_final["Horas Normales"].sum()
                            st.metric("Total Horas Normales", f"{total_horas_normales:.2f}")
                        with col2:
                            total_extra_25 = df_horas_final["Extra 25%"].sum()
                            st.metric("Total Extra 25%", f"{total_extra_25:.2f}")
                        with col3:
                            total_extra_35 = df_horas_final["Extra 35%"].sum()
                            st.metric("Total Extra 35%", f"{total_extra_35:.2f}")
                        with col4:
                            total_horas = df_horas_final["Total Horas"].sum()
                            st.metric("Total Horas", f"{total_horas:.2f}")
                        
                        # ==================== REPORTE 2: ASISTENCIA SEMANAL ====================
                        st.subheader("📊 Reporte 2: Asistencia Semanal Consolidada")
                        
                        # Crear DataFrame para asistencia (usando Total Horas como HORAS TRABAJ.)
                        df_asistencia = df_horas_final[["DNI", "Apellidos y Nombres", "DIA", "Total Horas"]].copy()
                        df_asistencia.rename(columns={"Total Horas": "HORAS TRABAJ."}, inplace=True)
                        
                        tareo_final = procesar_tareo(df_asistencia)
                        
                        if tareo_final is not None:
                            st.dataframe(tareo_final, use_container_width=True)
                            
                            # Métricas de asistencia
                            empleados_con_faltas = len(tareo_final[tareo_final["Total Faltas"] > 0])
                            empleados_sin_faltas = len(tareo_final[tareo_final["Total Faltas"] == 0])
                            promedio_horas_sem = tareo_final["Total Semanal"].mean()
                            total_faltas_general = tareo_final["Total Faltas"].sum()
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Empleados con Faltas", int(empleados_con_faltas))
                            with col2:
                                st.metric("Empleados sin Faltas", int(empleados_sin_faltas))
                            with col3:
                                st.metric("Promedio Horas/Semana", f"{promedio_horas_sem:.1f}")
                            with col4:
                                st.metric("Total Faltas General", int(total_faltas_general))
                        
                            # ==================== REPORTE 3: TRAMOS DE FALTAS ====================
                            st.subheader("📊 Reporte 3: Tramos de Faltas con Fechas")
                            
                            fecha_inicio_datetime = datetime.combine(fecha_inicio, datetime.min.time())
                            df_tramos = generar_reporte_tramos_faltas(tareo_final, fecha_inicio_datetime)
                            
                            if df_tramos is not None and not df_tramos.empty:
                                st.dataframe(df_tramos, use_container_width=True)
                                
                                # Métricas de tramos
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    total_tramos = len(df_tramos)
                                    st.metric("Total Tramos de Faltas", total_tramos)
                                with col2:
                                    promedio_dias = df_tramos["Cantidad de Días"].mean()
                                    st.metric("Promedio Días por Tramo", f"{promedio_dias:.1f}")
                                with col3:
                                    max_dias = int(df_tramos["Cantidad de Días"].max())
                                    st.metric("Máximo Días Consecutivos", max_dias)
                            else:
                                st.info("✅ ¡Excelente! No se encontraron tramos de faltas consecutivas en esta semana.")
                            
                            # ==================== DESCARGA DE LOS 3 REPORTES ====================
                            st.subheader("💾 Descargar los 3 Reportes")
                            
                            st.success("✅ Los 3 reportes han sido generados exitosamente!")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                # Reporte 1: Horas calculadas
                                output1 = io.BytesIO()
                                df_horas_final.to_excel(output1, sheet_name='Horas_Calculadas', index=False, engine='openpyxl')
                                excel_data1 = output1.getvalue()
                                
                                st.download_button(
                                    label="📥 Reporte 1: Horas Calculadas",
                                    data=excel_data1,
                                    file_name="reporte_1_horas_calculadas(C).xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    help="Descarga el reporte de horas laborales con todos los cálculos"
                                )
                            
                            with col2:
                                # Reporte 2: Asistencia semanal
                                output2 = io.BytesIO()
                                tareo_final.to_excel(output2, sheet_name='Asistencia_Semanal', index=False, engine='openpyxl')
                                excel_data2 = output2.getvalue()
                                
                                st.download_button(
                                    label="📥 Reporte 2: Asistencia Semanal",
                                    data=excel_data2,
                                    file_name="reporte_2_asistencia_semanal(C).xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    help="Descarga el reporte consolidado de asistencia"
                                )
                            
                            with col3:
                                # Reporte 3: Tramos de faltas
                                if df_tramos is not None and not df_tramos.empty:
                                    output3 = io.BytesIO()
                                    df_tramos.to_excel(output3, sheet_name='Tramos_Faltas', index=False, engine='openpyxl')
                                    excel_data3 = output3.getvalue()
                                    
                                    st.download_button(
                                        label="📥 Reporte 3: Tramos de Faltas",
                                        data=excel_data3,
                                        file_name="reporte_3_tramos_faltas(C).xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        help="Descarga el reporte de tramos de faltas con fechas"
                                    )
                                else:
                                    st.info("No hay tramos de faltas para descargar")
                            
                            # Resumen final
                            st.markdown("---")
                            st.markdown("### 📋 Resumen del Procesamiento Integral")
                            st.markdown(f"""
                            - **Empleados procesados**: {total_empleados}
                            - **Total de registros**: {total_registros}
                            - **Horas normales calculadas**: {total_horas_normales:.2f}
                            - **Horas extras calculadas**: {(total_extra_25 + total_extra_35):.2f}
                            - **Empleados con faltas**: {empleados_con_faltas}
                            - **Total de tramos de faltas**: {len(df_tramos) if df_tramos is not None and not df_tramos.empty else 0}
                            """)
                        
                    except Exception as e:
                        st.error(f"❌ Error al procesar los datos: {str(e)}")
                        st.error("Verifica que el archivo tenga el formato correcto y las columnas requeridas.")
        
        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {str(e)}")
            st.error("Asegúrate de que el archivo tenga una hoja llamada 'Horas' con el formato correcto.")
    
    else:
        st.info("👆 Por favor, sube un archivo Excel para comenzar el procesamiento integral de los 3 reportes.")

    # Footer
    st.markdown("---")
    st.markdown("📍 **Nota**: Este sistema procesa automáticamente los datos laborales según la legislación peruana, incluyendo cálculo de horas extras, sobretiempos y control de asistencia.")

if __name__ == "__main__":
    main()
