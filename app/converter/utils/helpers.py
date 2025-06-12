import io
import os
import shutil
from typing import Dict, Any
import fitz
from PIL import Image, ImageEnhance, ImageFilter


def get_file_name(file_path=""):
    if file_path == "":
        raise Exception("file cannot be empty")
    file_name = os.path.basename(file_path)
    file_name_without_ext = os.path.splitext(file_name)[0]

    return file_name_without_ext


def create_dir(dir_path):
    os.makedirs(dir_path, exist_ok=True)


def enhance_image(image):
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)
    image = image.convert('L')
    image = image.filter(ImageFilter.SHARPEN)

    return image


def pdf_to_image(pdf_file):
    if pdf_file == "":
        raise Exception("file cannot be empty")

    doc = fitz.open(pdf_file)
    first_page = doc.load_page(0)
    pix = first_page.get_pixmap(matrix=fitz.Matrix(3, 3), dpi=600)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    doc.close()

    return img


def expand_env_vars(params: Dict[str, Any]) -> Dict[str, Any]:
    expanded_params = {}
    for key, value in params.items():
        if isinstance(value, str):
            expanded_params[key] = os.path.expandvars(value)
        elif isinstance(value, dict):
            expanded_params[key] = expand_env_vars(value)
        elif isinstance(value, list):
            expanded_params[key] = [
                os.path.expandvars(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            expanded_params[key] = value
    return expanded_params


def delete_latex_md(text: str) -> str:
    text = text.replace("```latex", "")
    text = text.replace("```", "")
    return text


def zip_directory(folder_path, output_path):
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Directory {folder_path} does not exist")

    shutil.make_archive(
        base_name=f"downloads/{output_path}",
        format='zip',
        root_dir=folder_path
    )
    return f"{output_path}.zip"


def delete_temp_files(dirs: list, files: list):
    try:
        for dir in dirs:
            shutil.rmtree(dir)

        for file in files:
            os.remove(file)
    except PermissionError:
        print("Permission denied")
