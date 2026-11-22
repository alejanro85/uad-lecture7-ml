"""Экспорт обученных моделей в JSON для статической страницы (GitHub Pages, папка docs/).

Страница не требует сервера: логистическая регрессия — это формула
p = 1 / (1 + exp(-(b0 + Σ bi·zi))), где zi — стандартизованные признаки и 0/1 для категорий.
Поэтому достаточно выгрузить средние, стандартные отклонения, категории и веса.

Запуск: python webapps/export_static.py  →  docs/models.json
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent / "streamlit_app"))
from cases import CASES, fit_case  # noqa: E402

ENGINEER = {"concrete": "concrete", "flare": "flare"}   # JS-функции с тем же смыслом, что в cases.py
out = {}
for key, case in CASES.items():
    R = fit_case(case)
    m = R["model"]
    prep = m.named_steps["prep"]
    sc = prep.named_transformers_["num"]
    lr = m.named_steps["lr"]
    X = R["X"]
    inputs = []
    for c in case.num:
        lo, hi = float(X[c].quantile(0.01)), float(X[c].quantile(0.99))
        inputs.append(dict(name=c, label=case.labels.get(c, c), type="num",
                           min=round(lo, 3), max=round(hi, 3), value=round(float(X[c].median()), 3),
                           step=round((hi - lo) / 100, 4) or 1))
    cats = {}
    if case.cat:
        enc = prep.named_transformers_["cat"]
        for c, vals in zip(case.cat, enc.categories_):
            vals = [str(v) for v in vals]
            cats[c] = vals
            inputs.append(dict(name=c, label=case.labels.get(c, c), type="cat", options=vals,
                               value=str(X[c].mode()[0])))
    coef = lr.coef_[0].tolist()
    n_num = len(case.features_num)
    sample = X.iloc[:5]
    out[key] = dict(
        title=case.title, profile=case.profile, question=case.question, source=case.source,
        event=case.event, no_event=case.no_event, fp_text=case.fp_text, fn_text=case.fn_text,
        cost_fp=case.cost_fp, cost_fn=case.cost_fn, event_is_good=case.event_is_good,
        engineer=ENGINEER.get(key), inputs=inputs,
        model=dict(num=case.features_num, mean=sc.mean_.round(6).tolist(), scale=sc.scale_.round(6).tolist(),
                   num_coef=[round(v, 6) for v in coef[:n_num]],
                   cat=cats, cat_coef=[round(v, 6) for v in coef[n_num:]],
                   intercept=round(float(lr.intercept_[0]), 6),
                   labels={c: case.labels.get(c, c) for c in case.features_num}),
        test=dict(y=R["y_te"].astype(int).tolist(), p=np.round(R["proba"], 4).tolist()),
        check=dict(rows=json.loads(sample.to_json(orient="records", force_ascii=False)),
                   p=np.round(m.predict_proba(sample)[:, 1], 6).tolist()),
    )
    print(key, "ok", len(R["y_te"]))

dst = Path(__file__).resolve().parents[1] / "docs" / "models.json"
dst.parent.mkdir(exist_ok=True)
dst.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("→", dst, dst.stat().st_size // 1024, "KB")
