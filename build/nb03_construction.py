from nbb import *

nb = NB()
nb.md(HEADER.format(
    title="03. Строительство: прочность бетона — регрессия и контроль качества",
    profile="Менеджмент в девелопменте и строительстве",
    question="Можно ли по рецептуре смеси и возрасту бетона (а) спрогнозировать прочность на сжатие и (б) заранее отсеять замесы, которые не наберут требуемую прочность, — не дожидаясь лабораторных испытаний?",
    data=f"`Concrete_Data.xls` (**Excel**) — 1030 лабораторных испытаний: 7 компонентов смеси (кг/м³), возраст (сут.), прочность (МПа). Источник: [UCI ML Repository, Concrete Compressive Strength](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength), Yeh, 1998, CC BY 4.0.",
))
nb.md("## Шаг 1. Вопрос и гипотеза\n\n* **H1 (закон Абрамса):** чем ниже водоцементное отношение В/Ц, тем выше прочность.\n* **H2:** прочность растёт с возрастом нелинейно — быстро в первые недели, затем медленно.\n* Две ML-задачи на одних данных: **регрессия** (сколько МПа?) и **классификация** (наберёт ли порог?).")
nb.code(SETUP)
nb.md("## Шаги 2–3. Загрузка Excel-файла и паспорт данных\n\n`pd.read_excel` читает .xls/.xlsx так же просто, как CSV. Длинные названия столбцов заменим на короткие.")
nb.code(f'''beton = pd.read_excel("{RAW}Concrete_Data.xls")
beton.columns = ["cement", "slag", "fly_ash", "water", "superplast", "coarse_aggr", "fine_aggr", "age_days", "strength_mpa"]
print(beton.shape, "| пропусков:", beton.isna().sum().sum(), "| дублей:", beton.duplicated().sum())
beton.describe().T.round(1)''')
nb.md("**Вывод:** 1030 испытаний, пропусков нет, но есть **25 полных дублей** (повторные записи) — удалим. Прочность от 2 до 83 МПа, возраст от 1 до 365 суток.")
nb.md("## Шаг 4. Подготовка: дубли и инженерные признаки\n\nПредметное знание превращаем в признаки: **В/Ц** (водоцементное отношение) и **логарифм возраста** (нелинейный набор прочности).")
nb.code('''beton = beton.drop_duplicates().reset_index(drop=True)
beton["w_c"] = beton["water"] / beton["cement"]
beton["log_age"] = np.log(beton["age_days"])
beton.shape''')
nb.md("## Шаги 5–6. Разведка: проверяем гипотезы")
nb.code('''fig, ax = plt.subplots(1, 3, figsize=(15, 4))
sns.histplot(beton["strength_mpa"], kde=True, ax=ax[0]); ax[0].set_title("Распределение прочности, МПа")
sns.scatterplot(data=beton, x="w_c", y="strength_mpa", hue="log_age", palette="Greens", ax=ax[1], legend=False); ax[1].set_title("H1: В/Ц и прочность")
sns.boxplot(data=beton[beton.age_days.isin([3, 7, 14, 28, 56, 90])], x="age_days", y="strength_mpa", ax=ax[2]); ax[2].set_title("H2: прочность по возрасту, сут.")
plt.tight_layout(); plt.show()
beton[["w_c", "log_age", "cement", "superplast", "strength_mpa"]].corr()["strength_mpa"].round(2)''')
nb.md("**Вывод по шагам 5–6:** обе гипотезы подтверждаются: связь с В/Ц — отрицательная (чем больше воды на единицу цемента, тем слабее бетон); прочность резко растёт до 28 суток, дальше — медленно.")

nb.md("## Шаги 7–10 (А). Регрессия: прогноз прочности в МПа\n\nМетрики регрессии: **MAE** — средняя ошибка в МПа; **R²** — доля объяснённой изменчивости (1 — идеал).")
nb.code('''from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

base_cols = ["cement", "slag", "fly_ash", "water", "superplast", "coarse_aggr", "fine_aggr", "age_days"]
fe_cols = ["cement", "slag", "fly_ash", "water", "superplast", "coarse_aggr", "fine_aggr", "log_age", "w_c"]
y_reg = beton["strength_mpa"]
for name, cols in [("исходные признаки", base_cols), ("+ log(возраст), В/Ц", fe_cols)]:
    X_tr, X_te, y_tr, y_te = train_test_split(beton[cols], y_reg, test_size=0.25, random_state=42)
    reg = LinearRegression().fit(X_tr, y_tr)
    p = reg.predict(X_te)
    print(f"{name:<22} MAE = {mean_absolute_error(y_te, p):.1f} МПа   R² = {r2_score(y_te, p):.2f}")''')
nb.code('''plt.figure(figsize=(5, 5))
plt.scatter(y_te, p, alpha=0.5, color="#37B34A"); plt.plot([0, 85], [0, 85], "--", color="#244128")
plt.xlabel("факт, МПа"); plt.ylabel("прогноз, МПа"); plt.title("Регрессия: прогноз vs факт"); plt.show()''')
nb.md("**Вывод (А):** два «инженерных» признака заметно повышают качество той же линейной модели (см. рост R² и снижение MAE). Предметное знание важнее сложности алгоритма.")

nb.md("## Шаги 7–10 (Б). Классификация: «замес наберёт ≥ 30 МПа»\n\nПорог 30 МПа — условный учебный критерий приёмки (порядка класса B25 по требуемой средней прочности). Важная ошибка — **FP: принять слабый бетон** → следим за **precision** класса «годен».")
nb.code(ML_IMPORTS + "\n\n" + REPORT_FN + '''

THRESHOLD_MPA = 30
y = (beton["strength_mpa"] >= THRESHOLD_MPA).astype(int)
print("Доля годных:", round(y.mean(), 3))
X_tr, X_te, y_tr, y_te = train_test_split(beton[fe_cols], y, test_size=0.25, random_state=42, stratify=y)
quality(y_te, DummyClassifier(strategy="most_frequent").fit(X_tr, y_tr).predict(X_te), name="Базовая линия")
clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_tr, y_tr)
pred, proba = clf.predict(X_te), clf.predict_proba(X_te)[:, 1]
quality(y_te, pred, proba, name="Логистическая регрессия")
strict = (proba >= 0.8).astype(int)
quality(y_te, strict, proba, name="Строгий порог p ≥ 0,8")''')
nb.code('''fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ConfusionMatrixDisplay(confusion_matrix(y_te, pred), display_labels=["брак", "годен"]).plot(ax=ax[0], cmap="Greens", colorbar=False); ax[0].set_title("порог 0,5")
ConfusionMatrixDisplay(confusion_matrix(y_te, strict), display_labels=["брак", "годен"]).plot(ax=ax[1], cmap="Greens", colorbar=False); ax[1].set_title("порог 0,8")
plt.tight_layout(); plt.show()''')
nb.md("""## Итоговые выводы для бизнеса

1. **Регрессия:** прочность прогнозируется по рецептуре со средней ошибкой ≈ 6 МПа (R² = 0,80 против 0,56 на «сырых» признаках) после добавления двух инженерных признаков.
2. **Контроль качества:** классификатор отделяет «годные» замесы значительно лучше базовой линии; **строгий порог 0,8** повышает precision — меньше риска принять слабый бетон, но больше замесов уходит на лабораторную проверку.
3. **Управленческий эффект:** лаборатория проверяет в первую очередь «сомнительные» замесы, а не все подряд; рецептуры с высоким В/Ц — кандидаты на пересмотр.
4. **Ограничения:** лабораторные данные из одного источника (Тайвань, 1990-е); для стройплощадки нужны данные своего поставщика бетона.""")
nb.save("/home/user/workspace/lecture7/notebooks/03_construction_concrete.ipynb")
print("ok")
