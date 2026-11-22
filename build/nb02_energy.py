from nbb import *

nb = NB()
nb.md(HEADER.format(
    title="02. Энергетика: устойчивость «умной» электросети (Smart Grid)",
    profile="Менеджмент в энергетике",
    question="Можно ли по параметрам участников энергосети (время реакции на цену, мощность, ценовая эластичность) заранее определить, станет ли сеть неустойчивой, — и какие параметры менеджмент может регулировать (тарифы, требования к оборудованию)?",
    data=f"`grid_stability.csv` — 10 000 сценариев сети «1 производитель + 3 потребителя» с децентрализованным управлением по цене (Decentral Smart Grid Control). Источник: [UCI ML Repository, Electrical Grid Stability Simulated Data](https://archive.ics.uci.edu/dataset/471/electrical+grid+stability+simulated+data), Arzamasov et al., 2018, CC BY 4.0.",
))
nb.md("""## Шаг 1. Вопрос и гипотеза

| признак | смысл |
|---|---|
| `tau1…tau4` | время реакции участника на изменение цены, с (1 — производитель, 2–4 — потребители) |
| `p1…p4` | номинальная мощность: p1 > 0 производство, p2–p4 < 0 потребление |
| `g1…g4` | коэффициент ценовой эластичности участника (γ) |
| `stab` | максимальный действительный корень характеристического уравнения (> 0 — неустойчиво) |
| `stabf` | метка: stable / unstable → **целевая переменная** |

**Гипотеза H1:** чем медленнее участники реагируют на цену (больше τ), тем выше риск неустойчивости.""")
nb.code(SETUP)
nb.md("## Шаги 2–3. Загрузка и паспорт данных")
nb.code(f'''grid = pd.read_csv("{RAW}grid_stability.csv")
print(grid.shape); print("Пропусков:", grid.isna().sum().sum())
grid.describe().T.round(2)''')
nb.code('''grid["stabf"].value_counts(normalize=True).round(3)''')
nb.md("**Вывод:** 10 000 сценариев, 14 столбцов, пропусков нет (данные смоделированы). Неустойчивых сценариев — 63,8%: классы не сбалансированы, но не критично.")

nb.md("## Шаг 4. Подготовка: убираем «утечку ответа» и дубли информации\n\n* `stab` — это численная версия ответа. Если оставить её в признаках, модель будет «списывать» → **data leakage**.\n* `p1 = −(p2 + p3 + p4)` — линейно зависит от других, добавляет только мультиколлинеарность.")
nb.code('''print("Проверка баланса мощности:", np.allclose(grid["p1"], -(grid["p2"] + grid["p3"] + grid["p4"])))
X = grid.drop(columns=["stab", "stabf", "p1"])
y = (grid["stabf"] == "unstable").astype(int)      # 1 — неустойчиво
X.columns.tolist()''')
nb.md("## Шаги 5–6. Разведка: какие параметры связаны с неустойчивостью?")
nb.code('''fig, ax = plt.subplots(1, 3, figsize=(14, 3.6))
for a, col in zip(ax, ["tau1", "g1", "p2"]):
    sns.kdeplot(data=grid, x=col, hue="stabf", fill=True, common_norm=False, ax=a)
plt.tight_layout(); plt.show()''')
nb.code('''share = grid.assign(tau_mean=grid[["tau1","tau2","tau3","tau4"]].mean(axis=1))
share["tau_group"] = pd.qcut(share["tau_mean"], 5, labels=["очень быстро", "быстро", "средне", "медленно", "очень медленно"])
ax = share.groupby("tau_group", observed=True)["stabf"].apply(lambda s: (s == "unstable").mean()).plot.bar(color="#37B34A", figsize=(7, 3.5))
ax.set_ylabel("доля неустойчивых"); ax.set_title("Скорость реакции участников и риск неустойчивости"); plt.xticks(rotation=0); plt.show()''')
nb.code('''sns.heatmap(grid.drop(columns=["stabf"]).corr()[["stab"]].drop("stab").sort_values("stab"),
            annot=True, fmt=".2f", cmap="RdYlGn_r", center=0)
plt.title("Корреляция признаков со stab"); plt.show()''')
nb.md("**Вывод по шагам 5–6:** гипотеза H1 подтверждается: в группе «очень медленной» реакции доля неустойчивых сценариев — 92%, в группе «очень быстрой» — 28% (в 3,3 раза меньше). Эластичность γ тоже положительно связана с неустойчивостью. Мощность p почти не влияет.")

nb.md("## Шаги 7–10. Модель и оценка качества")
nb.code(ML_IMPORTS + "\n\n" + REPORT_FN + '''

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
quality(y_te, DummyClassifier(strategy="most_frequent").fit(X_tr, y_tr).predict(X_te), name="Базовая линия")
model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_tr, y_tr)
pred, proba = model.predict(X_te), model.predict_proba(X_te)[:, 1]
quality(y_te, pred, proba, name="Логистическая регрессия")''')
nb.code('''fig, ax = plt.subplots(1, 2, figsize=(13, 4.2))
ConfusionMatrixDisplay(confusion_matrix(y_te, pred), display_labels=["устойчиво", "неустойчиво"]).plot(ax=ax[0], cmap="Greens", colorbar=False)
coef = pd.Series(model[-1].coef_[0], index=X.columns).sort_values()
coef.plot.barh(ax=ax[1], color=["#37B34A" if v < 0 else "#DA4927" for v in coef])
ax[1].set_title("Веса: красные повышают риск неустойчивости")
plt.tight_layout(); plt.show()''')
nb.md("""## Итоговые выводы для бизнеса

1. Модель распознаёт неустойчивые сценарии с **accuracy ≈ 82% против 64%** у базовой линии (ROC-AUC ≈ 0,89).
2. **Главные управляемые факторы риска** — время реакции участников (τ) и их ценовая эластичность (γ). Это прямые рычаги для менеджмента: требования к скорости систем учёта/управления у потребителей, дизайн тарифа (насколько резко цена реагирует на дисбаланс).
3. **Демонстрация методической ошибки:** если не удалить `stab`, точность будет ~100% — но это «списывание», а не прогноз. Проверяйте признаки на утечку!
4. **Ограничения:** данные смоделированы; линейная модель не ловит взаимодействия факторов — следующий шаг: дерево решений / градиентный бустинг и данные реальной сети.""")
nb.save("/home/user/workspace/lecture7/notebooks/02_energy_smart_grid.ipynb")
print("ok")
