import copy, json, os
from lib import *
HIGHL = RGBColor(0x2A, 0x86, 0x38)

D = json.load(open("data.json"))
IMG = "/home/user/workspace/lecture7/img/"
os.makedirs("/tmp/qr", exist_ok=True)

prs = Presentation("/tmp/brand/tpl_MaNvMhjA485GEw.pptx")
L_SECTION = prs.slide_layouts[5]
L_CONTENT = prs.slide_layouts[11]

# --- detach "01" text box from section layout (we place our own number on each section slide)
num_tpl = None
for sh in list(L_SECTION.shapes):
    if sh.shape_type == 17 and sh.has_text_frame and sh.text_frame.text.strip() == "01":
        num_tpl = copy.deepcopy(sh._element)
        sh._element.getparent().remove(sh._element)

sldnum_tpl = None
for sh in L_CONTENT.placeholders:
    if sh.placeholder_format.idx == 12:
        sldnum_tpl = sh._element

SLIDE_NO = [0]


def add_sldnum(slide):
    el = copy.deepcopy(sldnum_tpl)
    slide.shapes._spTree.append(el)


def footer(slide, runs, y=6.86):
    """runs: list of str/dict for source line"""
    tb(slide, 0.45, y, 9.3, 0.3, [runs], size=10, color=GREY)


def content(title, src=None, note=None):
    s = prs.slides.add_slide(L_CONTENT)
    s.shapes.title.text = title
    for p in s.shapes.title.text_frame.paragraphs:
        for r in p.runs:
            r.font.size = Pt(24)
    add_sldnum(s)
    if src:
        footer(s, src)
    if note:
        notes(s, note)
    return s


def section(num, title, sub, note=None):
    s = prs.slides.add_slide(L_SECTION)
    s.shapes.title.text = title
    s.placeholders[1].text = sub
    el = copy.deepcopy(num_tpl)
    s.shapes._spTree.append(el)
    for t in el.iter(qn("a:t")):
        t.text = num
    if note:
        notes(s, note)
    return s


def src_runs(*pairs, prefix="Источник: "):
    out = [prefix]
    for k, (name, url) in enumerate(pairs):
        if k:
            out.append(", ")
        out.append({"text": name, "link": url, "c": PURPLE})
    return out


def colab_link(nb):
    return COLAB + nb + ".ipynb"


# ========================= 1. TITLE (template slide 0)
t0 = prs.slides[0]
for sh in t0.shapes:
    if not sh.has_text_frame:
        continue
    txt = sh.text_frame.text
    paras = sh.text_frame.paragraphs

    def put(lines):
        for i, p in enumerate(paras):
            if i < len(lines):
                rs = p.runs
                if rs:
                    rs[0].text = lines[i]
                    for r in rs[1:]:
                        r._r.getparent().remove(r._r)
            else:
                p._p.getparent().remove(p._p)
    if "НАУЧНО" in txt:
        put(["   ОТ ДАННЫХ", "К РЕШЕНИЮ"])
        for p in sh.text_frame.paragraphs:
            p.line_spacing = 0.92
        sh.top = sh.top - I(0.38)
    elif "ПОТЕНЦИАЛ" in txt:
        put(["ЗА 10 ШАГОВ"])
        sh.top = sh.top + I(0.4)
    elif "ПОЛИТЕХНИЧЕСКОГО" in txt:
        put(["МАШИННОЕ ОБУЧЕНИЕ", "НА ОТКРЫТЫХ ДАННЫХ"])
        sh.top = I(4.25)
    elif txt.strip() == "2025":
        put(["2026"])
    elif "Иванов" in txt:
        put(["Лекция 7", "Открытая лекция", "Управление и аналитика данных на предприятии"])
notes(t0, "Открытая лекция. Тема: машинное обучение простым языком — от вопроса бизнеса до проверенной модели. "
          "Весь код и данные открыты, ссылки и QR-коды — в презентации.")

# ========================= 2. Agenda
s = content("За 90 минут пройдём путь от вопроса бизнеса до проверенной модели")
items = [
    ("01", "Задачи машинного обучения", "какие вопросы предприятия решает ML и где брать данные"),
    ("02", "Эталон на students.csv", "10 шагов в Google Colab: от паспорта данных до матрицы ошибок"),
    ("03", "То же без кода", "сценарий в low-code системе Orange на том же датасете"),
    ("04", "Кейсы профилей", "нефтегаз, энергетика, строительство, производство"),
    ("05", "От ЛР1 к ЛР2", "TO BE → данные, обратная задача, GitHub, чек-лист сдачи"),
]
x0, y0, w, h, gap = 0.5, 1.95, 2.33, 3.2, 0.13
for i, (n, t, d) in enumerate(items):
    x = x0 + i * (w + gap)
    card(s, x, y0, w, h, [{"runs": [{"text": n, "s": 40, "c": GREEN, "f": F_SEMI}], "after": 10},
                          {"runs": [{"text": t, "b": True, "s": 18}], "after": 8},
                          {"runs": [{"text": d, "s": 14, "c": GREY}]}], fill=LIGHT)
tb(s, 0.5, 5.45, 12.3, 1.2, [
    [{"text": "Что вы унесёте с лекции: ", "b": True},
     "6 готовых Colab-блокнотов с интерпретацией, схему Orange, шаблон генерации датасета и чек-лист ЛР2. "
     "Все материалы — в открытом репозитории (QR-код на последнем слайде)."]], size=16)
notes(s, "Пять блоков. Акцент — логика рассуждения, а не библиотеки: один и тот же сценарий работает в Python и в Orange.")

# ========================= SECTION 01
section("01", "Задачи машинного обучения", "Какие вопросы предприятия решаются на данных")

# ========================= 3. Data -> decision chain
s = content("Данные ценны, только если меняют решение в бизнес‑процессе",
            note="Связь двух лабораторных: в ЛР1 вы построили ССП и модели AS IS / TO BE. "
                 "В TO BE появляется шлюз, где решение принимается по данным. ЛР2 — это и есть этот шлюз.")
steps = [("ЛР1 · ССП", "цель и KPI: снизить простои, потери, брак"),
         ("ЛР1 · AS IS", "узкое место: решение «на глаз», с опозданием"),
         ("ЛР1 · TO BE", "шлюз «решение по данным»: да / нет, сколько, когда"),
         ("ЛР2 · данные", "датасет с признаками и целевой переменной"),
         ("ЛР2 · модель", "прогноз + оценка качества против базовой линии"),
         ("Эффект", "KPI из ССП: сколько случаев найдено, сколько стоит ошибка")]
w, gap = 1.86, 0.22
for i, (t, d) in enumerate(steps):
    x = 0.5 + i * (w + gap)
    fillc = LPURPLE if i < 3 else (LIGHT if i < 5 else DARK)
    col = WHITE if i == 5 else INK
    card(s, x, 2.0, w, 2.35, [{"runs": [{"text": t, "b": True, "s": 16, "c": (WHITE if i == 5 else (PURPLE if i < 3 else DARK))}], "after": 8},
                             {"runs": [{"text": d, "s": 14, "c": col}]}], fill=fillc, pad=0.14)
    if i < 5:
        arrow(s, x + w + 0.03, 3.05, 0.16, 0.25, color=GREEN if i >= 2 else PURPLE)
card(s, 0.5, 4.7, 12.3, 1.85, [
    {"runs": [{"text": "Пример. ", "b": True}, "Факельная установка НПЗ: в AS IS осмотр ствола — по графику. "
              "В TO BE шлюз «Нужен внеплановый осмотр?» решается по крену, ветру, нагрузке и давности осмотра. "
              "Целевая переменная — «осмотр нужен: да/нет», метрика — доля пойманных опасных случаев (полнота)."], "after": 6},
    {"runs": [{"text": "Правило: ", "b": True, "c": DARK}, "сначала вопрос и решение, потом данные и модель — не наоборот."]}],
    fill=LIGHT2, size=16)

# ========================= 4. ML task map
s = content("Пять типовых задач ML покрывают большинство отраслевых кейсов",
            note="Не нужно знать алгоритмы — нужно узнать тип вопроса. Тип вопроса определяет и модель, и метрику.")
rows = [["Задача", "Вопрос", "Нефтегаз", "Энергетика", "Строительство", "Производство"],
        ["Классификация", "Да или нет? Какой класс?", "Пятно на снимке — нефть?", "Режим сети устойчив?", "Партия бетона ≥ 30 МПа?", "Отказ станка в смене?"],
        ["Регрессия", "Сколько?", "Дебит скважины", "Потребление тепла завтра", "Прочность бетона, МПа", "Время до износа"],
        ["Прогноз ряда", "Что будет дальше?", "Цена Brent", "Нагрузка по часам", "Цена м² по месяцам", "Спрос на продукцию"],
        ["Кластеризация", "Какие есть группы?", "Типы скважин", "Профили потребителей", "Типы объектов", "Режимы работы"],
        ["Аномалии", "Что необычно?", "Утечка, сбой датчика", "Хищение энергии", "Крен конструкции", "Брак, вибрация"]]
g = table(s, 0.5, 1.85, 12.3, 4.4, rows, colw=[1.85, 2.15, 2.1, 2.1, 2.1, 2.0], size=14, first_bold=True, row_h=0.7)
for r in range(1, 6):
    cell_fill(g, r, 0, LIGHT if r != 1 else GREEN, txt=(WHITE if r == 1 else DARK))
tb(s, 0.5, 6.3, 12.3, 0.45, [[{"text": "Сегодня в фокусе — классификация: ", "b": True},
                             "её результат проще всего превратить в управленческое решение и оценить в деньгах."]], size=14, color=GREY)

# ========================= 5. Classification explained
s = content("Классификация оценивает вероятность события, а решение принимает порог",
            note="Логистическая регрессия — взвешенная сумма признаков, сжатая в вероятность 0–1. Порог задаёт бизнес, а не модель.")
flow = [("Объект", "студент, скважина,\nпартия бетона"), ("Признаки x", "баллы, давление,\nВ/Ц, возраст"),
        ("Модель", "взвешенная сумма\nпризнаков"), ("Вероятность p", "от 0 до 1"), ("Решение", "p ≥ порог → «да»")]
w, gap = 2.18, 0.35
for i, (t, d) in enumerate(flow):
    x = 0.5 + i * (w + gap)
    card(s, x, 1.95, w, 1.45, [{"runs": [{"text": t, "b": True, "s": 18, "c": WHITE if i == 4 else DARK}], "after": 4}, {"runs": [{"text": d, "s": 14, "c": WHITE if i == 4 else GREY}]}],
         fill=LIGHT if i != 4 else DARK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, pad=0.1)
    if i == 4:
        pass
    if i < 4:
        arrow(s, x + w + 0.07, 2.55, 0.22, 0.26)
card(s, 0.5, 3.75, 6.0, 2.85, [
    {"runs": [{"text": "Логистическая регрессия", "b": True, "s": 18}], "after": 8},
    {"runs": [{"text": "z = b₀ + b₁·x₁ + b₂·x₂ + … + bₙ·xₙ", "f": F_MONO, "s": 16}], "after": 4},
    {"runs": [{"text": "p = 1 / (1 + e⁻ᶻ)", "f": F_MONO, "s": 16}], "after": 10},
    {"runs": ["Вес bᵢ показывает, в какую сторону и насколько сильно признак сдвигает вероятность. "
              "Модель простая и объяснимая — поэтому с неё начинают."], "s": 15}], fill=LIGHT2)
card(s, 6.8, 3.75, 6.0, 2.85, [
    {"runs": [{"text": "Две ошибки — разная цена", "b": True, "s": 18}], "after": 8},
    {"runs": [{"text": "Ложная тревога: ", "b": True, "c": ORANGE}, "лишний осмотр, лишняя консультация — стоит денег."], "bullet": True, "s": 15},
    {"runs": [{"text": "Пропуск: ", "b": True, "c": RGBColor(0xA8, 0x2E, 0x14)}, "не нашли разлив, отказ, неуспевающего — стоит дороже."], "bullet": True, "s": 15},
    {"runs": ["Поэтому порог 0,5 — не закон: его сдвигают под цену ошибок."], "s": 15}], fill=LIGHT2)

# ========================= 6. Open data sources
s = content("Открытые данные для ЛР2 есть по каждому отраслевому профилю",
            src=src_runs(("Kaggle", "https://www.kaggle.com/datasets"), ("UCI ML Repository", "https://archive.ics.uci.edu/datasets"),
                         ("Google Dataset Search", "https://datasetsearch.research.google.com/"), ("EIA / datasets", "https://github.com/datasets/oil-prices"),
                         ("Petrobras 3W", "https://github.com/petrobras/3W")),
            note="Формат не важен: CSV, Excel, JSON читаются одной строкой pandas. Важно — лицензия, описание столбцов и наличие целевой переменной.")
srcs = [("Kaggle", "kaggle.com/datasets", "крупнейший каталог, есть оценки и чужие блокноты", "https://www.kaggle.com/datasets"),
        ("UCI ML Repository", "archive.ics.uci.edu", "классические учебные наборы с описанием", "https://archive.ics.uci.edu/datasets"),
        ("Google Dataset Search", "datasetsearch.research.google.com", "поиск по открытым порталам мира", "https://datasetsearch.research.google.com/"),
        ("GitHub", "github.com/datasets, petrobras/3W", "данные с историей версий и прямыми ссылками", "https://github.com/datasets")]
for i, (n, u, d, link) in enumerate(srcs):
    y = 1.9 + i * 1.12
    card(s, 0.5, y, 5.3, 0.98, [{"runs": [{"text": n, "b": True, "s": 17, "link": link, "c": DARK}, {"text": "  " + u, "s": 13, "c": GREY}], "after": 2},
                               {"runs": [{"text": d, "s": 14, "c": INK}]}], fill=LIGHT, pad=0.14, anchor=MSO_ANCHOR.MIDDLE)
rows = [["Профиль", "Датасет в лекции", "Формат"],
        ["Нефтегаз", [{"text": "Brent (EIA), SAR-снимки разливов", "link": "https://github.com/datasets/oil-prices"}], "CSV"],
        ["Энергетика", [{"text": "Устойчивость умной сети (UCI)", "link": "https://archive.ics.uci.edu/dataset/471/electrical+grid+stability+simulated+data"}], "CSV"],
        ["Строительство", [{"text": "Прочность бетона (UCI)", "link": "https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength"}], "Excel"],
        ["Производство", [{"text": "AI4I 2020, отказы станка (UCI)", "link": "https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset"}], "CSV"],
        ["Эталон", [{"text": "students.csv (курс Stepik)", "link": "https://stepik.org/a/177213"}], "CSV"]]
table(s, 6.15, 1.9, 6.65, 4.4, rows, colw=[1.75, 3.9, 1.0], size=14, first_bold=True, row_h=0.62)

# ========================= SECTION 02
section("02", "Эталон: students.csv", "Один сценарий из 10 шагов — для любого датасета")

# ========================= 7. 10-step scenario
s = content("Один сценарий из 10 шагов подходит для любого датасета",
            src=["Эталонный блокнот: ", {"text": "00_students_etalon.ipynb в Colab", "link": colab_link("00_students_etalon"), "c": PURPLE}],
            note="Это скелет каждого блокнота лекции и требуемая структура итога ЛР2.")
st = [("Вопрос", "какое решение поддерживаем"), ("Загрузка", "pd.read_csv(ссылка)"), ("Паспорт", "размер, типы, пропуски"),
      ("Очистка", "ошибки, пропуски, опечатки"), ("Разведка", "распределения, выбросы"),
      ("Связи и тренды", "корреляции, группы"), ("Постановка ML", "цель y и признаки X"), ("Разбиение", "train / test 75 / 25"),
      ("Модель", "+ базовая линия"), ("Качество и вывод", "метрики → решение")]
w, h, gx = 2.3, 1.75, 0.2
for i, (t, d) in enumerate(st):
    r, c = divmod(i, 5)
    x = 0.5 + c * (w + gx); y = 1.95 + r * (h + 0.4)
    fillc = LPURPLE if i < 6 else LIGHT
    card(s, x, y, w, h, [{"runs": [{"text": f"{i+1:02d}", "s": 26, "c": PURPLE if i < 6 else GREEN, "f": F_SEMI}], "after": 2},
                         {"runs": [{"text": t, "b": True, "s": 17}], "after": 2},
                         {"runs": [{"text": d, "s": 14, "c": GREY}]}], fill=fillc, pad=0.14)
tb(s, 0.5, 1.6, 6, 0.3, [[{"text": "Шаги 1–6: статистика и разведка", "c": PURPLE, "b": True}]], size=14)
tb(s, 4.4, 1.6, 6, 0.3, [[{"text": "Шаги 7–10: машинное обучение", "c": HIGHL, "b": True}]], size=14)

# ========================= 8. Steps 1-4: load, passport, cleaning
s = content("Шаги 1–4: паспорт данных показывает, что чинить до моделирования",
            src=src_runs(("students.csv", "https://raw.githubusercontent.com/evgpat/stepik_from_idea_to_mvp/main/datasets/students.csv"),
                         ("Stepik: от идеи к MVP", "https://stepik.org/a/177213")),
            note="Вопрос: кого из студентов заранее пригласить на консультацию по письменной работе. 1000 строк, 8 столбцов.")
code(s, 0.5, 1.85, 6.1, 3.2,
     "import pandas as pd\n"
     "URL = 'https://raw.githubusercontent.com/…/students.csv'\n"
     "df = pd.read_csv(URL)          # шаг 2: загрузка\n"
     "df.info()                      # шаг 3: паспорт\n"
     "df.isna().sum()                # пропуски\n\n"
     "df['math score'] = df['math score'].clip(lower=0)\n"
     "df[num] = df[num].fillna(df[num].mean())\n"
     "df[cat] = df[cat].fillna('unknown')\n"
     "df['lunch'] = df['lunch'].replace('standart', 'standard')", size=12)
card(s, 0.5, 5.25, 6.1, 1.35, [{"runs": [{"text": "Вопрос (шаг 1): ", "b": True},
                                         "кого заранее пригласить на консультацию, чтобы не допустить провала письменной работы?"]}],
     fill=LIGHT, size=15, anchor=MSO_ANCHOR.MIDDLE)
rows = [["Проблема в данных", "Сколько", "Решение"],
        ["Пропуски gender", "77", "категория «unknown»"],
        ["Пропуски parental education", "76", "категория «unknown»"],
        ["Пропуски math score", "48", "среднее (< 5% строк)"],
        ["Пропуски reading score", "10", "среднее"],
        ["Отрицательный балл math", str(D["stud_raw"]["neg_math"]), "обрезать до 0"],
        ["Опечатка «standart»", str(D["stud_raw"]["standart"]), "заменить на «standard»"]]
table(s, 6.9, 1.85, 5.9, 4.0, rows, colw=[2.65, 1.0, 2.25], size=14, row_h=0.55, align_cols=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT])
tb(s, 6.9, 6.0, 5.9, 0.6, [[{"text": "1000 строк × 8 столбцов. ", "b": True}, "После очистки — 0 пропусков, ни одна строка не удалена."]], size=14)

# ========================= 9. EDA: prep course + correlation (native chart)
s = content("Шаги 5–6: подготовительный курс даёт +10 баллов, а чтение почти дублирует письмо",
            note="Средний балл за письмо: 74,4 у прошедших подготовку против 64,5 у остальных. Корреляция чтения и письма 0,95 — "
                 "сильная связь, но это не причинность.")
cd = CategoryChartData(); cd.categories = ["прошли курс", "без курса"]; cd.add_series("Средний балл за письмо", (74.4, 64.5))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, I(0.5), I(1.9), I(5.6), I(4.3), cd); ch = gf.chart
style_chart(ch); pl = ch.plots[0]; pl.gap_width = 70; pl.has_data_labels = True
pl.data_labels.font.size = Pt(18); pl.data_labels.font.name = F_SEMI; pl.data_labels.font.color.rgb = INK
pl.data_labels.number_format = '0.0'; pl.data_labels.number_format_is_linked = False
pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
ser = pl.series[0]
for i, col in enumerate([GREEN, RGBColor(0xB9, 0xC2, 0xBB)]):
    pt = ser.points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = col
va = ch.value_axis; va.minimum_scale = 0; va.maximum_scale = 100; va.major_unit = 20; gridlines(va); va.format.line.fill.background()
va.tick_labels.font.size = Pt(14); ch.category_axis.tick_labels.font.size = Pt(16); axis_line(ch.category_axis)
ch.has_title = True; ch.chart_title.text_frame.text = "Средний балл за письмо"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(16); ch.chart_title.text_frame.paragraphs[0].runs[0].font.name = F_SEMI
rows = [["Корреляция", "math", "reading", "writing"]]
names = ["math", "reading", "writing"]
for i, n in enumerate(names):
    rows.append([n] + [f"{v:.2f}".replace(".", ",") for v in D["stud_corr"][i]])
g = table(s, 6.5, 1.95, 6.3, 2.1, rows, colw=[1.8, 1.5, 1.5, 1.5], size=15, first_bold=True, row_h=0.5,
          align_cols=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER])
cell_fill(g, 2, 3, HIGHL, WHITE); cell_fill(g, 3, 2, HIGHL, WHITE)
card(s, 6.5, 4.3, 6.3, 2.3, [
    {"runs": [{"text": "Что это значит для модели", "b": True, "s": 17}], "after": 6},
    {"runs": ["Сильные признаки есть — модель будет полезной."], "bullet": True},
    {"runs": ["Письмо — это ответ, его нельзя подавать на вход: иначе «подсказка» (утечка)."], "bullet": True},
    {"runs": ["Корреляция ≠ причина: курс выбирают мотивированные."], "bullet": True}], fill=LIGHT, size=15)

# ========================= 10. Binarization histogram
s = content("Шаг 7: порог 50 баллов превращает оценку в ответ «сдал / не сдал»",
            note="114 из 1000 студентов ниже 50 баллов — 11,4%. Классы несбалансированы: это ключ к ловушке accuracy.")
hist = D["stud_hist"]
cats = ["10–19", "20–29", "30–39", "40–49", "50–59", "60–69", "70–79", "80–89", "90–100"]
cd = CategoryChartData(); cd.categories = cats; cd.add_series("Студентов", hist[1:])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, I(0.5), I(1.85), I(7.6), I(4.75), cd); ch = gf.chart
style_chart(ch); pl = ch.plots[0]; pl.gap_width = 25; pl.has_data_labels = True
pl.data_labels.font.size = Pt(14); pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
for i in range(len(cats)):
    pt = pl.series[0].points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = ORANGE if i < 4 else GREEN
gridlines(ch.value_axis); ch.value_axis.format.line.fill.background(); ch.value_axis.tick_labels.font.size = Pt(14)
ch.category_axis.tick_labels.font.size = Pt(14); axis_line(ch.category_axis)
ch.has_title = True; ch.chart_title.text_frame.text = "Распределение баллов за письмо, число студентов"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(15); ch.chart_title.text_frame.paragraphs[0].runs[0].font.name = F_SEMI
tb(s, 8.45, 1.95, 4.4, 1.1, [[{"text": "114", "s": 54, "c": ORANGE, "f": F_SEMI}, {"text": "  из 1000", "s": 20, "c": GREY}]])
tb(s, 8.45, 3.0, 4.4, 0.6, [["не сдали (< 50 баллов) — всего 11,4%"]], size=16)
code(s, 8.45, 3.75, 4.35, 1.3, "w = df['writing score']\ny = (w >= 50).astype(int)\nX = df.drop(columns=['writing score'])\nX = pd.get_dummies(X, drop_first=True)", size=11)
card(s, 8.45, 5.25, 4.35, 1.35, [[{"text": "Классы несбалансированы: ", "b": True}, "модель «все сдали» уже права в 88% случаев."]], fill=LPURPLE, size=15, anchor=MSO_ANCHOR.MIDDLE)

# ========================= 11. Baseline vs model
s = content("Шаги 8–9: модель сравнивают с базовой линией, а не с нулём",
            note="Базовая линия — DummyClassifier «всегда большинство». Если модель её не превосходит, модели нет. "
                 "Тестовая выборка — 250 студентов (25%), stratify сохраняет долю классов.")
code(s, 0.5, 1.85, 6.0, 3.0,
     "X_train, X_test, y_train, y_test = train_test_split(\n"
     "    X, y, test_size=0.25, stratify=y, random_state=42)\n\n"
     "baseline = DummyClassifier(strategy='most_frequent')\n"
     "model = make_pipeline(StandardScaler(),\n"
     "                      LogisticRegression(max_iter=1000))\n"
     "model.fit(X_train, y_train)\n"
     "proba = model.predict_proba(X_test)[:, 1]", size=12)
card(s, 0.5, 5.05, 6.0, 1.55, [[{"text": "Честная проверка: ", "b": True},
                               "модель учится на 750 студентах, а оценивается на 250, которых не видела."]], fill=LIGHT, size=15, anchor=MSO_ANCHOR.MIDDLE)
cd = CategoryChartData(); cd.categories = ["Базовая линия «все сдали»", "Логистическая регрессия"]
cd.add_series("Accuracy", (0.884, 0.960)); cd.add_series("Найдено «не сдал» из 29", (0 / 29, 22 / 29))
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, I(6.8), I(1.85), I(6.0), I(4.75), cd); ch = gf.chart
style_chart(ch, legend=True); pl = ch.plots[0]; pl.gap_width = 60; pl.overlap = -10; pl.has_data_labels = True
pl.data_labels.number_format = '0%'; pl.data_labels.number_format_is_linked = False; pl.data_labels.font.size = Pt(15)
pl.series[0].format.fill.solid(); pl.series[0].format.fill.fore_color.rgb = RGBColor(0xB9, 0xC2, 0xBB)
pl.series[1].format.fill.solid(); pl.series[1].format.fill.fore_color.rgb = GREEN
va = ch.value_axis; va.minimum_scale = 0; va.maximum_scale = 1; va.major_unit = 0.25; va.tick_labels.number_format = '0%'
va.tick_labels.number_format_is_linked = False; gridlines(va); va.format.line.fill.background(); va.tick_labels.font.size = Pt(14)
ch.category_axis.tick_labels.font.size = Pt(14); ch.category_axis.reverse_order = True; axis_line(ch.category_axis)

# ========================= 12. Confusion matrix
s = content("Матрица несоответствий показывает, кого именно модель пропустила",
            src=src_runs(("Habr: матрица ошибок простыми словами", "https://habr.com/ru/articles/758510/")),
            note="Accuracy 0,960 при базовой 0,884. Но для решения важнее: из 29 реальных «не сдал» модель нашла 22.")
rows = [["", "Модель: «не сдаст»", "Модель: «сдаст»"],
        ["Факт: не сдал (29)", "22", "7"],
        ["Факт: сдал (221)", "3", "218"]]
g = table(s, 0.5, 1.95, 6.4, 3.0, rows, colw=[2.2, 2.1, 2.1], size=16, row_h=0.6, first_bold=True,
          align_cols=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER])
g.table.rows[1].height = I(1.2); g.table.rows[2].height = I(1.2)
cell_fill(g, 1, 1, HIGHL, WHITE); cell_fill(g, 2, 2, LIGHT); cell_fill(g, 1, 2, RGBColor(0xFB, 0xE3, 0xDA)); cell_fill(g, 2, 1, RGBColor(0xFD, 0xF0, 0xE8))
lab = {(1, 1): "найдены", (1, 2): "пропущены", (2, 1): "ложная тревога", (2, 2): "верно"}
for (r, c), l in lab.items():
    tf = g.table.cell(r, c).text_frame
    for rr in tf.paragraphs[0].runs:
        rr.font.size = Pt(28); rr.font.name = F_SEMI
    p = tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER; rn = p.add_run(); rn.text = l
    set_run(rn, size=14, color=WHITE if (r, c) == (1, 1) else INK)
tb(s, 0.5, 5.35, 6.4, 1.2, [[{"text": "Accuracy = 240 / 250 = 0,960", "b": True}],
                           ["но по «не сдал» полнота лишь 22 / 29 = 0,76"]], size=16)
metrics = [("Precision (точность)", "из тех, кого модель назвала «группой риска», сколько действительно в ней", "22 / 25 = 0,88"),
           ("Recall (полнота)", "из всех реально не сдавших, скольких модель нашла", "22 / 29 = 0,76"),
           ("F1", "баланс точности и полноты, когда важны обе", "0,81"),
           ("ROC-AUC", "насколько хорошо модель ранжирует риск при любом пороге", "0,988")]
for i, (n, d, v) in enumerate(metrics):
    y = 1.95 + i * 1.18
    card(s, 7.25, y, 5.55, 1.05, [{"runs": [{"text": n + "   ", "b": True, "s": 16}, {"text": v, "s": 16, "c": DARK, "f": F_SEMI}], "after": 2},
                                 {"runs": [{"text": d, "s": 14, "c": GREY}]}], fill=LIGHT2, pad=0.14, anchor=MSO_ANCHOR.MIDDLE)

# ========================= 13. Threshold
s = content("Сдвиг порога до 0,7 находит 25 из 29 студентов группы риска ценой 9 лишних приглашений",
            note="Порог — управленческий параметр. Консультация дешёвая, провал дорогой — поэтому приглашаем больше. "
                 "Модель ранжирует риск, а решение о пороге принимает руководитель.")
rows = [["Порог «сдаст» ≥", "Найдено «не сдал»", "Пропущено", "Лишние приглашения", "Accuracy"],
        ["0,5 (по умолчанию)", "22 из 29", "7", "3", "0,960"],
        ["0,7 (осторожный)", "25 из 29", "4", "9", "0,948"]]
g = table(s, 0.5, 1.95, 12.3, 1.75, rows, colw=[2.9, 2.5, 2.0, 2.7, 2.2], size=16, row_h=0.58, first_bold=True,
          align_cols=[PP_ALIGN.LEFT] + [PP_ALIGN.CENTER] * 4)
cell_fill(g, 2, 1, HIGHL, WHITE); cell_fill(g, 2, 2, HIGHL, WHITE)
card(s, 0.5, 4.0, 3.9, 2.6, [{"runs": [{"text": "+3", "s": 44, "c": GREEN, "f": F_SEMI}], "after": 2},
                             {"runs": ["студента получат помощь вовремя"], "s": 16}], fill=LIGHT)
card(s, 4.7, 4.0, 3.9, 2.6, [{"runs": [{"text": "+6", "s": 44, "c": PEACH, "f": F_SEMI}], "after": 2},
                             {"runs": ["лишних приглашений — цена консультации"], "s": 16}], fill=LIGHT2)
card(s, 8.9, 4.0, 3.9, 2.6, [{"runs": [{"text": "Вывод для бизнеса", "b": True, "s": 17}], "after": 6},
                             {"runs": ["Если пропуск дороже ложной тревоги, порог сдвигают в сторону осторожности. "
                                       "Accuracy при этом даже падает — и это правильно."], "s": 15}], fill=LPURPLE)

# ========================= 14. Accuracy trap
s = content("Ловушка accuracy: модель по анкете набирает 88% и находит лишь одного из 29",
            note="Модель только на анкетных признаках (пол, образование родителей, обед, курс, группа). "
                 "Accuracy 0,880 — как у базовой линии. ROC-AUC 0,819: ранжирует неплохо, но при пороге 0,5 бесполезна.")
cd = CategoryChartData(); cd.categories = ["Базовая линия", "Только анкета", "Все признаки"]
cd.add_series("Accuracy", (0.884, 0.880, 0.960)); cd.add_series("Полнота по «не сдал»", (0.0, 1 / 29, 22 / 29))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, I(0.5), I(1.85), I(7.4), I(4.8), cd); ch = gf.chart
style_chart(ch, legend=True); pl = ch.plots[0]; pl.gap_width = 70; pl.overlap = -5; pl.has_data_labels = True
pl.data_labels.number_format = '0%'; pl.data_labels.number_format_is_linked = False; pl.data_labels.font.size = Pt(15)
pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
pl.series[0].format.fill.solid(); pl.series[0].format.fill.fore_color.rgb = RGBColor(0xB9, 0xC2, 0xBB)
pl.series[1].format.fill.solid(); pl.series[1].format.fill.fore_color.rgb = GREEN
va = ch.value_axis; va.minimum_scale = 0; va.maximum_scale = 1.1; va.major_unit = 0.25; va.tick_labels.number_format = '0%'
va.tick_labels.number_format_is_linked = False; gridlines(va); va.format.line.fill.background(); va.tick_labels.font.size = Pt(14)
ch.category_axis.tick_labels.font.size = Pt(15); axis_line(ch.category_axis)
card(s, 8.25, 1.95, 4.55, 4.65, [
    {"runs": [{"text": "Три правила оценки", "b": True, "s": 18}], "after": 10},
    {"runs": [{"text": "Сравнивай с базовой линией. ", "b": True}, "Без неё 88% звучит как успех."], "bullet": True, "after": 10},
    {"runs": [{"text": "Смотри полноту по редкому классу. ", "b": True}, "Именно его и ищет бизнес."], "bullet": True, "after": 10},
    {"runs": [{"text": "Показывай матрицу ошибок. ", "b": True}, "Она переводит метрику в людей, скважины и партии."], "bullet": True}],
    fill=LIGHT, size=15)

# ========================= SECTION 03
section("03", "То же самое без кода", "Low-code сценарий в Orange на том же students.csv")

# ========================= 15. Orange workflow
s = content("В Orange тот же сценарий собирается из восьми виджетов без единой строки кода",
            src=src_runs(("Orange Data Mining", "https://orangedatamining.com/"), ("скачать Orange", "https://orangedatamining.com/download/"),
                         ("схема .ows в репозитории", REPO + "/tree/main/orange")),
            note="Файл students_for_orange.csv уже размечен: целевая переменная writing_result, writing score исключён. "
                 "Схема students_classification.ows открывается в Orange 3.")
s.shapes.add_picture(IMG + "orange_workflow.png", I(0.8), I(1.8), height=I(4.15))
rows = [["Виджет Orange", "Шаг сценария"],
        ["Файл", "2–3: загрузка, паспорт"],
        ["Таблица, Распределения", "5–6: разведка"],
        ["Логистическая регрессия", "9: модель"],
        ["Тест и оценка", "8, 10: проверка"],
        ["Матрица несоответствий", "10: ошибки"],
        ["Номограмма", "10: объяснение"]]
table(s, 7.75, 1.85, 5.05, 4.0, rows, colw=[2.65, 2.4], size=14, row_h=0.55, first_bold=True)
tb(s, 0.5, 6.05, 12.3, 0.6, [[{"text": "Подготовка данных: ", "b": True},
                             "в заголовке CSV помечены роли столбцов — cD#writing_result (цель, категория), остальные — признаки."]], size=14)

# ========================= 16. Orange results
s = content("Orange подтверждает Python: CA 0,956 и AUC 0,985 на кросс-валидации",
            note="Небольшая разница с Colab (0,960) объяснима: в Orange — 5-кратная стратифицированная кросс-валидация по всем 1000 строкам, "
                 "в Colab — одна отложенная выборка из 250 строк. Совпадение — аргумент в пользу устойчивости результата.")
tb(s, 0.5, 1.8, 6.4, 0.35, [[{"text": "Виджет «Тест и оценка»: 5-кратная кросс-валидация", "b": True}]], size=14)
s.shapes.add_picture(IMG + "orange_testscore_crop.png", I(0.5), I(2.2), width=I(6.4))
tb(s, 0.5, 3.35, 6.4, 0.35, [[{"text": "Виджет «Матрица несоответствий»: все 1000 строк", "b": True}]], size=14)
s.shapes.add_picture(IMG + "orange_confmat_crop.png", I(0.5), I(3.75), width=I(5.6))
rows = [["Метрика", "Colab, тест", "Orange, CV"],
        ["Accuracy / CA", "0,960", "0,956"],
        ["ROC-AUC", "0,988", "0,985"],
        ["F1 (взвешенная)", "0,96", "0,955"],
        ["Найдено «не сдал»", "22 из 29", "89 из 114"]]
table(s, 7.3, 1.85, 5.5, 3.0, rows, colw=[2.3, 1.6, 1.6], size=15, row_h=0.55, first_bold=True,
      align_cols=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER])
card(s, 7.3, 5.1, 5.5, 1.5, [[{"text": "Один вывод разными инструментами: ", "b": True},
                             "полнота по «не сдал» ≈ 0,76–0,78 в обоих случаях — модель устойчива."]], fill=LIGHT, size=15, anchor=MSO_ANCHOR.MIDDLE)

# ========================= 17. Orange: explain
s = content("Распределения и номограмма объясняют модель руководителю без формул",
            note="Слева: среди прошедших подготовку почти нет «не сдал». Справа: номограмма показывает вклад каждого признака в вероятность «не сдал» — "
                 "чтение даёт основной вклад, затем математика и подготовительный курс.")
s.shapes.add_picture(IMG + "orange_dist_crop.png", I(1.15), I(1.75), height=I(3.95))
s.shapes.add_picture(IMG + "orange_nomogram_crop.png", I(6.75), I(2.35), width=I(6.05))
card(s, 0.5, 5.75, 6.05, 0.9, [["Без подготовки доля «не сдал» в разы выше — гипотеза для управленческого решения."]], fill=LIGHT, size=14, anchor=MSO_ANCHOR.MIDDLE, pad=0.12)
card(s, 6.75, 5.75, 6.05, 0.9, [["Главный вклад в риск — балл за чтение, затем математика и курс."]], fill=LIGHT, size=14, anchor=MSO_ANCHOR.MIDDLE, pad=0.12)

# ========================= SECTION 04
section("04", "Кейсы отраслевых профилей", "Тот же сценарий — на данных нефтегаза, энергетики, строительства и производства")

# ========================= 18. Brent
yrs = []; vals = []
for d_, v in zip(D["brent_m"]["d"], D["brent_m"]["v"]):
    y_, m_ = d_.split("-"); yrs.append(int(y_) + (int(m_) - 0.5) / 12); vals.append(v)
s = content("Нефтегаз: в 2026 году волатильность Brent достигла 71% — максимум с 2020 года",
            src=src_runs(("EIA через datasets/oil-prices", "https://github.com/datasets/oil-prices")) + ["  ·  ",
                 {"text": "Colab: 01_oilgas_brent_oilspill", "link": colab_link("01_oilgas_brent_oilspill"), "c": PURPLE}],
            note="9132 торговых дня с 20.05.1987 по 17.11.2026. В 2026 году цена выросла с 61 $ в январе до пика 138,21 $ 7 апреля. "
                 "Попытка предсказать направление цены через 4 недели: точность 0,556 против базовой 0,554 — честный отрицательный результат: "
                 "цена — почти случайное блуждание, для неё ставят задачу оценки риска, а не угадывания.")
cd = XyChartData(); sr = cd.add_series("Brent, $/барр., среднее за месяц")
for x, v in zip(yrs, vals):
    sr.add_data_point(x, v)
gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, I(0.5), I(1.85), I(8.1), I(4.8), cd); ch = gf.chart
style_chart(ch); ser = ch.plots[0].series[0]; ser.format.line.color.rgb = DARK; ser.format.line.width = Pt(1.75); ser.smooth = False
va = ch.value_axis; va.minimum_scale = 0; va.maximum_scale = 150; va.major_unit = 25; gridlines(va); va.format.line.fill.background()
ca = ch.category_axis; ca.minimum_scale = 1987; ca.maximum_scale = 2027; ca.major_unit = 5; ca.tick_labels.number_format = '0'
ca.tick_labels.number_format_is_linked = False; gridlines(ca, False); axis_line(ca)
va.tick_labels.font.size = Pt(14); ca.tick_labels.font.size = Pt(14)
ch.has_title = True; ch.chart_title.text_frame.text = "Brent, $/барр., среднее за месяц, 1987–2026"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(15); ch.chart_title.text_frame.paragraphs[0].runs[0].font.name = F_SEMI
stats = [("143,95 $", "исторический максимум, 03.07.2008"), ("138,21 $", "пик 2026 года, 07.04.2026"),
         ("71,4%", "годовая волатильность 2026 (2023–2025: 27–34%)"), ("0,556 vs 0,554", "направление через 4 недели: модель ≈ базовая линия")]
for i, (v, d) in enumerate(stats):
    y = 1.9 + i * 1.18
    card(s, 8.9, y, 3.9, 1.05, [{"runs": [{"text": v, "s": 22, "c": ORANGE if i == 3 else GREEN, "f": F_SEMI}], "after": 0},
                               {"runs": [{"text": d, "s": 13, "c": GREY}]}], fill=LIGHT2, pad=0.12, anchor=MSO_ANCHOR.MIDDLE)

# ========================= 19. Oil spill
s = content("Нефтегаз: взвешивание классов поднимает поиск разливов на SAR-снимках с 4 до 9 из 10",
            src=src_runs(("Oil Spill dataset, Kubat et al., 1998", "https://github.com/jbrownlee/Datasets")) + ["  ·  ",
                 {"text": "Colab: 01_oilgas_brent_oilspill", "link": colab_link("01_oilgas_brent_oilspill"), "c": PURPLE}],
            note="937 фрагментов радарных снимков, 41 — нефть (4,4%). Обычная модель: accuracy 0,962 — выше базовой 0,957, но нашла 4 пятна из 10. "
                 "С class_weight='balanced' — 9 из 10, ценой 24 ложных тревог из 235. Оператору нужно перепроверить около 14% снимков вместо 100%.")
for k, (ttl, m, note_) in enumerate([("Обычная логистическая регрессия", [[222, 3], [6, 4]], "accuracy 0,962 · полнота 0,40"),
                                     ("С весами классов (balanced)", [[201, 24], [1, 9]], "accuracy 0,894 · полнота 0,90")]):
    x = 0.5 + k * 4.25
    tb(s, x, 1.85, 4.0, 0.4, [[{"text": ttl, "b": True}]], size=16)
    rows = [["", "→ не нефть", "→ нефть"], ["не нефть", str(m[0][0]), str(m[0][1])], ["нефть", str(m[1][0]), str(m[1][1])]]
    g = table(s, x, 2.3, 4.0, 2.4, rows, colw=[1.4, 1.3, 1.3], size=16, row_h=0.8, first_bold=True,
              align_cols=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER])
    cell_fill(g, 2, 2, HIGHL, WHITE); cell_fill(g, 2, 1, RGBColor(0xFB, 0xE3, 0xDA))
    for r in (1, 2):
        for c in (1, 2):
            for rr in g.table.cell(r, c).text_frame.paragraphs[0].runs:
                rr.font.size = Pt(24); rr.font.name = F_SEMI
    tb(s, x, 4.8, 4.0, 0.4, [[note_]], size=14, color=GREY)
card(s, 9.0, 1.85, 3.8, 4.8, [
    {"runs": [{"text": "937", "s": 36, "c": GREEN, "f": F_SEMI}, {"text": " фрагментов", "s": 16}], "after": 0},
    {"runs": [{"text": "41 — нефть (4,4%)", "s": 15, "c": GREY}], "after": 12},
    {"runs": [{"text": "Решение", "b": True, "s": 17}], "after": 4},
    {"runs": ["Модель — фильтр для оператора: перепроверить ≈ 14% снимков вместо всех и не пропустить 9 из 10 пятен."], "s": 15, "after": 8},
    {"runs": [{"text": "Рычаг: ", "b": True}, "class_weight='balanced' — одна строка кода."], "s": 15}], fill=LIGHT)
tb(s, 0.5, 5.35, 8.25, 1.3, [[{"text": "Строки — факт, столбцы — прогноз. ", "b": True},
                            "Пропущенный разлив дороже ложной тревоги, поэтому accuracy снижается, а ценность модели растёт."]], size=15)

# ========================= 20. Energy grid
s = content("Энергетика: медленная реакция участников сети повышает риск неустойчивости с 28% до 92%",
            src=src_runs(("Electrical Grid Stability, UCI", "https://archive.ics.uci.edu/dataset/471/electrical+grid+stability+simulated+data")) + ["  ·  ",
                 {"text": "Colab: 02_energy_smart_grid", "link": colab_link("02_energy_smart_grid"), "c": PURPLE}],
            note="10 000 симуляций сети «производитель + 3 потребителя», 63,8% неустойчивых. tau — время реакции участника на изменение цены. "
                 "Столбец stab — численный ответ, по нему вычислен stabf: это утечка, его исключаем. p1 = −(p2+p3+p4) — линейная зависимость, тоже исключаем.")
q = D["grid_q"]
cd = CategoryChartData(); cd.categories = list(q.keys()); cd.add_series("Доля неустойчивых режимов", list(q.values()))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, I(0.5), I(1.85), I(7.4), I(4.8), cd); ch = gf.chart
style_chart(ch); pl = ch.plots[0]; pl.gap_width = 45; pl.has_data_labels = True
pl.data_labels.number_format = '0%'; pl.data_labels.number_format_is_linked = False; pl.data_labels.font.size = Pt(16)
pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
shades = [RGBColor(0xB9, 0xE0, 0xBF), RGBColor(0x8C, 0xCF, 0x97), GREEN, GREEN2, DARK]
for i in range(5):
    pt = pl.series[0].points[i]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = shades[i]
va = ch.value_axis; va.minimum_scale = 0; va.maximum_scale = 1; va.major_unit = 0.25; va.tick_labels.number_format = '0%'
va.tick_labels.number_format_is_linked = False; gridlines(va); va.format.line.fill.background(); va.tick_labels.font.size = Pt(14)
ch.category_axis.tick_labels.font.size = Pt(14); axis_line(ch.category_axis)
ch.has_title = True; ch.chart_title.text_frame.text = "Доля неустойчивых режимов по скорости реакции (квинтили τ)"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(15); ch.chart_title.text_frame.paragraphs[0].runs[0].font.name = F_SEMI
rows = [["Модель «неустойчиво?»", "Значение"], ["Accuracy", "0,817"], ["Precision", "0,836"], ["Recall", "0,887"], ["ROC-AUC", "0,891"]]
table(s, 8.25, 1.9, 4.55, 2.5, rows, colw=[2.9, 1.65], size=15, row_h=0.5, first_bold=True, align_cols=[PP_ALIGN.LEFT, PP_ALIGN.CENTER])
card(s, 8.25, 4.6, 4.55, 2.05, [
    {"runs": [{"text": "Две ловушки данных", "b": True, "s": 16}], "after": 4},
    {"runs": [{"text": "stab", "f": F_MONO}, " — готовый ответ: утечка, убираем."], "bullet": True, "s": 14},
    {"runs": [{"text": "p1 = −(p2+p3+p4)", "f": F_MONO}, " — дубль, убираем."], "bullet": True, "s": 14}], fill=LPURPLE)

# ========================= 21. Concrete
s = content("Строительство: признаки В/Ц и log(возраст) поднимают точность прогноза прочности с R² 0,56 до 0,80",
            src=src_runs(("Concrete Compressive Strength, UCI (Excel)", "https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength")) + ["  ·  ",
                 {"text": "Colab: 03_construction_concrete", "link": colab_link("03_construction_concrete"), "c": PURPLE}],
            note="1030 строк, 25 дублей удалены → 1005. Регрессия: исходные признаки R² 0,56, MAE 8,9 МПа; с водоцементным отношением и логарифмом возраста R² 0,80, MAE 5,8 МПа. "
                 "Классификация «≥ 30 МПа»: accuracy 0,909, AUC 0,957; строгий порог 0,8 — точность 0,953 при полноте 0,803.")
cd = XyChartData(); sr = cd.add_series("Партии бетона (тест)")
for a_, b_ in zip(D["conc_scatter"]["fact"], D["conc_scatter"]["pred"]):
    sr.add_data_point(a_, b_)
sr2 = cd.add_series("Идеальный прогноз"); sr2.add_data_point(0, 0); sr2.add_data_point(85, 85)
gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, I(0.5), I(1.85), I(5.6), I(4.8), cd); ch = gf.chart
style_chart(ch, legend=True)
s0 = ch.plots[0].series[0]; s0.marker.style = 8; s0.marker.size = 6; s0.marker.format.fill.solid(); s0.marker.format.fill.fore_color.rgb = GREEN
s0.marker.format.line.fill.background(); s0.format.line.fill.background()
s1 = ch.plots[0].series[1]; s1.marker.style = None
from pptx.enum.chart import XL_MARKER_STYLE
s1.marker.style = XL_MARKER_STYLE.NONE; s1.format.line.color.rgb = DARK; s1.format.line.dash_style = 4; s1.format.line.width = Pt(1.5)
for ax in (ch.value_axis, ch.category_axis):
    ax.minimum_scale = 0; ax.maximum_scale = 90; ax.major_unit = 15; gridlines(ax); ax.tick_labels.font.size = Pt(14)
    ax.has_title = True
ch.category_axis.axis_title.text_frame.text = "факт, МПа"; ch.value_axis.axis_title.text_frame.text = "прогноз, МПа"
for ax in (ch.value_axis, ch.category_axis):
    r = ax.axis_title.text_frame.paragraphs[0].runs[0]; r.font.size = Pt(14); r.font.name = F_REG; r.font.color.rgb = GREY
rows = [["Регрессия «сколько МПа?»", "R²", "MAE, МПа"], ["Исходные 8 признаков", "0,56", "8,9"], ["+ В/Ц и log(возраст)", "0,80", "5,8"]]
g = table(s, 6.45, 1.9, 6.35, 1.6, rows, colw=[3.55, 1.3, 1.5], size=15, row_h=0.5, first_bold=True,
          align_cols=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER])
cell_fill(g, 2, 1, HIGHL, WHITE); cell_fill(g, 2, 2, HIGHL, WHITE)
rows = [["Классификация «≥ 30 МПа?»", "Precision", "Recall"], ["Порог 0,5", "0,911", "0,941"], ["Строгий порог 0,8", "0,953", "0,803"]]
table(s, 6.45, 3.7, 6.35, 1.6, rows, colw=[3.55, 1.3, 1.5], size=15, row_h=0.5, first_bold=True,
      align_cols=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER])
card(s, 6.45, 5.5, 6.35, 1.15, [[{"text": "Знание предметной области ", "b": True},
                                "(закон Абрамса для В/Ц) дало больше, чем смена алгоритма."]], fill=LIGHT, size=15, anchor=MSO_ANCHOR.MIDDLE, pad=0.14)

# ========================= 22. Production AI4I
r_ = D["ai4i"]
labels = ["Сырые датчики", "+ веса классов", "+ физ. признаки", "Физ. признаки + веса"]
found = [m[1][1] for m in r_.values()]; fp = [m[0][1] for m in r_.values()]
s = content("Производство: физические признаки находят 78 из 85 отказов станка",
            src=src_runs(("AI4I 2020 Predictive Maintenance, UCI", "https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset")) + ["  ·  ",
                 {"text": "Colab: 04_production_predictive_maintenance", "link": colab_link("04_production_predictive_maintenance"), "c": PURPLE}],
            note="10 000 записей, 339 отказов (3,4%). На сырых датчиках accuracy 0,968, но найдено 12 из 85 отказов теста. "
                 "Физика: мощность = момент × угловая скорость, перепад температур, нагрузка на изношенный инструмент. "
                 "Физические признаки без весов: 59 из 85 и ни одной ложной тревоги. С весами: 78 из 85 (полнота 0,918), 178 ложных тревог, AUC 0,983. "
                 "Кластеризация KMeans выделяет 4 режима с долей отказов от 1,1% до 9,3%.")
cd = CategoryChartData(); cd.categories = labels
cd.add_series("Найдено отказов из 85", found); cd.add_series("Ложные тревоги", fp)
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, I(0.5), I(1.85), I(7.6), I(4.8), cd); ch = gf.chart
style_chart(ch, legend=True); pl = ch.plots[0]; pl.gap_width = 55; pl.overlap = -10; pl.has_data_labels = True; pl.data_labels.font.size = Pt(15)
pl.series[0].format.fill.solid(); pl.series[0].format.fill.fore_color.rgb = GREEN
pl.series[1].format.fill.solid(); pl.series[1].format.fill.fore_color.rgb = PEACH
ch.category_axis.reverse_order = True; ch.category_axis.tick_labels.font.size = Pt(15); axis_line(ch.category_axis)
va = ch.value_axis; va.minimum_scale = 0; va.maximum_scale = 450; va.major_unit = 100; gridlines(va); va.format.line.fill.background(); va.tick_labels.font.size = Pt(14)
card(s, 8.45, 1.9, 4.35, 2.2, [
    {"runs": [{"text": "Физика процесса", "b": True, "s": 17}], "after": 6},
    {"runs": [{"text": "P = M · ω", "f": F_MONO}, "  мощность"], "bullet": True, "s": 15},
    {"runs": [{"text": "ΔT = Tпроц − Tвозд", "f": F_MONO}], "bullet": True, "s": 15},
    {"runs": [{"text": "износ × момент", "f": F_MONO}, "  нагрузка"], "bullet": True, "s": 15}], fill=LIGHT)
card(s, 8.45, 4.3, 4.35, 2.35, [
    {"runs": [{"text": "Выбор варианта — за бизнесом", "b": True, "s": 17}], "after": 6},
    {"runs": ["0 ложных тревог и 59 из 85 — если осмотр дорог."], "bullet": True, "s": 15},
    {"runs": ["78 из 85 при 178 тревогах — если простой дороже осмотра."], "bullet": True, "s": 15}], fill=LPURPLE)

# ========================= 23. Case hub
s = content("Каждый кейс — готовый Colab-блокнот с разбором и интерпретацией",
            note="Блокноты открываются по ссылке без установки. Данные подтягиваются из GitHub по raw-ссылке — запуск «под ключ»: Среда выполнения → Выполнить все.")
rows = [["Профиль", "Блокнот (открыть в Colab)", "Задача", "Ключевой результат"],
        ["Эталон", [{"text": "00_students_etalon", "link": colab_link("00_students_etalon"), "c": PURPLE}], "классификация", "accuracy 0,960 против 0,884"],
        ["Нефтегаз", [{"text": "01_oilgas_brent_oilspill", "link": colab_link("01_oilgas_brent_oilspill"), "c": PURPLE}], "тренды + классификация", "9 из 10 разливов"],
        ["Энергетика", [{"text": "02_energy_smart_grid", "link": colab_link("02_energy_smart_grid"), "c": PURPLE}], "классификация", "ROC-AUC 0,891"],
        ["Строительство", [{"text": "03_construction_concrete", "link": colab_link("03_construction_concrete"), "c": PURPLE}], "регрессия + классификация", "R² 0,56 → 0,80"],
        ["Производство", [{"text": "04_production_predictive_maintenance", "link": colab_link("04_production_predictive_maintenance"), "c": PURPLE}], "классификация + кластеры", "78 из 85 отказов"],
        ["Мост ЛР1 → ЛР2", [{"text": "05_reverse_task_synthetic_dataset", "link": colab_link("05_reverse_task_synthetic_dataset"), "c": PURPLE}], "генерация датасета", "accuracy 0,751 против 0,582"]]
table(s, 0.5, 1.85, 9.75, 4.8, rows, colw=[1.85, 3.9, 2.15, 1.85], size=14, row_h=0.66, first_bold=True)
qr("/tmp/qr/repo.png", REPO)
s.shapes.add_picture("/tmp/qr/repo.png", I(10.6), I(1.9), width=I(2.2))
tb(s, 10.5, 4.2, 2.4, 1.6, [[{"text": "Репозиторий лекции", "b": True}], [{"text": "github.com/alejanro85/", "link": REPO, "c": PURPLE, "s": 12}], [{"text": "uad-lecture7-ml", "link": REPO, "c": PURPLE, "s": 12}]],
   size=14, align=PP_ALIGN.CENTER)

# ========================= SECTION 05
section("05", "От ЛР1 к ЛР2", "Модель TO BE → данные → модель. Что делать, если датасета нет")

# ========================= 24. Reverse task
s = content("Если подходящего датасета нет, модель TO BE подсказывает, какие переменные собрать",
            src=["Контекст: «Примеры проблемных областей в промышленности» (материалы курса)  ·  ",
                 {"text": "Colab: 05_reverse_task_synthetic_dataset", "link": colab_link("05_reverse_task_synthetic_dataset"), "c": PURPLE}],
            note="Обратная задача: не «что можно найти в данных», а «какие данные нужны, чтобы принять решение в шлюзе TO BE». "
                 "Генерируем правдоподобный CSV с заданным скрытым законом, затем проверяем, что сценарий из 10 шагов его находит.")
fl = [("BPMN TO BE", "шлюз «Нужен внеплановый осмотр факела?»"), ("Переменные", "что влияет на решение — со знаком и единицами"),
      ("Генератор", "Python или LLM создаёт CSV со скрытым законом"), ("Проверка", "10 шагов: модель должна найти закон")]
w, gap = 2.85, 0.3
for i, (t, d) in enumerate(fl):
    x = 0.5 + i * (w + gap)
    card(s, x, 1.9, w, 1.35, [{"runs": [{"text": t, "b": True, "s": 17, "c": DARK}], "after": 4}, {"runs": [{"text": d, "s": 14, "c": GREY}]}],
         fill=LPURPLE if i == 0 else LIGHT, pad=0.14, anchor=MSO_ANCHOR.MIDDLE)
    if i < 3:
        arrow(s, x + w + 0.05, 2.45, 0.2, 0.26)
rows = [["Переменная", "Смысл и единицы", "Ожидаемое влияние на «осмотр нужен»"],
        ["tilt_x_deg, tilt_y_deg", "крен ствола по двум осям, °", "+ сильное (через полный угол крена)"],
        ["wind_ms", "скорость ветра, м/с", "+"],
        ["days_since_inspection", "дней с последнего осмотра", "+"],
        ["flare_load_pct", "нагрузка факела, %", "+"],
        ["ch4_ppm", "метан у основания, ppm", "+ (логарифм)"],
        ["air_temp_c", "температура воздуха, °C", "− слабое"],
        ["so2_ppm", "SO₂, ppm", "0 — контрольная «пустышка»"]]
table(s, 0.5, 3.5, 12.3, 3.15, rows, colw=[3.2, 4.0, 5.1], size=14, row_h=0.39, first_bold=True)

# ========================= 25. Synthetic results
fw = D["flare_w"]
order = ["tilt_total", "wind_ms", "days_since_inspection", "flare_load_pct", "ch4_ppm", "so2_ppm", "air_temp_c"]
rus = {"tilt_total": "крен", "wind_ms": "ветер", "days_since_inspection": "давность осмотра", "flare_load_pct": "нагрузка факела",
       "ch4_ppm": "метан", "so2_ppm": "SO₂ (пустышка)", "air_temp_c": "температура"}
s = content("Синтетический датасет проверяет постановку: модель восстановила заложенные зависимости",
            note="3000 строк, 58,3% «осмотр нужен». В данные специально внесены 15 сбоев датчика и по 60 пропусков в ветре и метане — "
                 "студенты отрабатывают очистку. Accuracy 0,751 против базовой 0,582, ROC-AUC 0,789. "
                 "Важно: синтетика проверяет логику и набор переменных, но не заменяет реальные данные.")
cd = CategoryChartData(); cd.categories = [rus[k] for k in order]; cd.add_series("Сила влияния |вес|", [abs(fw[k]) for k in order])
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, I(0.5), I(1.85), I(7.0), I(4.8), cd); ch = gf.chart
style_chart(ch); pl = ch.plots[0]; pl.gap_width = 45; pl.has_data_labels = True; pl.data_labels.font.size = Pt(15)
pl.data_labels.number_format = '0.00;-0.00'; pl.data_labels.number_format_is_linked = False
for i, k in enumerate(order):
    pt = pl.series[0].points[i]; pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = GREEN if fw[k] > 0.1 else (ORANGE if fw[k] < 0 else RGBColor(0xB9, 0xC2, 0xBB))
    if fw[k] < 0:
        tf_ = pt.data_label.text_frame; tf_.text = "−" + f"{abs(fw[k]):.2f}"
        tf_.paragraphs[0].runs[0].font.size = Pt(15); tf_.paragraphs[0].runs[0].font.color.rgb = ORANGE
        pt.data_label.position = XL_LABEL_POSITION.OUTSIDE_END
ch.category_axis.reverse_order = True; ch.category_axis.tick_labels.font.size = Pt(15); axis_line(ch.category_axis)
from pptx.enum.chart import XL_TICK_LABEL_POSITION
ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
va = ch.value_axis; va.minimum_scale = 0.0; va.maximum_scale = 1.0; va.major_unit = 0.2; gridlines(va); va.format.line.fill.background(); va.tick_labels.font.size = Pt(14)
va.tick_labels.number_format = '0.0'; va.tick_labels.number_format_is_linked = False
ch.has_title = True; ch.chart_title.text_frame.text = "Сила влияния (|вес| модели); оранжевый — влияние со знаком минус"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(15); ch.chart_title.text_frame.paragraphs[0].runs[0].font.name = F_SEMI
card(s, 7.85, 1.9, 4.95, 1.4, [{"runs": [{"text": "0,751", "s": 34, "c": GREEN, "f": F_SEMI}, {"text": "  против 0,582", "s": 18, "c": GREY}], "after": 0},
                              {"runs": [{"text": "accuracy модели и базовой линии, ROC-AUC 0,789", "s": 14, "c": GREY}]}], fill=LIGHT2, pad=0.14, anchor=MSO_ANCHOR.MIDDLE)
card(s, 7.85, 3.5, 4.95, 3.15, [
    {"runs": [{"text": "Что доказано", "b": True, "s": 17}], "after": 6},
    {"runs": ["Знаки и порядок влияния совпали с заложенными: крен, затем ветер, давность осмотра, нагрузка."], "bullet": True, "s": 15},
    {"runs": ["SO₂ ≈ 0 — модель не нашла связь там, где её нет."], "bullet": True, "s": 15},
    {"runs": ["Набор переменных достаточен для шлюза TO BE — можно планировать сбор реальных данных."], "bullet": True, "s": 15}], fill=LIGHT)

# ========================= 26. Interactive
s = content("Работа с аудиторией: за 7 минут превращаем ваш процесс TO BE в датасет",
            note="Интерактив. Группы по профилям. Каждая называет шлюз TO BE из своей ЛР1, 5–7 переменных со знаком влияния и целевую переменную. "
                 "Преподаватель вставляет ответ в шаблон запроса и генерирует CSV прямо на лекции, затем запускает блокнот 05.")
steps = [("1 мин", "Назовите шлюз TO BE", "Какое решение «да / нет» принимается по данным?"),
         ("3 мин", "Перечислите 5–7 переменных", "Единицы, диапазон, знак влияния, одна «пустышка»."),
         ("1 мин", "Задайте цель и метрику", "Что дороже: пропуск или ложная тревога?"),
         ("2 мин", "Генерируем и проверяем", "Запрос к LLM → CSV → блокнот 05 → вывод.")]
for i, (tm, t, d) in enumerate(steps):
    y = 1.9 + i * 1.18
    card(s, 0.5, y, 1.3, 1.02, [[{"text": tm, "b": True, "s": 17, "c": WHITE}]], fill=GREEN, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, pad=0.05)
    card(s, 1.95, y, 4.6, 1.02, [{"runs": [{"text": t, "b": True, "s": 16}], "after": 2}, {"runs": [{"text": d, "s": 14, "c": GREY}]}],
         fill=LIGHT2, pad=0.12, anchor=MSO_ANCHOR.MIDDLE)
code(s, 6.85, 1.9, 5.95, 4.75,
     "Шаблон запроса к LLM:\n\n"
     "Сгенерируй Python-код, создающий CSV на 3000 строк\n"
     "для процесса «<шлюз TO BE>».\n"
     "Переменные: <имя, единицы, диапазон, распределение>.\n"
     "Целевая переменная <имя> (0/1) задаётся через\n"
     "логистическую функцию: <знак и сила влияния>.\n"
     "Добавь 1 переменную без влияния, 2% пропусков\n"
     "и 0,5% сбоев датчика. Зафиксируй seed.\n"
     "Выведи таблицу «заложенные зависимости».", size=13)

# ========================= 27. GitHub raw link
s = content("Ссылка на датасет через GitHub делает ваш Colab воспроизводимым у проверяющего",
            src=["Требование Задания 7 ЛР2 в курсе  ·  ", {"text": "пример: data/ в репозитории лекции", "link": REPO + "/tree/main/data", "c": PURPLE}],
            note="Локальный путь /content/file.csv у проверяющего не откроется — после перезапуска среды файл исчезает. "
                 "Raw-ссылка с GitHub работает всегда и позволяет автоматизировать проверку.")
gs = [("1", "Создайте репозиторий", "github.com → New → Public"), ("2", "Загрузите файл", "Add file → Upload files → CSV / XLSX"),
      ("3", "Откройте файл и нажмите Raw", "адрес вида raw.githubusercontent.com/…"), ("4", "Вставьте ссылку в Colab", "pd.read_csv(URL) или pd.read_excel(URL)")]
for i, (n, t, d) in enumerate(gs):
    y = 1.9 + i * 1.18
    card(s, 0.5, y, 0.8, 1.02, [[{"text": n, "s": 26, "c": WHITE, "f": F_SEMI}]], fill=DARK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, pad=0.02)
    card(s, 1.45, y, 5.0, 1.02, [{"runs": [{"text": t, "b": True, "s": 16}], "after": 2}, {"runs": [{"text": d, "s": 14, "c": GREY}]}],
         fill=LIGHT2, pad=0.12, anchor=MSO_ANCHOR.MIDDLE)
code(s, 6.8, 1.9, 6.0, 2.6,
     "# так НЕ работает у проверяющего:\n"
     "df = pd.read_csv('/content/my_data.csv')\n\n"
     "# так работает у всех:\n"
     "URL = ('https://raw.githubusercontent.com/'\n"
     "       'login/repo/main/data/my_data.csv')\n"
     "df = pd.read_csv(URL)", size=13)
card(s, 6.8, 4.7, 6.0, 1.95, [
    {"runs": [{"text": "Проверьте себя", "b": True, "s": 16}], "after": 6},
    {"runs": ["Ссылка открывается в браузере как «голый» текст / скачивает файл."], "bullet": True, "s": 14},
    {"runs": ["Среда выполнения → Перезапустить и выполнить все — без ошибок."], "bullet": True, "s": 14}], fill=LIGHT)

# ========================= 28. Typical errors
s = content("Типичные ошибки прошлых лет снижают оценку сильнее, чем простая модель",
            note="Ошибки взяты из разбора работ прошлых лет. Простая логистическая регрессия с честной оценкой лучше сложной модели без базовой линии.")
errs = [("Утечка ответа", "целевая переменная или её производная среди признаков: stab, writing score"),
        ("Нет базовой линии", "«accuracy 95%» при 95% одного класса — это ноль"),
        ("Только accuracy", "без матрицы ошибок и полноты по редкому классу"),
        ("Графики без выводов", "каждый график — гипотеза или ответ на вопрос"),
        ("Копия шаблона", "чужой датасет и текст без связи с вашим процессом ЛР1"),
        ("Локальный путь к файлу", "блокнот не запускается у проверяющего")]
for i, (t, d) in enumerate(errs):
    r, c = divmod(i, 3)
    x = 0.5 + c * 4.18; y = 1.95 + r * 2.4
    card(s, x, y, 3.94, 2.2, [{"runs": [{"text": f"{i+1}", "s": 30, "c": ORANGE, "f": F_SEMI}], "after": 2},
                              {"runs": [{"text": t, "b": True, "s": 17}], "after": 4},
                              {"runs": [{"text": d, "s": 14, "c": GREY}]}], fill=LIGHT2, pad=0.16)

# ========================= 29. Checklist
s = content("Чек-лист итога ЛР2: десять вопросов перед сдачей 14 декабря",
            note="Задание 7 ЛР2 — срок 14.12.2026. Визуализация, модель ML или простой интерфейс, выводы и ценность для бизнеса.")
chk = ["Сформулирован вопрос и решение из TO BE (ЛР1)", "Датасет загружен по raw-ссылке GitHub", "Есть паспорт: размер, типы, пропуски",
       "Очистка обоснована: что, сколько, почему", "Каждый график сопровождён выводом", "Целевая переменная и признаки названы явно, утечки нет",
       "Train / test, фиксированный random_state", "Модель сравнена с базовой линией", "Матрица ошибок, precision, recall — с интерпретацией",
       "Вывод на языке бизнеса: эффект для KPI из ССП"]
for i, t in enumerate(chk):
    c, r = divmod(i, 5)
    x = 0.5 + c * 6.25; y = 1.9 + r * 0.95
    card(s, x, y, 0.62, 0.8, [[{"text": f"{i+1}", "s": 18, "c": WHITE, "f": F_SEMI}]], fill=GREEN if i < 5 else DARK,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, pad=0.02)
    card(s, x + 0.75, y, 5.3, 0.8, [[t]], fill=LIGHT2, size=15, pad=0.14, anchor=MSO_ANCHOR.MIDDLE)

# ========================= FINAL (template slide 16) - move to end
fin = prs.slides[16]
for sh in fin.shapes:
    if sh.has_text_frame and "БЛАГОДАРЮ" in sh.text_frame.text:
        ps = sh.text_frame.paragraphs
        ps[0].runs[0].text = "СПАСИБО"
        for r in ps[0].runs[1:]:
            r._r.getparent().remove(r._r)
        if len(ps) > 1:
            ps[1].runs[0].text = "ЗА ВНИМАНИЕ"
            for r in ps[1].runs[1:]:
                r._r.getparent().remove(r._r)
qr("/tmp/qr/repo_w.png", REPO)
pq = fin.shapes.add_picture("/tmp/qr/repo_w.png", I(5.55), I(4.55), width=I(1.35)); pq.click_action.hyperlink.address = REPO
tb(fin, 7.05, 4.6, 5.2, 1.3, [[{"text": "Материалы лекции: блокноты, данные, схема Orange", "c": WHITE, "s": 14}],
                              [{"text": "github.com/alejanro85/uad-lecture7-ml", "c": WHITE, "s": 14, "f": F_SEMI}]], size=14)

# ========================= reorder: keep slide0 first, drop template slides 1..17 except 16, final last
sldIdLst = prs.slides._sldIdLst
ids = list(sldIdLst)
keep_first = ids[0]; final = ids[16]
drop = [e for k, e in enumerate(ids[:18]) if k not in (0, 16)]
for e in drop:
    rid = e.get(qn("r:id"))
    prs.part.drop_rel(rid)
    sldIdLst.remove(e)
sldIdLst.remove(final); sldIdLst.append(final)
prs.save("/home/user/workspace/lecture7/Лекция_7_Машинное_обучение_на_открытых_данных.pptx")
print("slides:", len(prs.slides))
