"""Convierte el guion de exposicion en Markdown a un PDF formateado.

Usa fpdf2 con la fuente DejaVu (Unicode) para soporte de tildes y caracteres
especiales del espanol.
"""

from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts" / "presentacion" / "guion_exposicion.md"
OUTPUT = ROOT / "artifacts" / "presentacion" / "guion_exposicion.pdf"


COLOR_TITLE = (31, 41, 55)        # gris oscuro
COLOR_H2 = (78, 121, 167)         # azul corporativo
COLOR_H3 = (90, 90, 90)           # gris medio
COLOR_ACCENT = (196, 61, 61)      # rojo para P1/P2
COLOR_TEXT = (33, 37, 41)
COLOR_RULE = (210, 210, 210)
COLOR_TABLE_HEADER_BG = (235, 238, 242)


class GuionPDF(FPDF):
    def __init__(self) -> None:
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(left=18, top=18, right=18)

    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_y(8)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(
            0, 5,
            "Guion de exposicion - Sinergia socioeconomica HHI - USTA 2026-I",
            align="L",
        )
        self.ln(6)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f"Pagina {self.page_no()}", align="C")


def register_fonts(pdf: FPDF) -> None:
    """Carga Arial del sistema para soporte Unicode."""
    fonts_dir = Path("C:/Windows/Fonts")
    pdf.add_font("DejaVu", "", str(fonts_dir / "arial.ttf"))
    pdf.add_font("DejaVu", "B", str(fonts_dir / "arialbd.ttf"))
    pdf.add_font("DejaVu", "I", str(fonts_dir / "ariali.ttf"))
    pdf.add_font("DejaVu", "BI", str(fonts_dir / "arialbi.ttf"))


def render_inline(pdf: FPDF, text: str, size: float = 11) -> None:
    """Renderiza una linea con soporte para **bold**, *italic*, `code` y resaltado P1/P2."""
    # Procesa segmentos por bold ** y backtick `
    tokens = re.split(r"(\*\*[^\*]+\*\*|`[^`]+`)", text)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**"):
            content = tok[2:-2]
            pdf.set_font("DejaVu", "B", size)
            # Resaltar P1: / P2: en color
            if content in ("P1:", "P2:"):
                pdf.set_text_color(*COLOR_ACCENT)
                pdf.write(size * 0.45, content + " ")
                pdf.set_text_color(*COLOR_TEXT)
            else:
                pdf.write(size * 0.45, content)
            pdf.set_font("DejaVu", "", size)
        elif tok.startswith("`") and tok.endswith("`"):
            content = tok[1:-1]
            pdf.set_font("Courier", "", size - 1)
            pdf.write(size * 0.45, content)
            pdf.set_font("DejaVu", "", size)
        else:
            pdf.set_font("DejaVu", "", size)
            pdf.write(size * 0.45, tok)


def render_paragraph(pdf: FPDF, text: str) -> None:
    pdf.set_text_color(*COLOR_TEXT)
    render_inline(pdf, text, size=10.5)
    pdf.ln(6)


def render_bullet(pdf: FPDF, text: str) -> None:
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font("DejaVu", "", 10.5)
    pdf.set_x(pdf.l_margin + 4)
    pdf.cell(4, 5, chr(8226))  # bullet
    render_inline(pdf, text, size=10.5)
    pdf.ln(5.5)


def render_h1(pdf: FPDF, text: str) -> None:
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font("DejaVu", "B", 20)
    pdf.multi_cell(0, 10, text)
    pdf.ln(2)


def render_h2(pdf: FPDF, text: str) -> None:
    if pdf.get_y() > 240:
        pdf.add_page()
    pdf.ln(2)
    pdf.set_text_color(*COLOR_H2)
    pdf.set_font("DejaVu", "B", 14)
    pdf.multi_cell(0, 7.5, text)
    # Linea bajo el h2
    pdf.set_draw_color(*COLOR_H2)
    pdf.set_line_width(0.3)
    y = pdf.get_y()
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.ln(3)


def render_h3(pdf: FPDF, text: str) -> None:
    if pdf.get_y() > 245:
        pdf.add_page()
    pdf.ln(1)
    pdf.set_text_color(*COLOR_H3)
    pdf.set_font("DejaVu", "B", 11.5)
    pdf.multi_cell(0, 6, text)
    pdf.ln(1)


def render_hr(pdf: FPDF) -> None:
    pdf.ln(2)
    pdf.set_draw_color(*COLOR_RULE)
    pdf.set_line_width(0.2)
    y = pdf.get_y()
    pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
    pdf.ln(4)


def parse_table(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    """Lee una tabla markdown desde lines[start]. Retorna (filas, nueva_pos)."""
    rows: list[list[str]] = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        line = lines[i].strip()
        # saltar la fila separadora ---
        if re.match(r"^\|[\s\-:|]+\|?\s*$", line):
            i += 1
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
        i += 1
    return rows, i


def render_table(pdf: FPDF, rows: list[list[str]]) -> None:
    if not rows:
        return
    if pdf.get_y() > 230:
        pdf.add_page()
    n_cols = len(rows[0])
    avail_width = pdf.w - pdf.l_margin - pdf.r_margin
    col_w = avail_width / n_cols
    pdf.ln(1)
    pdf.set_font("DejaVu", "B", 9)

    # Header
    pdf.set_fill_color(*COLOR_TABLE_HEADER_BG)
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_draw_color(180, 180, 180)
    for cell in rows[0]:
        clean = cell.replace("**", "").replace("`", "")
        pdf.cell(col_w, 7, clean, border=1, align="L", fill=True)
    pdf.ln(7)

    # Body
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(*COLOR_TEXT)
    for row in rows[1:]:
        if pdf.get_y() > 270:
            pdf.add_page()
            pdf.set_font("DejaVu", "B", 9)
            pdf.set_fill_color(*COLOR_TABLE_HEADER_BG)
            pdf.set_text_color(*COLOR_TITLE)
            for cell in rows[0]:
                clean = cell.replace("**", "").replace("`", "")
                pdf.cell(col_w, 7, clean, border=1, align="L", fill=True)
            pdf.ln(7)
            pdf.set_font("DejaVu", "", 9)
            pdf.set_text_color(*COLOR_TEXT)

        for cell in row:
            # Detecta alineacion derecha si es numerico
            clean = cell.replace("**", "")
            is_num = bool(re.match(r"^[\d,.\-:%\(\) ]+$", clean.replace(" ", "")))
            align = "R" if is_num and clean else "L"
            pdf.cell(col_w, 6, clean[:60], border=1, align=align)
        pdf.ln(6)
    pdf.ln(2)


def render_markdown(pdf: FPDF, md_text: str) -> None:
    lines = md_text.splitlines()
    i = 0
    in_first_section = True
    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()

        # Saltos de linea en blanco -> mini espaciado
        if not line.strip():
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^---+\s*$", line):
            render_hr(pdf)
            i += 1
            continue

        # Tablas
        if line.lstrip().startswith("|"):
            rows, new_i = parse_table(lines, i)
            render_table(pdf, rows)
            i = new_i
            continue

        # Headers
        if line.startswith("# "):
            if not in_first_section:
                pdf.add_page()
            render_h1(pdf, line[2:].strip())
            in_first_section = False
            i += 1
            continue
        if line.startswith("## "):
            render_h2(pdf, line[3:].strip())
            i += 1
            continue
        if line.startswith("### "):
            render_h3(pdf, line[4:].strip())
            i += 1
            continue
        if line.startswith("#### "):
            render_h3(pdf, line[5:].strip())
            i += 1
            continue

        # Bullets
        if line.lstrip().startswith("- "):
            render_bullet(pdf, line.lstrip()[2:].strip())
            i += 1
            continue

        # Numerados
        m = re.match(r"^\s*(\d+)\.\s+(.*)", line)
        if m:
            text = f"{m.group(1)}. {m.group(2)}"
            pdf.set_text_color(*COLOR_TEXT)
            pdf.set_x(pdf.l_margin + 4)
            render_inline(pdf, text, size=10.5)
            pdf.ln(5.5)
            i += 1
            continue

        # Parrafo normal
        render_paragraph(pdf, line.strip())
        i += 1


def render_cover(pdf: FPDF) -> None:
    pdf.add_page()
    pdf.set_fill_color(78, 121, 167)
    pdf.rect(0, 0, pdf.w, 65, style="F")

    pdf.set_text_color(255, 255, 255)
    pdf.set_y(22)
    pdf.set_font("DejaVu", "B", 22)
    pdf.multi_cell(0, 10, "Guion de exposicion")

    pdf.set_font("DejaVu", "", 13)
    pdf.set_y(38)
    pdf.multi_cell(
        0, 6.5,
        "Concentracion de la contratacion publica en Colombia\n"
        "Indice Herfindahl-Hirschman (HHI) - SECOP I + II",
    )

    pdf.set_y(75)
    pdf.set_text_color(33, 37, 41)
    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 6, "Proyecto:")
    pdf.ln(6)
    pdf.set_font("DejaVu", "", 11)
    pdf.multi_cell(0, 6, "Sinergia socioeconomica: contratacion publica, estructura territorial y economia popular")
    pdf.ln(2)

    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 6, "Equipo:")
    pdf.ln(6)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 6, "Consultorio de Estadistica USTA - Observatorio Ustadistica 2026-I")
    pdf.ln(8)

    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 6, "Modalidad:")
    pdf.ln(6)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 6, "Exposicion para dos presentadores")
    pdf.ln(8)

    pdf.set_font("DejaVu", "B", 11)
    pdf.cell(0, 6, "Duracion estimada:")
    pdf.ln(6)
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 6, "12 a 15 minutos")
    pdf.ln(10)

    # Indice
    pdf.set_y(165)
    pdf.set_font("DejaVu", "B", 13)
    pdf.set_text_color(78, 121, 167)
    pdf.cell(0, 7, "Indice")
    pdf.ln(8)
    pdf.set_text_color(33, 37, 41)
    pdf.set_font("DejaVu", "", 10.5)
    indice = [
        "1.  Apertura",
        "2.  Por que hablar primero de las bases de datos",
        "3.  Las fuentes de datos abiertos",
        "4.  Resumen: que hace cada base",
        "5.  Como construimos el modelo dimensional",
        "6.  Por que este modelo es util",
        "7.  Que es el HHI y por que lo usamos",
        "8.  Resultados con datos reales",
        "9.  Hallazgos clave",
        "10. Limitaciones explicitas",
        "11. Cierre conjunto",
        "Anexo: tablas resumen de datos para apoyo visual",
    ]
    for item in indice:
        pdf.cell(0, 5.5, item)
        pdf.ln(5.5)


def main() -> None:
    md_text = SOURCE.read_text(encoding="utf-8")
    # Quitar el bloque de portada/intro y manejarlo aparte:
    # detectamos el inicio del cuerpo (primera "## 1.").
    intro_end = md_text.find("\n## 1.")
    body = md_text[intro_end + 1:] if intro_end > 0 else md_text

    pdf = GuionPDF()
    register_fonts(pdf)
    render_cover(pdf)
    pdf.add_page()
    render_markdown(pdf, body)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUTPUT))
    print(f"OK {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
