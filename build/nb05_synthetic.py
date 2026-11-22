from nbb import *

nb = NB()
nb.md(HEADER.format(
    title="05. Обратная задача: генерируем датасет под процесс TO BE",
    profile="все профили (мост ЛР1 → ЛР2); пример — мониторинг факельного ствола НПЗ",
    question="В модели TO BE (ЛР1) решение принимается «на основе данных», но открытого датасета нет. Какие переменные нужны, чтобы такое решение было возможно, и сработает ли на них наш алгоритм классификации?",
    data="генерируется в этом ноутбуке (`flare_monitoring_synthetic.csv`), сценарий — из материала курса «Примеры проблемных областей в промышленности» (инклинометры на этажерке факельного ствола + газоанализаторы).",
))
nb.md("""## Шаг 1. От BPMN к таблице: какие данные нужны процессу TO BE?

**AS IS:** осмотр факельного ствола — по графику раз в квартал; аварийные крены обнаруживаются поздно.
**TO BE:** датчики → сервер мониторинга → **модель оценивает риск** → при высоком риске автоматически создаётся заявка на внеплановый осмотр.

| элемент BPMN (TO BE) | вопрос к данным | переменная |
|---|---|---|
| событие-триггер «пришли показания» | что измеряем? | `tilt_x_deg`, `tilt_y_deg`, `wind_ms`, `air_temp_c`, `ch4_ppm`, `so2_ppm`, `flare_load_pct` |
| контекст объекта | что влияет на риск? | `days_since_inspection` |
| шлюз «риск высокий?» | что предсказываем? | **`inspection_needed`** (0/1) — целевая переменная |
| результат: заявка в ТОиР | как оцениваем качество? | recall (не пропустить), precision (не гонять бригаду зря) |

**Правило:** каждая переменная должна быть (1) измеримой на практике, (2) доступной *до* решения (без утечки ответа), (3) связанной с решением гипотезой.""")
nb.code(SETUP)
nb.md("## Шаг 2. Генератор: закладываем «скрытые законы» + шум + реальные дефекты данных\n\nМы **знаем** истинные зависимости — значит, можем проверить, найдёт ли их модель. Специально добавлены пропуски и сбои датчиков, чтобы отработать очистку.")
nb.code('''rng = np.random.default_rng(2026)
N = 3000

data = pd.DataFrame({
    "tilt_x_deg": rng.normal(0, 0.25, N),
    "tilt_y_deg": rng.normal(0, 0.25, N),
    "wind_ms": rng.gamma(2.2, 2.5, N).round(1),
    "air_temp_c": rng.normal(2, 12, N).round(1),
    "ch4_ppm": rng.lognormal(1.2, 0.6, N).round(2),
    "so2_ppm": rng.lognormal(-0.5, 0.7, N).round(3),
    "flare_load_pct": rng.uniform(5, 100, N).round(1),
    "days_since_inspection": rng.integers(0, 120, N),
})
tilt = np.hypot(data["tilt_x_deg"], data["tilt_y_deg"])      # полный угол крена

# «Скрытый закон» риска (логит). Знаки и сила влияния заданы осознанно:
z = (-4.2 + 6.0 * tilt + 0.18 * data["wind_ms"] + 0.015 * data["days_since_inspection"]
     + 0.25 * np.log(data["ch4_ppm"]) + 0.012 * data["flare_load_pct"]
     - 0.01 * data["air_temp_c"] + rng.normal(0, 0.6, N))
data["inspection_needed"] = (rng.uniform(size=N) < 1 / (1 + np.exp(-z))).astype(int)

# Дефекты реальной телеметрии: 2% пропусков и 0,5% «зависаний» датчика (значение 99)
for col in ["wind_ms", "ch4_ppm"]:
    data.loc[rng.choice(N, int(0.02 * N), replace=False), col] = np.nan
data.loc[rng.choice(N, int(0.005 * N), replace=False), "tilt_x_deg"] = 99.0

data.to_csv("flare_monitoring_synthetic.csv", index=False)
print(data.shape, "| доля «нужен осмотр»:", round(data["inspection_needed"].mean(), 3))
data.head()''')
nb.md("> Файл `flare_monitoring_synthetic.csv` можно скачать (панель «Файлы» слева) и открыть в **Orange** или Excel — тот же датасет, другой инструмент.")
nb.md("## Шаги 3–4. Паспорт и очистка (как с «настоящими» данными)")
nb.code('''df = pd.read_csv("flare_monitoring_synthetic.csv")
print(df.isna().sum()[lambda s: s > 0])
print("Сбой датчика (|крен| > 10°):", (df["tilt_x_deg"].abs() > 10).sum())
df = df[df["tilt_x_deg"].abs() <= 10].copy()                          # сбой датчика — удаляем строку
df[["wind_ms", "ch4_ppm"]] = df[["wind_ms", "ch4_ppm"]].fillna(df[["wind_ms", "ch4_ppm"]].median())
df["tilt_total"] = np.hypot(df["tilt_x_deg"], df["tilt_y_deg"])       # инженерный признак
df.shape''')
nb.md("## Шаги 5–6. Разведка")
nb.code('''fig, ax = plt.subplots(1, 3, figsize=(15, 4))
sns.boxplot(data=df, x="inspection_needed", y="tilt_total", ax=ax[0]); ax[0].set_title("Крен, °")
sns.boxplot(data=df, x="inspection_needed", y="wind_ms", ax=ax[1]); ax[1].set_title("Ветер, м/с")
df.groupby(pd.cut(df["days_since_inspection"], [0, 30, 60, 90, 120], include_lowest=True), observed=True)["inspection_needed"].mean().plot.bar(ax=ax[2], color="#37B34A")
ax[2].set_title("Доля «нужен осмотр» по давности осмотра, дн."); ax[2].tick_params(axis="x", rotation=0)
plt.tight_layout(); plt.show()''')
nb.md("## Шаги 7–10. Модель, качество — и проверка: нашла ли модель «скрытый закон»?")
nb.code(ML_IMPORTS + "\n\n" + REPORT_FN + '''

features = ["tilt_total", "wind_ms", "air_temp_c", "ch4_ppm", "so2_ppm", "flare_load_pct", "days_since_inspection"]
X, y = df[features], df["inspection_needed"]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
quality(y_te, DummyClassifier(strategy="most_frequent").fit(X_tr, y_tr).predict(X_te), name="Базовая линия")
model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_tr, y_tr)
pred, proba = model.predict(X_te), model.predict_proba(X_te)[:, 1]
quality(y_te, pred, proba, name="Логистическая регрессия")
ConfusionMatrixDisplay(confusion_matrix(y_te, pred), display_labels=["норма", "осмотр"]).plot(cmap="Greens"); plt.show()''')
nb.code('''truth = pd.Series({"tilt_total": "+ сильно", "wind_ms": "+", "air_temp_c": "− слабо", "ch4_ppm": "+ (лог)",
                   "so2_ppm": "0 (не влияет)", "flare_load_pct": "+", "days_since_inspection": "+"})
pd.DataFrame({"заложено в генератор": truth,
              "вес модели (станд.)": pd.Series(model[-1].coef_[0], index=features).round(2)})''')
nb.md("""## Выводы

1. Модель **восстановила знаки и порядок силы** заложенных зависимостей: крен — главный фактор, за ним ветер, давность осмотра и нагрузка факела; SO₂ — почти ноль (мы его и не закладывали). Значит, *набор переменных достаточен* для решения в шлюзе TO BE.
2. Синтетика проверяет **логику процесса и алгоритма**, но **не доказывает** реальный эффект: в реальности зависимости неизвестны. Следующий шаг — запрос реальных данных у владельца процесса (SCADA/АСУ ТП) по той же схеме столбцов.
3. Схема столбцов — это **техническое задание на сбор данных**: её можно приложить к модели TO BE в ЛР1 и к обоснованию ЛР2.

---
### Шаблон запроса к ИИ-ассистенту (GigaChat / YandexGPT / DeepSeek и др.) для своей темы

```
Роль: аналитик данных промышленного предприятия.
Контекст: процесс TO BE «<название>» (BPMN из ЛР1). Решение в шлюзе «<вопрос>» должно приниматься по данным.
Задача: предложи 6–10 измеримых переменных (название_латиницей, единицы, диапазон, источник данных в компании),
целевую бинарную переменную и правдоподобные зависимости (знак и сила влияния).
Затем напиши код Python (numpy, pandas) для генерации CSV на 2000–5000 строк:
логистическая зависимость цели от признаков + шум, 1–3% пропусков, 0,5% выбросов-сбоев.
Не используй переменные, известные только после события (утечка ответа).
```
**Обязательно** проверьте предложенные ИИ зависимости на здравый смысл и укажите в отчёте, что данные синтетические.""")
nb.save("/home/user/workspace/lecture7/notebooks/05_reverse_task_synthetic_dataset.ipynb")
print("ok")
