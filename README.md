# PDF → LaTeX Converter

Этот проект предоставляет сервис для преобразования PDF‑файлов в набор `.tex`‑страниц.
Сервис разбивает документ на страницы, выполняет OCR (текст, таблицы, формулы) и при необходимости использует модель OpenAI для генерации чистого LaTeX.

## Состав репозитория
- `app/` – код FastAPI и логика конвертации
- `config/` – `application.yaml` и шаблоны `prompts`
- `front/` – минимальный веб‑клиент
- `process_pdf.py` – утилита для пакетной обработки
- `downloads/`, `cache/`, `temp/` – создаются во время работы

## Установка
1. Python 3.10+ и пакеты `tesseract-ocr`, `poppler` и др.
2. `pip install -r requirements.txt`
3. Скопируйте `.env-example` в `.env` и укажите `API_KEY` и `HTTP_PROXY` при необходимости

## Настройка
Все стадии и параметры описаны в `config/application.yaml`.
Пример раздела `pipeline`:

```yaml
pipeline:
  preprocessors:
    - name: ImagePreprocessor
      params:
        directory: "img"
        output_prefix: "page_"
  stages:
    - name: MarkerPdfTextExtractor
      params:
        languages: "en,ru"
        force_ocr: true
    - name: TexExporter
      params:
        directory: "tex"
        output_prefix: "page_"
        result_data_key: "AIExtractor"
```

Путь к шаблонам (`prompts_dir`) и директории кеша также настраиваются здесь.

## Запуск сервера
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API
- `POST /api/v1/convert` – принять PDF и вернуть ссылку на скачивание
- `GET /api/v1/convert/{id}` – отдать ZIP‑архив с `.tex`‑страницами

### CLI
```bash
python process_pdf.py path/to/file.pdf
```

### Веб‑клиент
В папке `front/` есть простой клиент. Запустите его любым HTTP‑сервером:

```bash
cd front
python -m http.server 8000
```

Базовый URL API задаётся через параметр `apiBase` в строке запроса, например `index.html?apiBase=http://localhost:8000`.

## Очистка
Временные файлы хранятся в `temp/`, результаты – в `downloads/`. Метод `Converter.cleanup()` удаляет временные каталоги, но готовые архивы остаются.

## Расширение
Создайте класс‑наследник `Stage`, зарегистрируйте его в `CLASS_MAP` (`app/converter/stage/container.py`) и добавьте в `application.yaml`.

---
Сервис адаптируем к различным OCR и LLM, что позволяет собирать собственные пайплайны конвертации.
