import os
import fitz  # PyMuPDF
from PIL import Image
import io
import asyncio
import aiohttp
from aiohttp import ClientTimeout # Import ClientTimeout
import uuid
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TEMP_DIR = Path("pdf_docs")
OUTPUT_DIR = Path("pdf_docs_output") # Директория для сохранения результатов
OUTPUT_DIR.mkdir(exist_ok=True)


async def split_pdf_to_images(pdf_path: Path):
    """
    Разбивает PDF на отдельные страницы PDF и возвращает пути к ним.
    """
    logging.info(f"Начинаю разбиение PDF: {pdf_path} на страницы.")
    doc = fitz.open(pdf_path)
    pdf_paths = []
    file_name_without_ext = pdf_path.stem

    output_file_dir = OUTPUT_DIR / file_name_without_ext
    output_file_dir.mkdir(exist_ok=True)

    for i in range(doc.page_count):
        page = doc.load_page(i)
        # Сохранение страницы как отдельного PDF
        page_pdf_path = output_file_dir / f"page_{i + 1}.pdf"
        # Создаем новый документ для каждой страницы и сохраняем ее
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
        new_doc.save(page_pdf_path)
        new_doc.close()

        pdf_paths.append(page_pdf_path)
        logging.info(f"Сохранена страница {i + 1} как {page_pdf_path}")
    doc.close()
    logging.info(f"Разбиение PDF {pdf_path} завершено. Обнаружено {len(pdf_paths)} страниц.")
    return pdf_paths

async def process_page(pdf_path: Path):
    """
    Отправляет страницу PDF в сервис конвертации и сохраняет результат.
    """
    page_name = pdf_path.stem
    file_name = pdf_path.parent.name
    logging.info(f"Обработка страницы {page_name} из файла {file_name}...")

    # Создание уникальной директории для результатов страницы
    page_output_dir = OUTPUT_DIR / file_name / page_name
    page_output_dir.mkdir(parents=True, exist_ok=True)

    try:
        async with aiohttp.ClientSession() as session: # Create a new session for each request
            with open(pdf_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=pdf_path.name, content_type='application/pdf')

                # Add timeout to the post request
                async with session.post("http://127.0.0.1:8000/api/v1/convert", data=data, timeout=ClientTimeout(total=12000)) as response:
                    if response.status == 201:
                        result = await response.json()
                        download_url = result.get("download_url")
                        logging.info(f"Страница {page_name} успешно конвертирована. URL для скачивания: {download_url}")

                        # Скачивание результата по download_url
                        if download_url:
                            full_download_url = f"http://127.0.0.1:8000/api/v1{download_url}" # Убедитесь, что это правильный базовый URL
                            # Add timeout to the get request
                            async with session.get(full_download_url, timeout=ClientTimeout(total=12000)) as download_response:
                                if download_response.status == 200:
                                    output_zip_path = page_output_dir / "converted_data.zip"
                                    with open(output_zip_path, "wb") as f:
                                        f.write(await download_response.read())
                                    logging.info(f"Конвертированный результат для страницы {page_name} сохранен в {output_zip_path}")
                                else:
                                    logging.error(f"Не удалось скачать результат для страницы {page_name}: {download_response.status} - {await download_response.text()}")
                        else:
                            logging.warning(f"URL для скачивания не найден в ответе для страницы {page_name}.")

                    else:
                        error_detail = await response.text()
                        logging.error(f"Ошибка при конвертации страницы {page_name}: {response.status} - {error_detail}")
    except Exception as e:
        logging.error(f"Исключение при обработке страницы {page_name}: {e}")

async def main(pdf_file_path: str):
    """
    Основная функция для управления процессом конвертации PDF.
    """
    pdf_path = Path(pdf_file_path)
    if not pdf_path.exists():
        logging.error(f"Файл не найден: {pdf_file_path}")
        return

    logging.info(f"Начинаю процесс конвертации PDF: {pdf_file_path}")
    pdf_paths = await split_pdf_to_images(pdf_path)

    # Ограничение на количество одновременно обрабатываемых страниц
    sem = asyncio.Semaphore(4) # Не более 4 одновременных задач

    async def sem_task(pdf_path):
        async with sem:
            await process_page(pdf_path) # No longer passing session

    tasks = [sem_task(path) for path in pdf_paths[10:]]
    await asyncio.gather(*tasks)

    logging.info(f"Процесс конвертации PDF: {pdf_file_path} завершен.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        logging.error("Использование: python process_pdf.py <путь_к_pdf_файлу>")
        sys.exit(1)

    input_pdf_path = sys.argv[1]
    asyncio.run(main(input_pdf_path))
