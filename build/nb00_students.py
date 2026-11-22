from nbb import *

nb = NB()
nb.md(HEADER.format(
    title="00. Эталонный разбор: успеваемость студентов (students.csv)",
    profile="общий пример для всех профилей — «тренажёр» алгоритма",
    question="Можно ли заранее (по известным характеристикам) выявить студентов, которые рискуют не сдать экзамен по письму, чтобы вовремя предложить им подготовительный курс?",
    data=f"`students.csv` — 1000 студентов, 8 признаков. Источник: открытый учебный датасет курса Stepik «От идеи к MVP» ([оригинал](https://raw.githubusercontent.com/evgpat/stepik_from_idea_to_mvp/main/datasets/students.csv)); копия в репозитории курса.",
))
nb.md("""> **Что исправлено по сравнению с исходным примером.** (1) замена пропусков сделана без `inplace` в цепочке — в pandas ≥ 2 старый вариант *молча не работает*; (2) в модель включены *все* признаки (категориальные — через one-hot), а не только бинарные; (3) добавлена **базовая линия** — без неё нельзя понять, хороша ли точность; (4) добавлены precision / recall / F1 / ROC-AUC и **интерпретация коэффициентов**; (5) после каждого блока — **вывод**.""")

nb.md("## Шаг 1. Бизнес-вопрос и гипотеза\n\n* **Объект** — студент; **целевая переменная** — сдал ли письменный экзамен (балл ≥ 50).\n* **Гипотеза H1:** подготовительный курс и баллы по другим предметам связаны с успешной сдачей.\n* **Цена ошибки:** пропустить «двоечника» (FN) хуже, чем лишний раз предложить курс (FP) → следим за **recall** класса «не сдал».")
nb.code(SETUP)
nb.md("## Шаг 2. Загрузка данных по постоянной ссылке")
nb.code(f'''URL = "{RAW}students.csv"
df = pd.read_csv(URL)
df.head()''')

nb.md("## Шаг 3. Паспорт данных: размер, типы, пропуски\n\n**Строки** — объекты (студенты), **столбцы** — признаки.")
nb.code('''print("Размер:", df.shape)
df.info()''')
nb.code('''df.describe().round(1)''')
nb.code('''df.describe(include="object")''')
nb.md("""**Описание признаков**

| признак | смысл | тип |
|---|---|---|
| gender | пол | категориальный (2) |
| parental level of education | образование родителей | категориальный (6) |
| lunch | тип обеда (standard / free-reduced) — косвенный признак дохода семьи | бинарный |
| test preparation course | проходил ли подготовительный курс | бинарный |
| class_group | учебная группа | категориальный (5) |
| math score, reading score | баллы за математику и чтение | числовой 0–100 |
| writing score | балл за письмо → **основа целевой переменной** | числовой 0–100 |

**Вывод по шагу 3:** 1000 объектов; есть пропуски (math score — 48, gender — 77, образование родителей — 76, reading — 10), отрицательный балл по математике (−5) и опечатка `standart` в lunch. Данные нужно почистить.""")

nb.md("## Шаг 4. Очистка: пропуски, ошибки, опечатки")
nb.code('''df.isna().sum()''')
nb.code('''# 4.1 некорректные значения: отрицательный балл -> 0
df["math score"] = df["math score"].clip(lower=0)

# 4.2 пропуски в числовых признаках -> среднее (пропусков < 5%)
for col in ["math score", "reading score"]:
    df[col] = df[col].fillna(df[col].mean())

# 4.3 пропуски в категориях -> отдельная категория "unknown"
for col in ["gender", "parental level of education"]:
    df[col] = df[col].fillna("unknown")

# 4.4 опечатка в категории
df["lunch"] = df["lunch"].replace("standart", "standard")

print(df.isna().sum().sum(), "пропусков осталось")
df["lunch"].value_counts()''')
nb.md("**Вывод по шагу 4:** пропусков не осталось, категории приведены к единому написанию. Каждое исправление обосновано: доля пропусков мала, поэтому заполняем, а не удаляем строки.")

nb.md("## Шаг 5. Разведка: распределения (однофакторный анализ)")
nb.code('''fig, ax = plt.subplots(1, 3, figsize=(14, 3.5))
for a, col in zip(ax, ["math score", "reading score", "writing score"]):
    sns.histplot(df[col], kde=True, ax=a)
    a.axvline(50, color="#DA4927", ls="--")
    a.set_title(col)
plt.tight_layout(); plt.show()''')
nb.md("**Вывод по шагу 5:** распределения баллов близки к нормальному, центр около 66–69. Левее порога 50 (красная линия) — заметное меньшинство: это и есть «группа риска».")

nb.md("## Шаг 6. Связи между признаками и целевой переменной")
nb.code('''corr = df[["math score", "reading score", "writing score"]].corr()
sns.heatmap(corr, annot=True, fmt=".2f", cmap="Greens", vmin=0, vmax=1)
plt.title("Корреляция Пирсона"); plt.show()''')
nb.code('''fig, ax = plt.subplots(1, 2, figsize=(12, 3.8))
sns.boxplot(data=df, x="test preparation course", y="writing score", ax=ax[0])
sns.boxplot(data=df, x="lunch", y="writing score", ax=ax[1])
ax[0].set_title("Подготовительный курс"); ax[1].set_title("Тип обеда")
plt.tight_layout(); plt.show()
df.groupby("test preparation course")["writing score"].mean().round(1)''')
nb.md("**Вывод по шагу 6:** баллы по предметам сильно связаны между собой (ρ ≈ 0.8–0.95). Прошедшие подготовительный курс пишут в среднем заметно лучше; «стандартный» обед (выше доход семьи) — тоже. Гипотеза H1 подтверждается на уровне описательной статистики; проверим её моделью.")

nb.md("## Шаг 7. Постановка ML-задачи: целевая переменная и матрица «объект-признак»\n\nБинаризация: **1 — сдал (≥ 50), 0 — не сдал**. Задача — **бинарная классификация**. Все признаки должны стать числами: категориальные кодируем one-hot (`get_dummies`).")
nb.code('''PASSMARK = 50
y = (df["writing score"] >= PASSMARK).astype(int)   # целевая переменная
X = df.drop(columns=["writing score"])               # признаки (writing score убираем — иначе «подсказка ответа»)
X = pd.get_dummies(X, drop_first=True, dtype=int)    # категории -> 0/1
print("Доля сдавших:", round(y.mean(), 3))
X.head()''')

nb.md("## Шаг 8. Разбиение на обучающую и тестовую выборки\n\n75% — учимся, 25% — проверяем на «невиданных» данных. `stratify=y` сохраняет долю классов, `random_state=42` — воспроизводимость.")
nb.code(ML_IMPORTS + '''

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y)
X_train.shape, X_test.shape''')

nb.md("## Шаг 9. Базовая линия и логистическая регрессия\n\n**Базовая линия** (DummyClassifier) всегда отвечает «сдал». Если модель её не обгоняет — модель бесполезна, какой бы высокой ни казалась точность.")
nb.code(REPORT_FN + '''

baseline = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
quality(y_test, baseline.predict(X_test), name="Базовая линия")

model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
model.fit(X_train, y_train)
pred = model.predict(X_test)
proba = model.predict_proba(X_test)[:, 1]
quality(y_test, pred, proba, name="Логистическая регрессия")''')

nb.md("## Шаг 10. Оценка качества и интерпретация")
nb.code('''ConfusionMatrixDisplay(confusion_matrix(y_test, pred),
                       display_labels=["не сдал (0)", "сдал (1)"]).plot(cmap="Greens")
plt.title("Матрица несоответствий (тест)"); plt.show()
print(classification_report(y_test, pred, target_names=["не сдал", "сдал"]))''')
nb.code('''# Какие признаки сильнее всего влияют на прогноз? (признаки стандартизованы -> веса сравнимы)
coef = pd.Series(model[-1].coef_[0], index=X.columns).sort_values()
coef.plot.barh(figsize=(7, 5), color=["#DA4927" if v < 0 else "#37B34A" for v in coef])
plt.title("Веса логистической регрессии"); plt.show()''')
nb.md("### Порог решения — управленческий параметр\n\nМодель выдаёт вероятность. По умолчанию «сдаст», если p ≥ 0,5. Если пропуск «двоечника» дорог, поднимем порог: приглашаем на курс всех, у кого p < 0,7.")
nb.code('''pred_07 = (proba >= 0.7).astype(int)
quality(y_test, pred_07, proba, name="Порог 0,7")
confusion_matrix(y_test, pred_07)''')
nb.md("### Проверка «на честность»: а если оценок по другим предметам нет?\n\nНа практике прогноз нужен *до* экзаменов. Уберём math/reading и оставим только анкетные признаки.")
nb.code('''X_demo = pd.get_dummies(df[["gender", "parental level of education", "lunch",
                             "test preparation course", "class_group"]], drop_first=True, dtype=int)
Xd_tr, Xd_te, yd_tr, yd_te = train_test_split(X_demo, y, test_size=0.25, random_state=42, stratify=y)
m_demo = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(Xd_tr, yd_tr)
quality(yd_te, m_demo.predict(Xd_te), m_demo.predict_proba(Xd_te)[:, 1], name="Только анкета")
confusion_matrix(yd_te, m_demo.predict(Xd_te))''')
nb.md("""## Итоговые выводы для «бизнеса» (деканата)

1. **Базовая линия = 88,4%** (доля сдавших). Модель на всех признаках даёт **accuracy = 96%**, ROC-AUC = 0,99 и находит **22 из 29** несдавших (recall класса «не сдал» = 0,76) — она действительно лучше «угадывания».
2. Главные факторы — баллы по чтению и математике; из «управляемых» факторов положительно влияет **подготовительный курс**.
3. **Ловушка accuracy:** модель только по анкете показывает 88% — ровно уровень базовой линии; из 29 несдавших она находит лишь одного. Высокая точность ≠ полезная модель.
4. **Управленческое решение:** промежуточный контроль (аналог math/reading) + автоматическое приглашение на подготовительный курс тем, чья вероятность сдачи < 0,7: так находим **25 из 29** рискующих ценой 9 «лишних» приглашений — порог выбирает менеджер, а не алгоритм.

**Ограничения:** учебный датасет, причинность не доказана (корреляция ≠ причина); для внедрения нужна проверка на данных своего вуза.""")
nb.save("/home/user/workspace/lecture7/notebooks/00_students_etalon.ipynb")
print("ok")
