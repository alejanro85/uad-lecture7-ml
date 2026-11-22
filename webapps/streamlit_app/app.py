"""Веб-сервис «От данных к решению»: разведка, модель, порог и форма «что если».

Запуск локально:   pip install -r requirements.txt && streamlit run app.py
Запуск в облаке:   share.streamlit.io → New app → репозиторий alejanro85/uad-lecture7-ml,
                   файл webapps/streamlit_app/app.py
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.metrics import roc_auc_score, roc_curve

from cases import CASES, Case, confusion, fit_case

GREEN, DARK, PURPLE, ORANGE, GREY = "#37B34A", "#244128", "#724796", "#DA4927", "#B9C2BB"
st.set_page_config(page_title="От данных к решению", layout="wide")
st.markdown(
    "<style>h1,h2,h3{color:#244128} .stMetric{background:#F2F5F2;border-radius:8px;padding:8px 12px}</style>",
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Загружаю данные и обучаю модель…")
def get(key: str, uploaded: bytes | None = None, target: str | None = None, pos: str | None = None):
    if key == "upload":
        import io
        df = pd.read_csv(io.BytesIO(uploaded))
        df = df.dropna(subset=[target]).reset_index(drop=True)
        feats = [c for c in df.columns if c != target]
        num = [c for c in feats if pd.api.types.is_numeric_dtype(df[c])]
        cat = [c for c in feats if c not in num and df[c].nunique() <= 30]
        for c in num:
            df[c] = df[c].fillna(df[c].median())
        for c in cat:
            df[c] = df[c].fillna("unknown").astype(str)
        case = Case(key="upload", title="Ваш датасет", profile="ЛР2", question="Ваш вопрос из шага 1",
                    source="загруженный файл", load=lambda: df,
                    target=lambda d: (d[target].astype(str) == pos).astype(int),
                    num=num, cat=cat, labels={}, event=str(pos), no_event="другое",
                    fp_text="ложная тревога", fn_text="пропуск события")
        return case, fit_case(case, df)
    case = CASES[key]
    return case, fit_case(case)


# ---------------- боковая панель ----------------
st.sidebar.title("От данных к решению")
st.sidebar.caption("Лекция 7 · Управление и аналитика данных на предприятии")
options = {k: f"{c.title}" for k, c in CASES.items()} | {"upload": "Загрузить свой CSV (для ЛР2)"}
key = st.sidebar.radio("Кейс", list(options), format_func=options.get)

if key == "upload":
    f = st.sidebar.file_uploader("CSV-файл", type="csv")
    if not f:
        st.info("Загрузите CSV, затем выберите целевую переменную и интересующее событие. Перед загрузкой удалите столбцы-идентификаторы и признаки-«подсказки ответа» (утечку).")
        st.stop()
    raw = pd.read_csv(f)
    target = st.sidebar.selectbox("Целевая переменная", raw.columns, index=len(raw.columns) - 1)
    pos = st.sidebar.selectbox("Событие (класс 1)", sorted(raw[target].dropna().astype(str).unique()))
    case, R = get("upload", f.getvalue(), target, pos)
else:
    case, R = get(key)

lab = lambda c: case.labels.get(c, c)
EC, NC = (GREEN, ORANGE) if case.event_is_good else (ORANGE, GREEN)       # цвет события / не-события
LE, LN = "#DCEFDD", "#FBE3DC"
if not case.event_is_good:
    LE, LN = LN, LE
df, y = R["df"], R["y"]

st.title(case.title)
st.markdown(f"**Шаг 1. Вопрос:** {case.question}  \n**Профиль:** {case.profile} · **Источник:** {case.source}")

t1, t2, t3, t4 = st.tabs(["Данные", "Разведка", "Модель и порог", "Форма «что если»"])

# ---------------- шаги 2–4 ----------------
with t1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Строк", f"{len(df):,}".replace(",", " "))
    c2.metric("Столбцов", df.shape[1])
    c3.metric(f"Доля «{case.event}»", f"{y.mean():.1%}")
    st.subheader("Первые строки")
    st.dataframe(df.head(10), width="stretch")
    st.subheader("Описательная статистика")
    st.dataframe(df[case.num].describe().T.round(2), width="stretch")

# ---------------- шаги 5–6 ----------------
with t2:
    d = df.assign(**{"класс": np.where(y == 1, case.event, case.no_event)})
    c1, c2 = st.columns(2)
    with c1:
        f_num = st.selectbox("Числовой признак", case.num, format_func=lab)
        fig = px.histogram(d, x=f_num, color="класс", barmode="overlay", opacity=0.7, nbins=40,
                           color_discrete_map={case.event: EC, case.no_event: NC},
                           labels={f_num: lab(f_num)})
        fig.update_layout(height=380, margin=dict(t=30, b=10), legend_title_text="")
        st.plotly_chart(fig, width="stretch")
    with c2:
        if case.cat:
            f_cat = st.selectbox("Категория", case.cat, format_func=lab)
            share = d.groupby(f_cat)["класс"].apply(lambda s: (s == case.event).mean()).reset_index(name="доля")
            fig = px.bar(share, x=f_cat, y="доля", text_auto=".0%", color_discrete_sequence=[PURPLE],
                         labels={f_cat: lab(f_cat), "доля": f"доля «{case.event}»"})
            fig.update_layout(height=380, margin=dict(t=30, b=10), yaxis_tickformat=".0%")
        else:
            corr = df[case.num].assign(y=y).corr()["y"].drop("y").sort_values()
            fig = px.bar(x=corr.values, y=[lab(c) for c in corr.index], orientation="h",
                         color=corr.values, color_continuous_scale=[NC, "#EEEEEE", EC], range_color=[-1, 1],
                         labels={"x": f"корреляция с «{case.event}»", "y": ""})
            fig.update_layout(height=380, margin=dict(t=30, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")

# ---------------- шаги 7–10 ----------------
with t3:
    y_te, proba = R["y_te"].values, R["proba"]
    base = max(y_te.mean(), 1 - y_te.mean())
    auc = roc_auc_score(y_te, proba)
    st.markdown(f"Тестовая выборка: **{len(y_te)}** объектов. Базовая линия «всегда большинство»: accuracy **{base:.3f}**. "
                f"ROC-AUC модели: **{auc:.3f}**.")
    thr = st.slider(f"Порог: считаем «{case.event}», если вероятность ≥", 0.05, 0.95, 0.50, 0.05)
    m = confusion(y_te, proba, thr)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Accuracy", f"{m['accuracy']:.3f}", f"{m['accuracy'] - base:+.3f} к базовой")
    c2.metric("Precision", f"{m['precision']:.3f}")
    c3.metric("Recall (полнота)", f"{m['recall']:.3f}")
    c4.metric(f"Найдено «{case.event}»", f"{m['tp']} из {m['tp'] + m['fn']}")

    left, right = st.columns([1, 1])
    with left:
        z = [[m["tp"], m["fn"]], [m["fp"], m["tn"]]]
        txt = [[f"{m['tp']}<br>найдены", f"{m['fn']}<br>пропуск"], [f"{m['fp']}<br>ложная тревога", f"{m['tn']}<br>верно"]]
        fig = go.Figure(go.Heatmap(z=[[1, 0.2], [0.35, 0.6]], text=txt, texttemplate="%{text}",
                                   colorscale=[[0, "#FBE3DC"], [0.5, "#DCEFDD"], [1, GREEN]], showscale=False,
                                   x=[f"модель: {case.event}", f"модель: {case.no_event}"],
                                   y=[f"факт: {case.event}", f"факт: {case.no_event}"], textfont=dict(size=18)))
        fig.update_layout(height=330, margin=dict(t=30, b=10), yaxis_autorange="reversed",
                          title="Матрица несоответствий")
        st.plotly_chart(fig, width="stretch")
    with right:
        st.markdown("**Цена ошибок для бизнеса**")
        a, b = st.columns(2)
        cfp = a.number_input(f"Ложная тревога: {case.fp_text}", 0.0, 1000.0, float(case.cost_fp), 1.0)
        cfn = b.number_input(f"Пропуск: {case.fn_text}", 0.0, 1000.0, float(case.cost_fn), 1.0)
        grid = np.round(np.arange(0.05, 0.96, 0.05), 2)
        costs = [confusion(y_te, proba, t)["fp"] * cfp + confusion(y_te, proba, t)["fn"] * cfn for t in grid]
        best = grid[int(np.argmin(costs))]
        fig = px.line(x=grid, y=costs, markers=True, labels={"x": "порог", "y": "суммарная цена ошибок"},
                      color_discrete_sequence=[DARK])
        fig.add_vline(x=thr, line_dash="dash", line_color=PURPLE)
        fig.add_vline(x=best, line_dash="dot", line_color=ORANGE)
        fig.update_layout(height=260, margin=dict(t=10, b=10))
        st.plotly_chart(fig, width="stretch")
        st.caption(f"Пунктир — выбранный порог; точки — порог минимальной цены ({best:.2f}).")

    coef = R["coef"].sort_values()
    fig = px.bar(x=coef.values, y=[lab(c) for c in coef.index], orientation="h",
                 color=np.where(coef.values > 0, f"повышает вероятность «{case.event}»", f"снижает вероятность «{case.event}»"),
                 color_discrete_map={f"повышает вероятность «{case.event}»": EC, f"снижает вероятность «{case.event}»": NC},
                 labels={"x": f"вес (стандартизованный) для «{case.event}»", "y": ""})
    fig.update_layout(height=max(300, 26 * len(coef)), margin=dict(t=30, b=10), legend_title_text="",
                      title="Какие признаки двигают вероятность")
    st.plotly_chart(fig, width="stretch")

# ---------------- форма «что если» ----------------
with t4:
    st.markdown("Задайте значения признаков — модель пересчитает вероятность события и решение при выбранном пороге.")
    X = R["X"]
    row = {}
    with st.form("whatif"):
        cols = st.columns(3)
        for i, c in enumerate(case.num + case.cat):
            with cols[i % 3]:
                if c in case.num:
                    lo, hi = float(X[c].quantile(0.01)), float(X[c].quantile(0.99))
                    med = float(X[c].median())
                    step = (hi - lo) / 100 or 1.0
                    row[c] = st.slider(lab(c), lo, hi, med, step)
                else:
                    vals = sorted(X[c].astype(str).unique())
                    mode = str(X[c].mode()[0])
                    row[c] = st.selectbox(lab(c), vals, index=vals.index(mode))
        thr_f = st.slider("Порог решения", 0.05, 0.95, 0.50, 0.05)
        ok = st.form_submit_button("Рассчитать", type="primary")
    if ok:
        p = float(R["model"].predict_proba(pd.DataFrame([row]))[0, 1])
        decision = case.event if p >= thr_f else case.no_event
        c1, c2, _ = st.columns([1, 1.3, 0.7])
        c1.metric(f"Вероятность «{case.event}»", f"{p:.1%}")
        c1.markdown(f"### Решение: {decision}")
        c1.caption(f"Ложная тревога: {case.fp_text}. Пропуск: {case.fn_text}.")
        fig = go.Figure(go.Indicator(mode="gauge+number", value=p * 100, number={"suffix": "%"},
                                     gauge={"axis": {"range": [0, 100]}, "bar": {"color": DARK},
                                            "steps": [{"range": [0, thr_f * 100], "color": LN},
                                                      {"range": [thr_f * 100, 100], "color": LE}],
                                            "threshold": {"line": {"color": ORANGE, "width": 4}, "value": thr_f * 100}}))
        fig.update_layout(height=230, margin=dict(t=20, b=10, l=30, r=30))
        c2.plotly_chart(fig, width="stretch")

st.sidebar.markdown("---")
st.sidebar.markdown("[Репозиторий лекции](https://github.com/alejanro85/uad-lecture7-ml)")
