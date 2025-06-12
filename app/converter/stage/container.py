import importlib

CLASS_MAP = {
    'ImagePreprocessor': 'app.converter.pipeline.preprocessing.images',
    'PDFPreprocessor': 'app.converter.pipeline.preprocessing.pages',
    'MarkerPdfTextExtractor': 'app.converter.pipeline.ocr.marker_pdf.text',
    'MarkerPdfTablesExtractor': 'app.converter.pipeline.ocr.marker_pdf.tables',
    'TesseractTablesExtractor': 'app.converter.pipeline.ocr.tesseract.tables',
    'TesseractTextExtractor': 'app.converter.pipeline.ocr.tesseract.text',
    'FormulasExtractor': 'app.converter.pipeline.ocr.formulas',
    'AIExtractor': 'app.converter.pipeline.models.o4-mini',
    'TexExporter': 'app.converter.pipeline.file.tex',
}


def get_stage_class(class_name):
    if class_name not in CLASS_MAP.keys():
        raise ValueError(f"Class {class_name} not found in CLASS_MAP")

    module_path = CLASS_MAP[class_name]
    module = importlib.import_module(module_path)
    return getattr(module, class_name)
