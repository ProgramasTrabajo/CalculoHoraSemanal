# Sistema Integral de Gestión Laboral

Una aplicación web completa desarrollada con Streamlit para la gestión integral de recursos humanos, que combina el procesamiento de horas laborales y el control de asistencia en una sola plataforma.

## Características

### 📈 Módulo de Procesamiento de Horas Laborales
- **Cálculos automáticos de horas**: Procesa horarios de trabajo complejos
- **Clasificación de horarios**:
  - Horas diurnas (06:00-22:00) y nocturnas (22:00-06:00)
  - Horas normales (hasta 8 horas) y extras
  - Sobretiempo con recargo del 25% y 35%
  - Tratamiento especial para domingos y feriados
  - Descuento automático de refrigerio (13:00-14:00)
- **Cumplimiento legal**: Cálculos según legislación laboral peruana

### 👥 Módulo de Control de Asistencia y Faltas
- **Configuración de fechas**: Selecciona período de análisis semanal
- **Consolidación automática**:
  - Agrupa horas trabajadas por empleado y día
  - Marca automáticamente faltas (F) en días sin registro
  - Calcula totales semanales por empleado
- **Doble sistema de reportes**:
  - **Reporte 1**: Asistencia semanal consolidada
  - **Reporte 2**: Tramos de faltas consecutivas con fechas reales
- **Análisis avanzado**:
  - Empleados con mayor ausentismo
  - Patrones de faltas por día de la semana
  - Métricas de tramos consecutivos

### 🔄 Módulo de Procesamiento Integral (NUEVO)
- **Procesamiento automático completo**: Genera los 3 reportes en una sola ejecución
- **Triple reporte simultáneo**:
  - **Reporte 1**: Horas laborales calculadas con recargos
  - **Reporte 2**: Asistencia semanal consolidada con faltas
  - **Reporte 3**: Tramos de faltas consecutivas con fechas
- **Optimización de flujo**: Un solo archivo de entrada para todos los análisis
- **Descarga múltiple**: Los 3 reportes listos para descarga individual

### 🎯 Funcionalidades Generales
- **Interfaz unificada**: Selector de módulos en sidebar
- **Carga flexible**: Soporte para diferentes formatos Excel
- **Exportación múltiple**: Descarga de reportes en archivos Excel separados
- **Validación robusta**: Verificación de columnas y formatos
- **Feedback en tiempo real**: Métricas y estadísticas instantáneas

## Formatos de archivo requeridos

### Para Procesamiento de Horas
El archivo Excel debe contener una hoja llamada "Horas" con:
- `DIA`: Día de la semana (lunes, martes, miércoles, jueves, viernes, sábado, domingo)
- `Hora Inicio Labores`: Hora de inicio en formato HH:MM:SS
- `Hora Término Labores`: Hora de término en formato HH:MM:SS
- `Hora Inicio Refrigerio`: (Opcional) Hora de inicio del refrigerio
- `Hora Término Refrigerio`: (Opcional) Hora de término del refrigerio

### Para Control de Asistencia
El archivo Excel debe contener:
- `DNI`: Documento de identidad del trabajador
- `Apellidos y Nombres`: Nombre completo del trabajador
- `DIA`: Día de la semana
- `HORAS TRABAJ.`: Horas trabajadas en el día (número o 0 para ausencia)

## Reportes generados

### Módulo de Horas Laborales
- **Reporte único**: Horas calculadas con clasificación completa
  - Horas diurnas, nocturnas, normales, extras
  - Recargos por sobretiempo (25% y 35%)
  - Diferenciación nocturna y feriados
  - Totales consolidados

### Módulo de Asistencia
- **Reporte 1 - Tareo Semanal**: 
  - Empleados organizados por DNI y nombre
  - Horas trabajadas por día de la semana
  - Faltas marcadas como "F"
  - Totales semanales y conteo de faltas

- **Reporte 2 - Tramos de Faltas**:
  - DNI y nombre del empleado
  - Fecha inicial y final de cada tramo
  - Cantidad de días consecutivos
  - Solo incluye ausencias consecutivas

## Instalación local

1. Clona este repositorio
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta la aplicación:
   ```bash
   streamlit run app.py
   ```

## Despliegue en Streamlit Cloud

1. Haz fork de este repositorio
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu repositorio de GitHub
4. Selecciona `app.py` como archivo principal
5. Haz clic en "Deploy"

## Estructura del proyecto

```
├── app.py                    # Aplicación principal unificada
├── .streamlit/
│   └── config.toml          # Configuración de Streamlit
├── requirements.txt         # Dependencias Python
└── README.md               # Este archivo
```

## Casos de uso

### Para Departamentos de RRHH
- Procesamiento masivo de planillas horarias
- Control de asistencia semanal/mensual
- Identificación de patrones de ausentismo
- Cálculo automático de horas extras y recargos

### Para Supervisores
- Monitoreo de asistencia de equipos
- Análisis de productividad por empleado
- Detección temprana de problemas de ausentismo

### Para Administración
- Reportes consolidados para nómina
- Cumplimiento de normativas laborales
- Análisis de costos de horas extras
- Documentación para auditorías

## Ventajas del sistema unificado

1. **Eficiencia**: Dos módulos especializados en una sola aplicación
2. **Consistencia**: Interfaz uniforme para ambos procesos
3. **Flexibilidad**: Procesamiento independiente según necesidades
4. **Escalabilidad**: Fácil expansión con nuevos módulos
5. **Mantenimiento**: Un solo punto de actualización y despliegue

## Tecnologías utilizadas

- **Streamlit**: Framework web para aplicaciones de datos
- **Pandas**: Procesamiento de datos y archivos Excel
- **OpenPyXL**: Lectura y escritura de archivos Excel
- **Python DateTime**: Cálculos de tiempo y fechas avanzados