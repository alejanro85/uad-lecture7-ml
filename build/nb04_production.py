from nbb import *

nb = NB()
nb.md(HEADER.format(
    title="04. Производство: предиктивное обслуживание станков (AI4I 2020)",
    profile="Производственный и инновационный менеджмент",
    question="Можно ли по телеметрии станка (температуры, обороты, момент, износ инструмента) заранее выявлять отказы, чтобы перейти от ремонта «по факту» к ремонту «по состоянию»?",
    data=f"`ai4i2020.csv` — 10 000 записей телеметрии фрезерного станка, 3,4% отказов. Источник: [UCI ML Repository, AI4I 2020 Predictive Maintenance Dataset](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset), Matzka, 2020, CC BY 4.0.",
))
nb.md("""## Шаг 1. Вопрос, гипотеза, цена ошибки

* **Объект** — цикл работы станка; **цель** — `Machine failure` (1 — отказ).
* **Цена ошибки:** пропущенный отказ (FN) = простой линии + брак; ложная тревога (FP) = лишний осмотр. FN дороже → главная метрика **recall**.
* **H1:** отказы связаны с перегревом (малая разница температур), перегрузкой по мощности и износом инструмента.""")
nb.code(SETUP)
nb.md("## Шаги 2–3. Загрузка и паспорт данных")
nb.code(f'''df = pd.read_csv("{RAW}ai4i2020.csv")
print(df.shape, "| пропусков:", df.isna().sum().sum())
df.head()''')
nb.code('''df.describe().T.round(1)''')
nb.code('''print(df["Machine failure"].value_counts())
df[["TWF", "HDF", "PWF", "OSF", "RNF"]].sum().rename({"TWF": "износ инструмента", "HDF": "перегрев", "PWF": "мощность", "OSF": "перегрузка", "RNF": "случайный"})''')
nb.md("**Вывод:** 10 000 записей без пропусков; отказов всего **339 (3,4%)** — сильный дисбаланс. Столбцы TWF…RNF — *типы* уже случившегося отказа: это **утечка ответа**, в признаки их брать нельзя. UDI и Product ID — идентификаторы.")

nb.md("## Шаг 4. Подготовка: убираем идентификаторы и утечку, кодируем категорию")
nb.code('''sensors = ["Air temperature [K]", "Process temperature [K]", "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]"]
X_raw = pd.get_dummies(df[["Type"] + sensors], columns=["Type"], drop_first=True, dtype=int)   # Type: L/M/H -> 0/1
y = df["Machine failure"]
X_raw.head()''')
nb.md("## Шаги 5–6. Разведка: где «живут» отказы?")
nb.code('''fig, ax = plt.subplots(1, 3, figsize=(15, 4))
sns.boxplot(data=df, x="Machine failure", y="Torque [Nm]", ax=ax[0])
sns.boxplot(data=df, x="Machine failure", y="Tool wear [min]", ax=ax[1])
sns.scatterplot(data=df.sample(4000, random_state=1), x="Rotational speed [rpm]", y="Torque [Nm]",
                hue="Machine failure", palette=["#c9d6ca", "#DA4927"], s=12, ax=ax[2])
ax[2].set_title("Отказы — на краях рабочей области")
plt.tight_layout(); plt.show()''')
nb.md("**Вывод:** отказы концентрируются при большом моменте, большом износе и на краях области «обороты × момент». Связь **нелинейная** — простая линейная модель на «сырых» датчиках её не увидит. Подскажем модели физику: пороги взяты из описания датасета (аналог паспорта оборудования и регламента ТОиР).")
nb.code('''df["power_W"] = df["Torque [Nm]"] * df["Rotational speed [rpm]"] * 2 * np.pi / 60   # мощность = момент × угловая скорость
df["dT_K"] = df["Process temperature [K]"] - df["Air temperature [K]"]                  # запас по теплу
df["strain"] = df["Tool wear [min]"] * df["Torque [Nm]"]                                # нагрузка на изношенный инструмент
df["power_out_of_range"] = ((df["power_W"] < 3500) | (df["power_W"] > 9000)).astype(int)
df["heat_risk"] = ((df["dT_K"] < 8.6) & (df["Rotational speed [rpm]"] < 1380)).astype(int)
X_fe = pd.concat([X_raw, df[["power_W", "dT_K", "strain", "power_out_of_range", "heat_risk"]]], axis=1)
df.groupby("heat_risk")["Machine failure"].mean().round(3)''')

nb.md("## Шаги 7–10. Модели и «парадокс точности»")
nb.code(ML_IMPORTS + "\n\n" + REPORT_FN + '''

res = {}
for name, X, cw in [("1. сырые датчики", X_raw, None),
                    ("2. + веса классов", X_raw, "balanced"),
                    ("3. + физ. признаки", X_fe, None),
                    ("4. физ. признаки + веса", X_fe, "balanced")]:
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, class_weight=cw)).fit(X_tr, y_tr)
    p = m.predict(X_te); res[name] = confusion_matrix(y_te, p)
    quality(y_te, p, m.predict_proba(X_te)[:, 1], name=name)
quality(y_te, np.zeros_like(y_te), name="Базовая линия «отказов нет»")''')
nb.code('''fig, ax = plt.subplots(1, 4, figsize=(18, 4))
for a, (name, cm) in zip(ax, res.items()):
    ConfusionMatrixDisplay(cm, display_labels=["норма", "отказ"]).plot(ax=a, cmap="Greens", colorbar=False); a.set_title(name)
plt.tight_layout(); plt.show()''')
nb.md("## Бонус: кластеризация — типовые режимы работы (обучение без учителя)")
nb.code('''from sklearn.cluster import KMeans
Z = StandardScaler().fit_transform(df[["Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]"]])
df["regime"] = KMeans(n_clusters=4, n_init=10, random_state=42).fit_predict(Z)
df.groupby("regime").agg(n=("UDI", "size"), rpm=("Rotational speed [rpm]", "mean"), torque=("Torque [Nm]", "mean"),
                         wear=("Tool wear [min]", "mean"), failure_rate=("Machine failure", "mean")).round(3)''')
nb.md("""## Итоговые выводы для бизнеса

1. **Парадокс точности:** модель на сырых датчиках даёт 96,8% accuracy (≈ базовая линия 96,6%), но находит лишь **12 из 85** отказов в тесте — для цеха она бесполезна.
2. **Веса классов** поднимают recall до 0,80, но дают 420 ложных тревог из 2500 циклов.
3. **Физические признаки** (мощность, запас по теплу, нагрузка на инструмент) + веса: найдено **78 из 85 отказов (recall 0,92)** при 178 ложных тревогах; ROC-AUC 0,98. Без весов — 59 из 85 и **ни одной ложной тревоги** (precision 1,0).
4. **Управленческий выбор:** вариант 3 — «осмотр только по надёжному сигналу», вариант 4 — «не пропустить отказ». Выбор определяется соотношением стоимости простоя и осмотра — это задача менеджера, а не алгоритма.
5. **Кластеризация** выделяет режимы работы с разной частотой отказов → основа для норм эксплуатации и графика ТОиР.

**Ограничения:** датасет синтетический (построен по реальной логике отказов), для внедрения — данные своего оборудования (MES/SCADA).""")
nb.save("/home/user/workspace/lecture7/notebooks/04_production_predictive_maintenance.ipynb")
print("ok")
