Материалы к лекции "Методы и инструментальные средства анализа данных"
Профили: менеджмент в нефтегазе, менеджмент в энергетике, менеджмент в девелопменте и строительстве, производственный и инновационный менеджмент.

## Состав

| Папка / файл | Содержание |
|---|---|
| `notebooks/` | Блокноты Google Colab с выполненным анализом и интерпретацией |
| `data/` | Копии открытых датасетов для загрузки по raw-ссылкам |
| `orange/` | Low-code схема Orange для того же датасета students.csv |
| `webapps/` | Веб-формы для кейсов: Streamlit-приложение, экспорт моделей, руководство по средствам и шаблоны промптов |
| `docs/` | Статическая веб-форма для GitHub Pages (работает без сервера) |
| `img/` | Снимки экранов Orange, использованные в презентации |
| `deck/`, `build/` | Скрипты сборки презентации и блокнотов |

## Блокноты Colab

Сценарий во всех блокнотах один и тот же: вопрос → загрузка → паспорт данных → очистка → разведка → связи и тренды → постановка ML → разбиение → модель и базовая линия → качество и вывод.

| № | Профиль | Открыть |
|---|---|---|
| 00 | Эталон: students.csv, логистическая регрессия | [Colab](https://colab.research.google.com/github/alejanro85/uad-lecture7-ml/blob/main/notebooks/00_students_etalon.ipynb) |
| 01 | Нефтегаз: цены Brent, обнаружение нефтяных разливов | [Colab](https://colab.research.google.com/github/alejanro85/uad-lecture7-ml/blob/main/notebooks/01_oilgas_brent_oilspill.ipynb) |
| 02 | Энергетика: устойчивость электросети | [Colab](https://colab.research.google.com/github/alejanro85/uad-lecture7-ml/blob/main/notebooks/02_energy_smart_grid.ipynb) |
| 03 | Строительство: прочность бетона | [Colab](https://colab.research.google.com/github/alejanro85/uad-lecture7-ml/blob/main/notebooks/03_construction_concrete.ipynb) |
| 04 | Производство: предиктивное обслуживание AI4I 2020 | [Colab](https://colab.research.google.com/github/alejanro85/uad-lecture7-ml/blob/main/notebooks/04_production_predictive_maintenance.ipynb) |
| 05 | Связь ЛР1 и ЛР2: обратная задача, синтетический датасет | [Colab](https://colab.research.google.com/github/alejanro85/uad-lecture7-ml/blob/main/notebooks/05_reverse_task_synthetic_dataset.ipynb) |
| 06 | Веб-формы в Colab: Colab Forms, ipywidgets, Gradio | [Colab](https://colab.research.google.com/github/alejanro85/uad-lecture7-ml/blob/main/notebooks/06_web_forms_gradio.ipynb) |

Блокноты загружают данные по raw-ссылкам GitHub, поэтому в Colab достаточно выполнить «Среда выполнения → Выполнить все».

## Источники данных

| Файл | Источник | Лицензия / условия |
|---|---|---|
| `students.csv` | [Stepik: от идеи к MVP](https://github.com/evgpat/stepik_from_idea_to_mvp) | учебный датасет курса |
| `brent-daily.csv` | [datasets/oil-prices](https://github.com/datasets/oil-prices) (данные EIA) | PDDL / общественное достояние |
| `oil-spill.csv` | [jbrownlee/Datasets](https://github.com/jbrownlee/Datasets), Kubat et al., 1998 | учебное использование |
| `grid_stability.csv` | [UCI: Electrical Grid Stability](https://archive.ics.uci.edu/dataset/471/electrical+grid+stability+simulated+data) | CC BY 4.0 |
| `Concrete_Data.xls` | [UCI: Concrete Compressive Strength](https://archive.ics.uci.edu/dataset/165/concrete+compressive+strength) | CC BY 4.0 |
| `ai4i2020.csv` | [UCI: AI4I 2020 Predictive Maintenance](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset) | CC BY 4.0 |
| `flare_monitoring_synthetic.csv` | сгенерирован в блокноте 05 | синтетические данные |

## Orange

1. Установите Orange: https://orangedatamining.com/download/
2. Откройте `orange/students_classification.ows` (File → Open).
3. Виджет File загружает `students_for_orange.csv` по raw-ссылке из этого репозитория. Если нужна работа без интернета, переключите виджет File на локальный файл `orange/students_for_orange.csv`.

Схема: File → Data Table / Distributions / Box Plot; Logistic Regression → Test and Score → Confusion Matrix; Nomogram.

## Веб-формы

- Веб-форма без сервера: [alejanro85.github.io/uad-lecture7-ml](https://alejanro85.github.io/uad-lecture7-ml/). На ней пять кейсов, форма «что если», порог, матрица несоответствий и цена ошибок.
- Приложение Streamlit с загрузкой своего CSV лежит в `webapps/streamlit_app/`.
- Руководство по выбору средств и развёртыванию: [`webapps/README.md`](webapps/README.md). Шаблоны промптов для LLM: [`webapps/PROMPTS.md`](webapps/PROMPTS.md).

## Ссылка на данные в ЛР2

Итог ЛР2 требует ссылки на датасет через GitHub: загрузите CSV в свой репозиторий, откройте файл, нажмите Raw и используйте полученный адрес в `pd.read_csv(URL)`.
