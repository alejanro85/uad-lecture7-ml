"""Описание учебных кейсов лекции 7: откуда данные, как их чистить, что предсказываем.

Один файл используют три интерфейса:
  * Streamlit-приложение (webapps/streamlit_app/app.py);
  * форма Gradio в Colab (notebooks/06_web_forms_gradio.ipynb);
  * экспорт модели для статической страницы GitHub Pages (webapps/export_static.py).

Каждый кейс задаёт:
  load()      — загрузка и очистка (шаги 2–4 сценария);
  target      — как получить целевую переменную 0/1 (шаг 7);
  num / cat   — «сырые» признаки, которые человек вводит в веб-форму;
  engineer()  — инженерные признаки, вычисляемые из сырых (например, В/Ц);
  тексты      — что означают ошибки FP и FN для руководителя.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

RAW = "https://raw.githubusercontent.com/alejanro85/uad-lecture7-ml/main/data/"


@dataclass
class Case:
    key: str
    title: str
    profile: str
    question: str
    source: str
    load: Callable[[], pd.DataFrame]
    target: Callable[[pd.DataFrame], pd.Series]
    num: list[str]
    cat: list[str]
    labels: dict[str, str]                      # подписи признаков по-русски
    event: str                                  # что значит y = 1
    no_event: str                               # что значит y = 0
    fp_text: str                                # цена ложной тревоги
    fn_text: str                                # цена пропуска
    cost_fp: float = 1.0
    cost_fn: float = 5.0
    engineer: Callable[[pd.DataFrame], pd.DataFrame] = lambda d: d
    model_num: list[str] | None = None          # числовые признаки модели (после engineer)
    drop_from_model: list[str] = field(default_factory=list)
    event_is_good: bool = False                 # True, если класс 1 — желательный исход (бетон годен)
    stratify: Callable[[pd.DataFrame], pd.Series] | None = None   # как в блокноте (для совпадения разбиения)

    @property
    def features_num(self) -> list[str]:
        return self.model_num or self.num


# ---------- загрузчики (шаги 2–4) ----------

def _students() -> pd.DataFrame:
    df = pd.read_csv(RAW + "students.csv")
    df["math score"] = df["math score"].clip(lower=0)
    for c in ["math score", "reading score"]:
        df[c] = df[c].fillna(df[c].mean())
    for c in ["gender", "parental level of education"]:
        df[c] = df[c].fillna("unknown")
    df["lunch"] = df["lunch"].replace("standart", "standard")
    return df


def _grid() -> pd.DataFrame:
    return pd.read_csv(RAW + "grid_stability.csv")


def _concrete() -> pd.DataFrame:
    b = pd.read_excel(RAW + "Concrete_Data.xls")
    b.columns = ["cement", "slag", "fly_ash", "water", "superplast", "coarse_aggr",
                 "fine_aggr", "age_days", "strength_mpa"]
    return b.drop_duplicates().reset_index(drop=True)


def _ai4i() -> pd.DataFrame:
    return pd.read_csv(RAW + "ai4i2020.csv")


def _flare() -> pd.DataFrame:
    df = pd.read_csv(RAW + "flare_monitoring_synthetic.csv")
    df = df[df["tilt_x_deg"].abs() <= 10].copy()              # сбой датчика
    for c in ["wind_ms", "ch4_ppm"]:
        df[c] = df[c].fillna(df[c].median())
    return df.reset_index(drop=True)


# ---------- инженерные признаки ----------

def _eng_concrete(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["log_age"] = np.log(d["age_days"].clip(lower=1))
    d["w_c"] = d["water"] / d["cement"].clip(lower=1)
    return d


def _eng_flare(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["tilt_total"] = np.hypot(d["tilt_x_deg"], d["tilt_y_deg"])
    return d


CASES: dict[str, Case] = {
    "students": Case(
        key="students", title="Эталон: успеваемость студентов", profile="Все профили",
        question="Кого заранее пригласить на консультацию, чтобы не допустить провала письменной работы?",
        source="https://raw.githubusercontent.com/evgpat/stepik_from_idea_to_mvp/main/datasets/students.csv",
        load=_students, target=lambda d: (d["writing score"] < 50).astype(int),
        num=["math score", "reading score"],
        cat=["gender", "parental level of education", "lunch", "test preparation course", "class_group"],
        labels={"math score": "Балл по математике", "reading score": "Балл по чтению", "gender": "Пол",
                "parental level of education": "Образование родителей", "lunch": "Тип обеда",
                "test preparation course": "Подготовительный курс", "class_group": "Учебная группа"},
        event="не сдаст", no_event="сдаст",
        fp_text="лишнее приглашение на консультацию (час преподавателя)",
        fn_text="студент провалил работу без помощи (пересдача, риск отчисления)",
        cost_fp=1, cost_fn=8,
        stratify=lambda d: (d["writing score"] >= 50).astype(int),   # как в блокноте 00
    ),
    "grid": Case(
        key="grid", title="Энергетика: устойчивость электросети", profile="Менеджмент в энергетике",
        question="Перейдёт ли сеть в неустойчивый режим при текущих реакциях и мощностях участников?",
        source="https://archive.ics.uci.edu/dataset/471/electrical+grid+stability+simulated+data",
        load=_grid, target=lambda d: (d["stabf"] == "unstable").astype(int),
        num=["tau1", "tau2", "tau3", "tau4", "p2", "p3", "p4", "g1", "g2", "g3", "g4"], cat=[],
        labels={"tau1": "Время реакции производителя τ1, с", "tau2": "Время реакции τ2, с",
                "tau3": "Время реакции τ3, с", "tau4": "Время реакции τ4, с",
                "p2": "Мощность потребителя p2", "p3": "Мощность потребителя p3", "p4": "Мощность потребителя p4",
                "g1": "Эластичность цены g1", "g2": "Эластичность g2", "g3": "Эластичность g3", "g4": "Эластичность g4"},
        event="неустойчиво", no_event="устойчиво",
        fp_text="лишнее резервирование мощности",
        fn_text="неожиданное отклонение частоты, риск отключений",
        cost_fp=1, cost_fn=10,
    ),
    "concrete": Case(
        key="concrete", title="Строительство: приёмка бетона ≥ 30 МПа", profile="Менеджмент в девелопменте и строительстве",
        question="Наберёт ли замес прочность 30 МПа при данном составе и возрасте?",
        source="https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength",
        load=_concrete, target=lambda d: (d["strength_mpa"] >= 30).astype(int),
        num=["cement", "slag", "fly_ash", "water", "superplast", "coarse_aggr", "fine_aggr", "age_days"], cat=[],
        model_num=["cement", "slag", "fly_ash", "water", "superplast", "coarse_aggr", "fine_aggr", "log_age", "w_c"],
        engineer=_eng_concrete,
        labels={"cement": "Цемент, кг/м³", "slag": "Шлак, кг/м³", "fly_ash": "Зола-унос, кг/м³", "water": "Вода, кг/м³",
                "superplast": "Суперпластификатор, кг/м³", "coarse_aggr": "Щебень, кг/м³", "fine_aggr": "Песок, кг/м³",
                "age_days": "Возраст, сут.", "log_age": "log(возраст)", "w_c": "Водоцементное отношение В/Ц"},
        event="годен (≥ 30 МПа)", no_event="не годен",
        fp_text="принят слабый бетон (риск для конструкции, переделка)",
        fn_text="забракован годный замес (лишние испытания, простой)",
        cost_fp=10, cost_fn=1, event_is_good=True,
    ),
    "ai4i": Case(
        key="ai4i", title="Производство: отказ станка AI4I 2020", profile="Производственный и инновационный менеджмент",
        question="Откажет ли оборудование при текущих показаниях датчиков?",
        source="https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset",
        load=_ai4i, target=lambda d: d["Machine failure"].astype(int),
        num=["Air temperature [K]", "Process temperature [K]", "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]"],
        cat=["Type"],
        labels={"Air temperature [K]": "Температура воздуха, K", "Process temperature [K]": "Температура процесса, K",
                "Rotational speed [rpm]": "Скорость вращения, об/мин", "Torque [Nm]": "Крутящий момент, Н·м",
                "Tool wear [min]": "Износ инструмента, мин", "Type": "Класс изделия (L / M / H)"},
        event="отказ", no_event="норма",
        fp_text="лишняя остановка на осмотр",
        fn_text="внеплановый простой и брак",
        cost_fp=1, cost_fn=20,
    ),
    "flare": Case(
        key="flare", title="Нефтегаз: осмотр факельной установки (синтетика)", profile="Менеджмент в нефтегазе",
        question="Нужен ли внеплановый осмотр факела по данным датчиков? (шлюз TO BE из ЛР1)",
        source="https://github.com/alejanro85/uad-lecture7-ml/blob/main/notebooks/05_reverse_task_synthetic_dataset.ipynb",
        load=_flare, target=lambda d: d["inspection_needed"].astype(int),
        num=["tilt_x_deg", "tilt_y_deg", "wind_ms", "air_temp_c", "ch4_ppm", "so2_ppm", "flare_load_pct", "days_since_inspection"],
        cat=[],
        model_num=["tilt_total", "wind_ms", "air_temp_c", "ch4_ppm", "so2_ppm", "flare_load_pct", "days_since_inspection"],
        engineer=_eng_flare,
        labels={"tilt_x_deg": "Крен по оси X, °", "tilt_y_deg": "Крен по оси Y, °", "tilt_total": "Суммарный крен, °",
                "wind_ms": "Ветер, м/с", "air_temp_c": "Температура воздуха, °C", "ch4_ppm": "Метан CH₄, ppm",
                "so2_ppm": "SO₂, ppm", "flare_load_pct": "Нагрузка факела, %", "days_since_inspection": "Дней с осмотра"},
        event="осмотр нужен", no_event="осмотр не нужен",
        fp_text="лишний выезд бригады",
        fn_text="пропущена деформация конструкции (авария, штраф)",
        cost_fp=1, cost_fn=15,
    ),
}


def build_model(case: Case) -> Pipeline:
    """Шаг 9: тот же конвейер, что в блокнотах, — масштабирование + one-hot + логистическая регрессия."""
    pre = ColumnTransformer([
        ("num", StandardScaler(), case.features_num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), case.cat),
    ])
    return Pipeline([
        ("engineer", FunctionTransformer(case.engineer)),
        ("prep", pre),
        ("lr", LogisticRegression(max_iter=2000)),
    ])


def fit_case(case: Case, df: pd.DataFrame | None = None, seed: int = 42) -> dict:
    """Шаги 7–10: X/y, разбиение 75/25, обучение. Возвращает всё, что нужно интерфейсам."""
    df = case.load() if df is None else df
    y = case.target(df)
    X = df[case.num + case.cat]
    strat = case.stratify(df) if case.stratify else y
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=seed, stratify=strat)
    model = build_model(case).fit(X_tr, y_tr)
    proba = model.predict_proba(X_te)[:, 1]
    names = model.named_steps["prep"].get_feature_names_out()
    names = [n.split("__", 1)[1] for n in names]
    coef = pd.Series(model.named_steps["lr"].coef_[0], index=names)
    return dict(df=df, X=X, y=y, X_tr=X_tr, X_te=X_te, y_tr=y_tr, y_te=y_te,
                model=model, proba=proba, coef=coef)


def confusion(y_true, proba, thr: float) -> dict:
    """Матрица несоответствий при заданном пороге (событие = класс 1)."""
    y_true = np.asarray(y_true); pred = (np.asarray(proba) >= thr).astype(int)
    tp = int(((pred == 1) & (y_true == 1)).sum()); fn = int(((pred == 0) & (y_true == 1)).sum())
    fp = int(((pred == 1) & (y_true == 0)).sum()); tn = int(((pred == 0) & (y_true == 0)).sum())
    n = tp + fn + fp + tn
    return dict(tp=tp, fn=fn, fp=fp, tn=tn,
                accuracy=(tp + tn) / n,
                precision=tp / (tp + fp) if tp + fp else 0.0,
                recall=tp / (tp + fn) if tp + fn else 0.0)
