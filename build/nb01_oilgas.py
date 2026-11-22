from nbb import *

nb = NB()
nb.md(HEADER.format(
    title="01. Нефтегаз: тренды цены Brent и обнаружение нефтяных разливов",
    profile="Менеджмент в нефтегазе",
    question="(А) Какие тренды и режимы волатильности видны в цене Brent и можно ли «угадать» направление цены? (Б) Можно ли автоматически отбирать радарные снимки с вероятным нефтяным пятном, чтобы аналитик проверял не все снимки, а только подозрительные?",
    data=f"(А) `brent-daily.csv` — ежедневная цена Brent, $/барр., 1987–2026 (EIA через [datasets/oil-prices](https://github.com/datasets/oil-prices), лицензия ODC-PDDL; снимок на 17.11.2026). (Б) `oil-spill.csv` — 937 фрагментов спутниковых радарных (SAR) снимков, 48 числовых признаков пятна и метка «нефть / не нефть» (Kubat et al., 1998; [зеркало](https://github.com/jbrownlee/Datasets)).",
))

nb.md("# Часть А. Цена Brent: разведка временного ряда\n\n## Шаг 1. Вопрос и гипотеза\n* Как менялись уровень и **волатильность** цены по годам? Где «кризисные режимы»?\n* Гипотеза H0 (скептическая): по прошлым ценам направление цены через месяц предсказать нельзя лучше, чем «всегда расти».")
nb.code(SETUP)
nb.md("## Шаг 2–3. Загрузка и паспорт данных")
nb.code(f'''brent = pd.read_csv("{RAW}brent-daily.csv", parse_dates=["Date"])
print(brent.shape)
brent.info()
brent.describe().round(1)''')
nb.md("**Вывод:** ~9100 торговых дней, 2 столбца (дата, цена), пропусков нет. Пропущенные даты — выходные: это не ошибка, а свойство биржевых данных.")
nb.md("## Шаг 4–5. Подготовка и разведка: тренд и скользящее среднее")
nb.code('''s = brent.set_index("Date")["Price"]
fig, ax = plt.subplots(figsize=(13, 4))
s.plot(ax=ax, lw=0.6, color="#7a808b", label="Brent, день")
s.rolling(250).mean().plot(ax=ax, lw=2, color="#37B34A", label="скользящее среднее 250 дней (≈ год)")
ax.set_ylabel("$/барр."); ax.legend(); ax.set_title("Цена Brent, 1987–2026")
plt.show()''')
nb.code('''yearly = pd.DataFrame({
    "средняя цена": s.resample("YE").mean(),
    "волатильность, % годовых": s.pct_change().groupby(s.index.year).std().values * np.sqrt(252) * 100,
})
yearly.index = yearly.index.year
yearly.round(1).tail(12)''')
nb.code('''ax = yearly["волатильность, % годовых"].plot.bar(figsize=(13, 3.5), color="#244128")
ax.set_title("Годовая волатильность доходности Brent, %"); plt.show()''')
nb.md("**Вывод по шагам 4–5:** длинный тренд прерывается шоками (2008, 2014–2016, 2020, 2022). В 2026 г. волатильность — максимальная с 2020 г. (≈ 71% годовых против 27–34% в 2023–2025): цена выросла с ~61 $ в январе до ~138 $ в апреле. Для бизнеса это аргумент за хеджирование и сценарное планирование бюджета.")

nb.md("## Шаги 6–10. Можно ли предсказать направление цены через 4 недели?\n\nПризнаки: изменение за 1 и 4 недели, отклонение от 12-недельного среднего. Цель: **1 — цена через 4 недели выше**. Для временных рядов делим выборку **по времени** (прошлое → обучение, будущее → тест), а не случайно!")
nb.code(ML_IMPORTS + '''

w = s.resample("W").last()
d = pd.DataFrame({"chg_1w": w.pct_change(), "chg_4w": w.pct_change(4), "vs_ma12": w / w.rolling(12).mean() - 1})
d["target_up"] = (w.shift(-4) > w).astype(int)
d = d.dropna().iloc[:-4]          # последние 4 недели без «ответа» отбрасываем
cut = int(len(d) * 0.75)          # разбиение по времени
train, test = d.iloc[:cut], d.iloc[cut:]
X_cols = ["chg_1w", "chg_4w", "vs_ma12"]
m = LogisticRegression().fit(train[X_cols], train["target_up"])
acc_model = accuracy_score(test["target_up"], m.predict(test[X_cols]))
acc_base = max(test["target_up"].mean(), 1 - test["target_up"].mean())
print(f"Тест с {test.index[0].date()} по {test.index[-1].date()}")
print(f"Базовая линия («всегда вверх»): {acc_base:.3f}   Логистическая регрессия: {acc_model:.3f}")''')
nb.md("**Вывод:** точность модели ≈ 56% и практически равна базовой линии ≈ 55% — **модель не лучше монетки**. Это тоже научный результат: рынок нефти «слабо эффективен», и прошлые цены сами по себе не дают преимущества. Менеджеру полезнее моделировать *риски* (волатильность, сценарии), а не «угадывать» цену. Честно показанный отрицательный результат ценнее красивой, но ложной точности.")

nb.md("# Часть Б. Классификация: нефтяное пятно на радарном снимке\n\n## Шаг 1. Вопрос\nСпутник (SAR) видит тёмные пятна на воде; лишь часть из них — нефть (остальное — штиль, водоросли, «двойники»). **Пропустить разлив (FN) намного дороже**, чем проверить ложную тревогу (FP) → главная метрика — **recall** класса «нефть».")
nb.md("## Шаги 2–4. Загрузка, паспорт, подготовка")
nb.code(f'''spill = pd.read_csv("{RAW}oil-spill.csv", header=None)
spill.columns = ["patch"] + [f"f{{i}}" for i in range(1, 49)] + ["oil"]
print(spill.shape)
print("Пропусков:", spill.isna().sum().sum())
spill["oil"].value_counts()''')
nb.md("**Вывод:** 937 пятен, лишь **41 (4,4%)** — нефть. Сильный **дисбаланс классов**: модель «всегда не нефть» получит 95,6% accuracy и не найдёт ни одного разлива. Столбец `patch` — номер снимка (идентификатор), в модель его не берём.")
nb.md("## Шаги 5–6. Разведка: чем нефтяные пятна отличаются?")
nb.code('''X = spill.drop(columns=["patch", "oil"]); y = spill["oil"]
# стандартизованная разница средних (нефть vs не нефть): какие признаки разделяют классы
eff = ((X[y == 1].mean() - X[y == 0].mean()) / X.std()).abs().sort_values(ascending=False)
eff.head(10).plot.barh(figsize=(7, 4), color="#37B34A"); plt.gca().invert_yaxis()
plt.title("Признаки, сильнее всего отличающие нефть (|d| Коэна)"); plt.show()''')
nb.md("**Вывод:** несколько признаков (форма, контраст, площадь пятна) заметно отличают нефть → задача имеет смысл для ML.")
nb.md("## Шаги 7–10. Модель, базовая линия, учёт дисбаланса")
nb.code(REPORT_FN + '''

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
base = DummyClassifier(strategy="most_frequent").fit(X_tr, y_tr)
quality(y_te, base.predict(X_te), name="Базовая линия")

m1 = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)).fit(X_tr, y_tr)
quality(y_te, m1.predict(X_te), m1.predict_proba(X_te)[:, 1], name="Лог. регрессия")

m2 = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, class_weight="balanced")).fit(X_tr, y_tr)
quality(y_te, m2.predict(X_te), m2.predict_proba(X_te)[:, 1], name="Лог. регрессия + веса классов")''')
nb.code('''fig, ax = plt.subplots(1, 2, figsize=(10, 4))
for a, (mdl, t) in zip(ax, [(m1, "обычная"), (m2, "class_weight='balanced'")]):
    ConfusionMatrixDisplay(confusion_matrix(y_te, mdl.predict(X_te)), display_labels=["не нефть", "нефть"]).plot(ax=a, cmap="Greens", colorbar=False)
    a.set_title(t)
plt.tight_layout(); plt.show()''')
nb.md("""## Итоговые выводы для бизнеса

1. **Brent:** данные полезны для оценки *рисков* (волатильность 2026 г. ≈ 71% годовых — в 2+ раза выше 2023–2025), но не для «угадывания» цены: модель ≈ базовая линия.
2. **Разливы:** обычная модель по accuracy (96%) почти не отличается от «всегда нет», а находит лишь 4 из 10 разливов в тесте. **Взвешивание классов** поднимает recall до **0,9 (9 из 10)** ценой 24 ложных тревог из 235 снимков — аналитик смотрит ~14% снимков вместо 100%.
3. **Управленческий эффект:** сокращение ручного просмотра в ~7 раз при сохранении 90% обнаружения; порог тревоги — решение менеджера (цена пропуска vs цена проверки).

**Ограничения:** малая выборка разливов (41), признаки обезличены; перед внедрением — проверка на снимках своего региона.""")
nb.save("/home/user/workspace/lecture7/notebooks/01_oilgas_brent_oilspill.ipynb")
print("ok")
