"""Блокнот 06: веб-формы прямо в Colab (Colab Forms, ipywidgets, Gradio)."""
from nbb import NB, COLAB

nb = NB()
nb.md(f"""
# 06. Веб-формы для наглядной иллюстрации модели — прямо в Colab

**Зачем.** Руководителю не нужен код — ему нужна форма: ввёл параметры объекта → увидел вероятность и решение.
Здесь три способа сделать такую форму, от простого к сложному. Все работают на тех же кейсах и тем же конвейером, что блокноты 00–05.

| Способ | Что нужно | Кому показать |
|---|---|---|
| 1. Colab Forms (`#@param`) | ничего не устанавливать | себе и группе на занятии |
| 2. ipywidgets (`interact`) | ничего не устанавливать | на занятии: ползунок порога «вживую» |
| 3. Gradio | `pip install gradio` | любому человеку по временной публичной ссылке |

Постоянные варианты (без Colab): статическая страница GitHub Pages и приложение Streamlit — см. папку `webapps/` репозитория.

[Открыть этот блокнот в Colab]({COLAB}06_web_forms_gradio.ipynb)
""")

nb.md("## Шаг 0. Загружаем описание кейсов и обучаем модель\n\nФайл `cases.py` — общий для всех веб-форм: в нём загрузка, очистка, целевая переменная и подписи признаков по-русски.")
nb.code('''import urllib.request, importlib, sys
URL = "https://raw.githubusercontent.com/alejanro85/uad-lecture7-ml/main/webapps/streamlit_app/cases.py"
urllib.request.urlretrieve(URL, "cases.py")
import cases; importlib.reload(cases)
from cases import CASES, fit_case, confusion

CASE_KEY = "students"  #@param ["students", "grid", "concrete", "ai4i", "flare"]
case = CASES[CASE_KEY]
R = fit_case(case)
print(case.title)
print("Вопрос:", case.question)
print("Событие (класс 1):", case.event, "| тестовых объектов:", len(R["y_te"]))''')

nb.md("""
## Способ 1. Colab Forms: форма без единой библиотеки

Комментарий `#@param` превращает переменную в поле формы (ползунок, список). Справа от кода в Colab появится форма;
после изменения значения ячейка перезапускается. Ниже — форма для кейса students.
""")
nb.code('''import pandas as pd
cs = CASES["students"]; Rs = fit_case(cs)

math_score = 55  #@param {type:"slider", min:0, max:100, step:1}
reading_score = 52  #@param {type:"slider", min:0, max:100, step:1}
test_preparation = "none"  #@param ["none", "completed"]
lunch = "free/reduced"  #@param ["standard", "free/reduced"]
gender = "male"  #@param ["female", "male", "unknown"]
parental = "high school"  #@param ["some high school", "high school", "some college", "associate's degree", "bachelor's degree", "master's degree", "unknown"]
group = "group A"  #@param ["group A", "group B", "group C", "group D", "group E"]
threshold = 0.5  #@param {type:"slider", min:0.05, max:0.95, step:0.05}

student = pd.DataFrame([{"math score": math_score, "reading score": reading_score, "gender": gender,
                         "parental level of education": parental, "lunch": lunch,
                         "test preparation course": test_preparation, "class_group": group}])
p = Rs["model"].predict_proba(student)[0, 1]
print(f"Вероятность «не сдаст»: {p:.1%}")
print("Решение:", "пригласить на консультацию" if p >= threshold else "консультация не нужна")''')

nb.md("""
## Способ 2. ipywidgets: ползунок порога и матрица несоответствий «вживую»

`interact` строит ползунок по диапазону. Удобно на лекции: двигаем порог — и сразу видно, как меняются найденные и ложные тревоги.
""")
nb.code('''import matplotlib.pyplot as plt
from ipywidgets import interact, FloatSlider

def show(threshold=0.5):
    m = confusion(R["y_te"], R["proba"], threshold)
    fig, ax = plt.subplots(figsize=(4.6, 3.6))
    grid = [[m["tp"], m["fn"]], [m["fp"], m["tn"]]]
    ax.imshow([[1, 0.15], [0.3, 0.6]], cmap="Greens", vmin=0, vmax=1)
    names = [["найдены", "пропуск"], ["ложная тревога", "верно"]]
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{grid[i][j]}\\n{names[i][j]}", ha="center", va="center", fontsize=12,
                    color="white" if (i, j) == (0, 0) else "black")
    ax.set_xticks([0, 1], [f"модель: {case.event}", f"модель: {case.no_event}"])
    ax.set_yticks([0, 1], [f"факт: {case.event}", f"факт: {case.no_event}"])
    ax.set_title(f"Порог {threshold:.2f}: precision {m['precision']:.2f}, recall {m['recall']:.2f}")
    plt.show()

interact(show, threshold=FloatSlider(value=0.5, min=0.05, max=0.95, step=0.05, description="Порог"));''')

nb.md("""
## Способ 3. Gradio: веб-форма с публичной ссылкой

Gradio строит веб-страницу из обычной функции Python. Поля формы ниже создаются **автоматически** из описания кейса:
числовые признаки → ползунки (1–99 перцентиль данных), категории → выпадающие списки.
`launch(share=True)` выдаёт временную публичную ссылку вида `https://….gradio.live` — её можно отправить в чат группы или вывести QR-кодом.
Ссылка работает, пока запущена ячейка.
""")
nb.code('''!pip -q install gradio''')
nb.code('''import gradio as gr
import pandas as pd

def make_demo(case, R):
    X = R["X"]; comps = []
    for c in case.num:
        lo, hi = float(X[c].quantile(0.01)), float(X[c].quantile(0.99))
        comps.append(gr.Slider(lo, hi, value=float(X[c].median()), label=case.labels.get(c, c)))
    for c in case.cat:
        vals = sorted(X[c].astype(str).unique())
        comps.append(gr.Dropdown(vals, value=str(X[c].mode()[0]), label=case.labels.get(c, c)))
    thr = gr.Slider(0.05, 0.95, value=0.5, step=0.05, label="Порог решения")

    def predict(*vals):
        *feats, t = vals
        row = pd.DataFrame([dict(zip(case.num + case.cat, feats))])
        p = float(R["model"].predict_proba(row)[0, 1])
        decision = case.event if p >= t else case.no_event
        m = confusion(R["y_te"], R["proba"], t)
        text = (f"### Решение: {decision}\\n"
                f"При пороге {t:.2f} на тестовой выборке модель находит {m['tp']} из {m['tp'] + m['fn']} "
                f"случаев «{case.event}» и даёт {m['fp']} ложных тревог.\\n\\n"
                f"Ложная тревога — {case.fp_text}; пропуск — {case.fn_text}.")
        return {case.event: p, case.no_event: 1 - p}, text

    return gr.Interface(fn=predict, inputs=comps + [thr],
                        outputs=[gr.Label(label="Вероятность"), gr.Markdown()],
                        title=case.title, description=f"**Вопрос:** {case.question}",
                        flagging_mode="never")

demo = make_demo(case, R)
print("Форма готова:", len(case.num) + len(case.cat), "полей")''')
nb.code('''demo.launch(share=True)   # ссылка *.gradio.live появится ниже; остановить — кнопка «стоп» у ячейки''')

nb.md("""
## Как сделать такую форму для своего датасета ЛР2

1. Загрузите CSV в свой репозиторий GitHub и возьмите raw-ссылку (как в лекции).
2. Скопируйте ячейку способа 3 и замените `case.num`, `case.cat` на списки своих признаков, а `R["model"]` — на свою обученную модель.
3. Либо попросите LLM написать форму по шаблону промпта из файла `webapps/PROMPTS.md` репозитория.

**Проверка перед показом:** форма должна давать ту же вероятность, что `model.predict_proba` в блокноте, на 2–3 строках тестовой выборки.
""")
nb.save("/home/user/workspace/lecture7/notebooks/06_web_forms_gradio.ipynb")
print("ok")
