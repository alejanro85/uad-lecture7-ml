import copy, json
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.oxml.ns import qn
from lxml import etree

GREEN = RGBColor(0x37, 0xB3, 0x4A)
GREEN2 = RGBColor(0x56, 0x96, 0x5B)
DARK = RGBColor(0x24, 0x41, 0x28)
PURPLE = RGBColor(0x72, 0x47, 0x96)
ORANGE = RGBColor(0xDA, 0x49, 0x27)
PEACH = RGBColor(0xF3, 0x97, 0x68)
INK = RGBColor(0x1E, 0x1E, 0x1E)
GREY = RGBColor(0x5E, 0x63, 0x6B)
LIGHT = RGBColor(0xEE, 0xF5, 0xEE)
LIGHT2 = RGBColor(0xF4, 0xF4, 0xF6)
LPURPLE = RGBColor(0xEF, 0xEA, 0xF5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CODEBG = RGBColor(0x1F, 0x2B, 0x22)

F_REG = "Onest Regular"
F_SEMI = "Onest SemiBold"
F_BOLD = "Onest ExtraBold"
F_MONO = "Consolas"

REPO = "https://github.com/alejanro85/uad-lecture7-ml"
COLAB = "https://colab.research.google.com/github/alejanro85/uad-lecture7-ml/blob/main/notebooks/"


def I(x):
    return Inches(x)


def set_run(r, size=16, color=INK, font=F_REG, bold=False, italic=False, link=None):
    r.font.size = Pt(size)
    r.font.name = font
    r.font.bold = bold
    r.font.italic = italic
    if color is not None:
        r.font.color.rgb = color
    if link:
        r.hyperlink.address = link


def fill_tf(tf, paras, size=16, color=INK, font=F_REG, align=PP_ALIGN.LEFT, space_after=6, line=None, bullets=False):
    """paras: list of items; item = str | list of runs (str or dict(text=..,b=..,c=..,link=..,f=..,s=..)) | dict(runs=..,lvl=..,bullet=..)"""
    tf.word_wrap = True
    first = True
    for item in paras:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.space_after = Pt(space_after)
        if line:
            p.line_spacing = line
        bullet = bullets
        runs = item
        psize = size
        if isinstance(item, dict):
            runs = item.get("runs", item.get("text", ""))
            bullet = item.get("bullet", bullets)
            psize = item.get("s", size)
            if "after" in item:
                p.space_after = Pt(item["after"])
        if isinstance(runs, str):
            runs = [runs]
        for rr in runs:
            if isinstance(rr, str):
                rr = {"text": rr}
            r = p.add_run()
            r.text = rr["text"]
            set_run(r, size=rr.get("s", psize), color=rr.get("c", color), font=rr.get("f", F_SEMI if rr.get("b") else font),
                    bold=False, link=rr.get("link"))
        if bullet:
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(int(Pt(psize * 1.1))))
            pPr.set("indent", str(-int(Pt(psize * 1.1))))
            for t in ("a:buNone", "a:buChar", "a:buAutoNum"):
                for e in pPr.findall(qn(t)):
                    pPr.remove(e)
            buClr = etree.SubElement(pPr, qn("a:buClr"))
            s = etree.SubElement(buClr, qn("a:srgbClr")); s.set("val", "37B34A")
            bf = etree.SubElement(pPr, qn("a:buFont")); bf.set("typeface", "Arial")
            bc = etree.SubElement(pPr, qn("a:buChar")); bc.set("char", "•")
    return tf


def tb(slide, x, y, w, h, paras, size=16, color=INK, font=F_REG, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
       margin=0.05, bullets=False, space_after=6, line=None):
    s = slide.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = s.text_frame
    tf.margin_left = tf.margin_right = I(margin)
    tf.margin_top = tf.margin_bottom = I(0.03)
    tf.vertical_anchor = anchor
    fill_tf(tf, paras, size=size, color=color, font=font, align=align, bullets=bullets, space_after=space_after, line=line)
    return s


def box(slide, x, y, w, h, fill=LIGHT, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06):
    s = slide.shapes.add_shape(shape, I(x), I(y), I(w), I(h))
    s.shadow.inherit = False
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(1)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.text_frame.text = ""
    return s


def card(slide, x, y, w, h, paras, fill=LIGHT, size=16, color=INK, pad=0.18, anchor=MSO_ANCHOR.TOP, bullets=False,
         align=PP_ALIGN.LEFT, line=None, space_after=6):
    s = box(slide, x, y, w, h, fill=fill, line=line)
    tf = s.text_frame
    tf.margin_left = tf.margin_right = I(pad)
    tf.margin_top = tf.margin_bottom = I(pad * 0.8)
    tf.vertical_anchor = anchor
    fill_tf(tf, paras, size=size, color=color, align=align, bullets=bullets, space_after=space_after)
    return s


def code(slide, x, y, w, h, text, size=13):
    s = box(slide, x, y, w, h, fill=CODEBG, radius=0.04)
    tf = s.text_frame
    tf.margin_left = tf.margin_right = I(0.2)
    tf.margin_top = tf.margin_bottom = I(0.14)
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.word_wrap = True
    first = True
    for ln in text.split("\n"):
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.space_after = Pt(1)
        com = ln.lstrip().startswith("#")
        if "#" in ln and not com:
            i = ln.index("  #") if "  #" in ln else -1
        else:
            i = -1
        parts = [(ln, com)] if i < 0 else [(ln[:i], False), (ln[i:], True)]
        for t, c in parts:
            r = p.add_run(); r.text = t if t else " "
            set_run(r, size=size, font=F_MONO, color=RGBColor(0x9F, 0xD8, 0xA8) if c else RGBColor(0xF2, 0xF2, 0xF2))
    return s


def arrow(slide, x, y, w, h, color=GREEN):
    s = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, I(x), I(y), I(w), I(h))
    s.fill.solid(); s.fill.fore_color.rgb = color; s.line.fill.background(); s.shadow.inherit = False
    return s


def table(slide, x, y, w, h, rows, colw=None, size=14, header_fill=DARK, zebra=True, first_bold=False, header=True,
          row_h=None, align_cols=None):
    nr, nc = len(rows), len(rows[0])
    gs = slide.shapes.add_table(nr, nc, I(x), I(y), I(w), I(h))
    t = gs.table
    tblPr = t._tbl.tblPr
    for a in ("bandRow", "firstRow"):
        tblPr.set(a, "0")
    st = tblPr.find(qn("a:tableStyleId"))
    if st is not None:
        st.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"  # No style, table grid
    if colw:
        for i, cw in enumerate(colw):
            t.columns[i].width = I(cw)
    for ri, row in enumerate(rows):
        if row_h:
            t.rows[ri].height = I(row_h)
        for ci, val in enumerate(row):
            cell = t.cell(ri, ci)
            cell.margin_left = cell.margin_right = I(0.08)
            cell.margin_top = cell.margin_bottom = I(0.04)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            ishead = header and ri == 0
            if ishead:
                cell.fill.solid(); cell.fill.fore_color.rgb = header_fill
            elif zebra and ri % 2 == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = LIGHT2
            else:
                cell.fill.solid(); cell.fill.fore_color.rgb = WHITE
            tf = cell.text_frame
            tf.word_wrap = True
            paras = [val if isinstance(val, list) else [val]]
            fill_tf(tf, paras,
                    size=size, color=WHITE if ishead else INK,
                    font=F_SEMI if (ishead or (first_bold and ci == 0)) else F_REG, space_after=0,
                    align=(align_cols[ci] if align_cols else PP_ALIGN.LEFT))
            # borders
            tcPr = cell._tc.get_or_add_tcPr()
            for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
                ln = etree.SubElement(tcPr, qn(tag)); ln.set("w", "6350")
                sf = etree.SubElement(ln, qn("a:solidFill")); c = etree.SubElement(sf, qn("a:srgbClr")); c.set("val", "D5DAD6")
    return gs


def cell_fill(gs, r, c, color, txt=None):
    cell = gs.table.cell(r, c)
    cell.fill.solid(); cell.fill.fore_color.rgb = color
    if txt is not None:
        for p in cell.text_frame.paragraphs:
            for rr in p.runs:
                rr.font.color.rgb = txt


def style_chart(ch, size=14, legend=False):
    ch.font.size = Pt(size)
    ch.font.name = F_REG
    ch.font.color.rgb = GREY
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(size)


def gridlines(ax, on=True):
    ax.has_major_gridlines = on
    if on:
        ax.major_gridlines.format.line.color.rgb = RGBColor(0xE2, 0xE5, 0xE2)
        ax.major_gridlines.format.line.width = Pt(0.75)


def axis_line(ax, color=RGBColor(0xBF, 0xC4, 0xC0)):
    ax.format.line.color.rgb = color


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def qr(path, url, dark="244128"):
    import qrcode
    q = qrcode.QRCode(border=1, box_size=12)
    q.add_data(url); q.make(fit=True)
    img = q.make_image(fill_color="#" + dark, back_color="white")
    img.save(path)
    return path
