"""Genera notas del presentador (slide-by-slide) en PDF.

Mapea cada una de las 16 diapositivas de presentacion_HHI a su(s) seccion(es) del guion.
Usa fpdf2 con fuentes Arial de Windows para soporte Unicode.
"""
from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "presentacion" / "notas_presentador.pdf"

FONT_REG = "C:/Windows/Fonts/arial.ttf"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT_ITAL = "C:/Windows/Fonts/ariali.ttf"

NOTES = [
    {
        "n": 1,
        "titulo": "Portada",
        "speaker": "P1",
        "duracion": "0:30",
        "objetivo": "Presentar el proyecto, el equipo y enmarcar la sesion.",
        "bloques": [
            ("P1", "Buenos dias. Somos parte del Consultorio de Estadistica de la Universidad Santo Tomas, en el marco del Observatorio Ustadistica. Hoy les presentamos el proyecto Sinergia socioeconomica, que analiza la concentracion de la contratacion publica en Colombia entre 2018 y 2026, articulando datos abiertos de Colombia Compra Eficiente con informacion social y demografica del DANE."),
        ],
        "transicion": "Pasamos a P2 con la pregunta central.",
    },
    {
        "n": 2,
        "titulo": "Pregunta central",
        "speaker": "P2",
        "duracion": "0:30",
        "objetivo": "Plantear el problema y el indicador a usar.",
        "bloques": [
            ("P2", "La pregunta es muy concreta: cuando el Estado contrata, el valor que paga se reparte entre muchos proveedores o se concentra en pocos? Esa pregunta tiene implicaciones en competencia, eficiencia del gasto y riesgo de captura de rentas. Para responderla usamos el Indice Herfindahl-Hirschman, conocido como HHI, un estandar internacional para medir concentracion de mercado."),
            ("P2", "Antes de ver el indicador necesitan entender de donde vienen los datos."),
        ],
        "transicion": "P1 introduce las fuentes de datos.",
    },
    {
        "n": 3,
        "titulo": "Las cinco fuentes",
        "speaker": "P1",
        "duracion": "2:00",
        "objetivo": "Listar las cinco fuentes oficiales y su rol en el HHI.",
        "bloques": [
            ("P1", "Usamos cinco fuentes oficiales, todas con descarga publica. SECOP I (f789-7hwg) y SECOP II (jbjy-vk9h) son las protagonistas: 6.3 y 5.6 millones de filas respectivamente, periodo 2018-2026, contratos del Estado con su monto, fecha, municipio y NIT del contratista."),
            ("P1", "El CNPV 2018 (DANE, catalogo 643) nos da los 1,122 municipios y la poblacion base. EMICRON (catalogo 875) caracteriza la economia popular a nivel departamental. Y las proyecciones DANE 2018-2050 alimentan los indicadores per capita."),
            ("P2", "Aclaracion clave: el HHI se calcula 100% con SECOP. CNPV, EMICRON y proyecciones son contextuales: enriquecen la interpretacion pero no entran en la formula."),
        ],
        "transicion": "Con las fuentes claras, P1 explica como las integramos.",
    },
    {
        "n": 4,
        "titulo": "Arquitectura Medallion",
        "speaker": "P1",
        "duracion": "1:30",
        "objetivo": "Explicar las tres capas Bronce-Plata-Oro.",
        "bloques": [
            ("P1", "Las cinco bases vienen en formatos, codificaciones y granularidades distintas. Las homogenizamos con una arquitectura Medallion de tres capas."),
            ("P1", "Bronce: ingesta cruda. Convertimos los CSV oficiales a Parquet (columnar, comprimido) sin transformar el contenido. Trazabilidad total: cuando se ingesto, fuente, version, hash."),
            ("P1", "Plata: limpieza. Tres tareas criticas: (1) tipificacion de montos (texto a numero), (2) estandarizacion del DIVIPOLA -nuestra llave de cruce- mapeando nombres a codigos con catalogo de 1,102 municipios, (3) deduplicacion entre SECOP I y II."),
            ("P1", "Oro: modelo dimensional. Dos dimensiones (tiempo y territorio) y cuatro tablas de hechos. La tabla analitica final (mart) tiene 13,860 filas."),
        ],
        "transicion": "Detalle del modelo dimensional en la siguiente diapositiva.",
    },
    {
        "n": 5,
        "titulo": "Modelo dimensional (Oro)",
        "speaker": "P1",
        "duracion": "1:00",
        "objetivo": "Mostrar dimensiones y hechos que conforman el mart.",
        "bloques": [
            ("P1", "Dimensiones: dim_tiempo (una fila por anio 2018-2029 con atributos como anio electoral o pandemia) y dim_territorio (una fila por DIVIPOLA con municipio, departamento, region)."),
            ("P1", "Hechos: fact_contratacion_municipio_anio (union deduplicada SECOP I+II), fact_censo_municipio (CNPV propagado), fact_micronegocios_municipio_anio (EMICRON expandido) y fact_demografia_municipio_anio (proyecciones DANE)."),
            ("P2", "Todos se integran en el mart: 13,860 filas, 1,155 DIVIPOLA, 2018-2029. Es la tabla que consume el dashboard."),
        ],
        "transicion": "P1 cierra con los KPIs del pipeline.",
    },
    {
        "n": 6,
        "titulo": "KPIs del pipeline",
        "speaker": "P1",
        "duracion": "1:00",
        "objetivo": "Resumir el volumen procesado en cada capa.",
        "bloques": [
            ("P1", "Volumen procesado: Bronce SECOP I 6.35 millones; Bronce SECOP II 5.60 millones; Bronce CNPV personas 44.16 millones. Plata SECOP I queda en 5.45 millones, SECOP II en 4.03 millones tras descartar DIVIPOLA invalido, montos cero o anios fuera de rango."),
            ("P1", "Oro: mart 13,860 filas; tabla maestra HHI 11,792 mercados."),
            ("P1", "Tres beneficios practicos: trazabilidad (cada numero rastreable al contrato), reproducibilidad (python -m src.cli all regenera todo) y separacion de responsabilidades."),
        ],
        "transicion": "P2 toma el turno para explicar el HHI.",
    },
    {
        "n": 7,
        "titulo": "Que es el HHI?",
        "speaker": "P2",
        "duracion": "1:30",
        "objetivo": "Definir el indicador y las bandas de interpretacion.",
        "bloques": [
            ("P2", "El HHI es el estandar internacional de concentracion de mercado. Lo usan las autoridades de competencia en Estados Unidos, la Union Europea y muchos otros paises para evaluar fusiones, por ejemplo."),
            ("P2", "Formula simple: en un mercado, calculamos la participacion porcentual de cada actor, la elevamos al cuadrado y sumamos. Escala 0 a 10,000."),
            ("P2", "Bandas: menor a 1,500 concentracion baja; 1,500 a 2,500 moderada; mayor o igual a 2,500 alta. 10,000 es monopolio puro."),
            ("P1", "Nuestra unidad de analisis es un mercado: municipio x anio x orden de entidad. Calculamos HHI para 11,792 mercados entre 2018 y 2026, usando NIT como identificador de proveedor."),
        ],
        "transicion": "Pasamos a los resultados con datos reales.",
    },
    {
        "n": 8,
        "titulo": "Tendencia anual nacional",
        "speaker": "P2",
        "duracion": "1:00",
        "objetivo": "Mostrar la evolucion 2018-2026 del HHI promedio.",
        "bloques": [
            ("P2", "Evolucion: 2018 HHI 1,221.87 (mediana 669). 2020 baja a 1,040.57 -el minimo- coincide con pandemia: mas contratos pequenios de emergencia. 2023 sube a 1,483.89; 2025 alcanza 1,484.07; 2026 1,422.50 con corte a mayo."),
            ("P1", "Todos los valores estan en banda baja a moderada. La contratacion publica colombiana, en su conjunto, no presenta monopolizacion generalizada. Pero el promedio esconde matices."),
        ],
        "transicion": "Esos matices aparecen al separar por orden de entidad.",
    },
    {
        "n": 9,
        "titulo": "Nacional vs Territorial",
        "speaker": "P2",
        "duracion": "1:30",
        "objetivo": "Evidenciar que el orden nacional concentra mas.",
        "bloques": [
            ("P2", "Diferencia consistente y muy importante: 2018 nacional 2,145.84 vs territorial 1,047.54. 2025 nacional 2,809.30 vs territorial 1,147.46. 2026 nacional 2,189.69 vs territorial 1,237.99. El nacional siempre concentra mas y a veces casi triplica al territorial."),
            ("P1", "Razon estructural: orden nacional incluye ministerios, agencias, Invias, ICBF, Fuerzas Militares -entidades grandes con pocos contratos de gran magnitud y proveedores especializados-. El territorial son alcaldias, hospitales municipales, instituciones educativas: mas contratos, mas fragmentados, con mayor pluralidad de proveedores locales."),
            ("P2", "Implicacion: cualquier diagnostico de competencia tiene que separar los dos ordenes. Mezclarlos esconde el problema."),
        ],
        "transicion": "Veamos la distribucion completa de los 11,792 mercados.",
    },
    {
        "n": 10,
        "titulo": "Distribucion del HHI",
        "speaker": "P2",
        "duracion": "0:45",
        "objetivo": "Visualizar como se reparten los 11,792 mercados.",
        "bloques": [
            ("P2", "La distribucion es asimetrica: gran parte de los mercados estan en concentracion baja, lo que explica que la mediana sea bastante mas baja que el promedio. La cola derecha incluye los mercados con HHI alto -focos puntuales que merecen revision-."),
            ("P2", "Esta forma confirma el patron: la concentracion alta no es generalizada, es localizada."),
        ],
        "transicion": "Veamos donde se localiza esa cola alta.",
    },
    {
        "n": 11,
        "titulo": "Top departamentos por HHI",
        "speaker": "P2",
        "duracion": "1:30",
        "objetivo": "Identificar los focos territoriales en 2026.",
        "bloques": [
            ("P2", "Top 5 con mayor HHI promedio 2026: Atlantico 2,824.15 (31 mercados), Choco 2,695.77 (19), Magdalena 2,053.98 (34), La Guajira 1,885.03 (20), Boyaca 1,816.14 (143). Del otro lado: Guainia 495, Quindio 518, Amazonas 629."),
            ("P1", "Prudencia en la lectura: Atlantico, Choco, Magdalena en la parte alta no implican automaticamente irregularidad. Puede haber explicaciones estructurales: pocos proveedores con capacidad tecnica para ciertas obras, o contratos grandes que dominan el agregado. El HHI sirve para identificar donde mirar, no para concluir directamente."),
        ],
        "transicion": "Otro dato que llama la atencion: los HHI = 10,000.",
    },
    {
        "n": 12,
        "titulo": "Los 186 mercados con HHI = 10,000",
        "speaker": "P2",
        "duracion": "1:00",
        "objetivo": "Aclarar que el HHI maximo no implica cientos de monopolios.",
        "bloques": [
            ("P2", "De los 11,792 mercados, solo 186 alcanzan HHI = 10,000. Eso es 1.58%, menos del 2%."),
            ("P2", "De esos 186: 167 tienen exactamente un contrato y un proveedor -la unica participacion es 100% y el HHI da 10,000 por construccion, no es informativo-. 19 son monopolios reales: varios contratos pero todos al mismo NIT. Cero tienen mas de un proveedor con HHI = 10,000, lo que confirma que la formula esta bien implementada."),
            ("P1", "Los monopolios reales son apenas 19 casos en nueve anios. La aparicion del HHI maximo no es un error de calculo ni de ingesta, es la consecuencia natural de mercados muy pequenios. Esos casos los marcamos para revision cualitativa, no como alarma automatica."),
        ],
        "transicion": "Una limitacion estructural antes del cierre: el sesgo Bogota.",
    },
    {
        "n": 13,
        "titulo": "El sesgo de sede vs ejecucion",
        "speaker": "P2",
        "duracion": "1:00",
        "objetivo": "Explicar por que Bogota concentra entre 34% y 55% del monto.",
        "bloques": [
            ("P2", "El municipio que registramos en SECOP es el de la entidad contratante, no el del lugar de ejecucion del contrato. Por eso Bogota concentra entre 34% y 55% del monto anual: muchas entidades nacionales tienen sede en Bogota aunque ejecuten contratos en todo el pais."),
            ("P2", "Particion anual: 2018 50.2%, 2019 42.6%, 2020 41.2%, 2021 47.2%, 2022 54.3%, 2023 38.0%, 2024 34.1%."),
            ("P1", "Mitigamos el sesgo segmentando por orden de entidad, pero la advertencia siempre debe ir explicita en la lectura de los numeros."),
        ],
        "transicion": "Pasamos a los hallazgos clave.",
    },
    {
        "n": 14,
        "titulo": "Hallazgos clave",
        "speaker": "P1",
        "duracion": "1:00",
        "objetivo": "Sintetizar los cuatro hallazgos del proyecto.",
        "bloques": [
            ("P1", "Cuatro hallazgos. Primero: la concentracion promedio entre 2018 y 2026 se mantiene en banda baja a moderada, HHI entre 1,040 y 1,484."),
            ("P1", "Segundo: el orden nacional concentra sistematicamente mas que el territorial, hasta casi tres veces. Cualquier analisis serio debe separar los dos ordenes."),
            ("P1", "Tercero: existen focos territoriales -Atlantico, Choco, Magdalena, La Guajira- con HHI departamental superior a 1,800 en 2026 que ameritan analisis caso a caso."),
            ("P1", "Cuarto: los mercados con HHI = 10,000 son apenas 1.58%, en su mayoria artefactos de mercados pequenios, no monopolios estructurales."),
        ],
        "transicion": "P2 cierra con las limitaciones.",
    },
    {
        "n": 15,
        "titulo": "Limitaciones",
        "speaker": "P2",
        "duracion": "1:00",
        "objetivo": "Comunicar tres limitaciones que el publico debe conocer.",
        "bloques": [
            ("P2", "Primera: el municipio registrado es el de la entidad contratante, no el de ejecucion (sesgo Bogota ya explicado)."),
            ("P2", "Segunda: el HHI mide concentracion del valor adjudicado, no calidad de la competencia. No sabemos cuantos oferentes hubo en cada proceso ni si la convocatoria fue plural."),
            ("P1", "Tercera: las fuentes con secreto estadistico (CNPV, EMICRON) no se pueden cruzar a nivel persona con SECOP. Trabajamos siempre con agregaciones territoriales por mandato de la Ley 79 de 1993. Es restriccion legal, no tecnica."),
        ],
        "transicion": "Cerramos en conjunto.",
    },
    {
        "n": 16,
        "titulo": "Cierre y preguntas",
        "speaker": "P1 + P2",
        "duracion": "1:00",
        "objetivo": "Resumir el alcance del proyecto y abrir preguntas.",
        "bloques": [
            ("P1", "En sintesis: cinco fuentes oficiales integradas en arquitectura reproducible de tres capas, modelo dimensional con dos dimensiones y cuatro hechos, indicador HHI aplicado a 11,792 mercados colombianos entre 2018 y 2026."),
            ("P2", "El HHI nos permite afirmar con datos que la contratacion publica nacional no esta monopolizada en terminos generales, que el orden nacional concentra mas que el territorial, y que hay focos puntuales que merecen revision. Productos: informe estadistico, dashboard interactivo, infografia, presentacion y base de datos con diccionario."),
            ("P1", "Todo el repositorio esta versionado, documentado y es reproducible. Gracias por su atencion. Quedamos atentos a sus preguntas."),
        ],
        "transicion": "",
    },
]


# ---------------------------- PDF ----------------------------

PRIMARY = (32, 64, 130)       # azul USTA
ACCENT = (224, 168, 0)        # amarillo
DARK = (31, 41, 55)           # texto
MUTED = (108, 117, 125)       # secundario
LIGHT_BG = (245, 247, 250)    # fondo bloques


class NotasPDF(FPDF):
    def __init__(self) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.add_font("Arial", "", FONT_REG, uni=True)
        self.add_font("Arial", "B", FONT_BOLD, uni=True)
        self.add_font("Arial", "I", FONT_ITAL, uni=True)
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(left=18, top=18, right=18)

    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("Arial", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, "Notas del presentador  -  Sinergia socioeconomica (HHI)", ln=1, align="L")
        self.ln(2)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Arial", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, f"Pagina {self.page_no()}", align="C")

    # ------------- portada -------------
    def cover(self) -> None:
        self.add_page()
        self.set_fill_color(*PRIMARY)
        self.rect(0, 0, 210, 60, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 22)
        self.set_xy(18, 22)
        self.multi_cell(174, 9, "Notas del presentador")
        self.set_font("Arial", "", 12)
        self.set_xy(18, 44)
        self.cell(174, 6, "Presentacion HHI - Sinergia socioeconomica", ln=1)

        self.set_text_color(*DARK)
        self.set_font("Arial", "", 11)
        self.set_xy(18, 75)
        self.multi_cell(174, 6, "Documento complementario al deck presentacion_HHI.pdf. Para cada una de las 16 diapositivas se indica: ponente sugerido, duracion estimada, objetivo, bloques de discurso (versiones cortas del guion oficial) y transicion hacia la siguiente diapositiva.")

        self.set_xy(18, 110)
        self.set_font("Arial", "B", 11)
        self.set_text_color(*PRIMARY)
        self.cell(0, 6, "Como usar este documento", ln=1)
        self.set_text_color(*DARK)
        self.set_font("Arial", "", 10.5)
        self.ln(1)
        bullets = [
            "Cada bloque empieza con el ponente (P1 o P2). Mantengan los turnos para preservar el ritmo.",
            "Las cifras estan validadas contra INFORME_HHI_DETALLADO.md - no improvisen numeros.",
            "Si una diapositiva se extiende, recorten primero los ejemplos, nunca el cierre conjunto.",
            "Duracion total objetivo: 12-15 minutos (incluyendo cierre y respiros).",
        ]
        for b in bullets:
            self.cell(4)
            self.cell(3, 6, "-", ln=0)
            self.multi_cell(167, 6, b)

        self.set_xy(18, 165)
        self.set_font("Arial", "B", 11)
        self.set_text_color(*PRIMARY)
        self.cell(0, 6, "Distribucion de roles", ln=1)
        self.set_text_color(*DARK)
        self.set_font("Arial", "", 10.5)
        self.ln(1)
        self.cell(4)
        self.cell(3, 6, "-", ln=0)
        self.multi_cell(167, 6, "P1 abre, presenta el problema, las fuentes de datos, el modelo dimensional y los hallazgos.")
        self.cell(4)
        self.cell(3, 6, "-", ln=0)
        self.multi_cell(167, 6, "P2 desarrolla el indicador HHI, los resultados con datos reales, las limitaciones y co-cierra.")

        self.set_xy(18, 230)
        self.set_font("Arial", "I", 9)
        self.set_text_color(*MUTED)
        self.multi_cell(174, 5, "Consultorio de Estadistica USTA - Observatorio Ustadistica 2026-I.")

    # ------------- slide note -------------
    def slide_note(self, item: dict) -> None:
        self.add_page()

        # Banda superior
        self.set_fill_color(*PRIMARY)
        self.rect(0, 0, 210, 22, "F")
        self.set_fill_color(*ACCENT)
        self.rect(0, 22, 210, 1.6, "F")

        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 11)
        self.set_xy(18, 7)
        self.cell(0, 5, f"DIAPOSITIVA {item['n']:02d} / 16", ln=1)
        self.set_font("Arial", "B", 14)
        self.set_xy(18, 12)
        self.cell(0, 7, item["titulo"], ln=1)

        # Meta box
        self.set_y(32)
        self.set_fill_color(*LIGHT_BG)
        self.set_text_color(*DARK)
        self.set_font("Arial", "B", 9.5)
        self.set_x(18)
        self.cell(28, 8, "  Ponente", fill=True)
        self.cell(46, 8, "  Duracion", fill=True)
        self.cell(100, 8, "  Objetivo", fill=True, ln=1)
        self.set_font("Arial", "", 9.5)
        self.set_x(18)
        self.cell(28, 8, f"  {item['speaker']}")
        self.cell(46, 8, f"  {item['duracion']} min")
        # truncate objetivo if too long
        obj = item["objetivo"]
        # Use multi_cell-like by manual width-aware split for safety
        self.cell(100, 8, f"  {obj}", ln=1)

        # Bloques de discurso
        self.ln(4)
        self.set_font("Arial", "B", 10.5)
        self.set_text_color(*PRIMARY)
        self.cell(0, 6, "Discurso (versiones de bolsillo)", ln=1)
        self.ln(1)

        for ponente, texto in item["bloques"]:
            # etiqueta del ponente
            self.set_font("Arial", "B", 10)
            self.set_text_color(*ACCENT if ponente == "P2" else PRIMARY)
            self.cell(12, 6, ponente)
            # texto
            self.set_font("Arial", "", 10.5)
            self.set_text_color(*DARK)
            self.multi_cell(162, 5.5, texto)
            self.ln(1)

        # Transicion
        if item["transicion"]:
            self.ln(2)
            self.set_draw_color(*ACCENT)
            self.set_line_width(0.4)
            y = self.get_y()
            self.line(18, y, 192, y)
            self.ln(2)
            self.set_font("Arial", "B", 9.5)
            self.set_text_color(*PRIMARY)
            self.cell(28, 6, "Transicion:")
            self.set_font("Arial", "I", 10)
            self.set_text_color(*DARK)
            self.multi_cell(146, 6, item["transicion"])


def main() -> None:
    pdf = NotasPDF()
    pdf.cover()
    for item in NOTES:
        pdf.slide_note(item)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT))
    print(f"OK -> {OUT}")


if __name__ == "__main__":
    main()
