import io
import json
import os
import httpx
from openai import OpenAI, DefaultHttpxClient
import base64

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.converter.stage.stage import Stage
from app.converter.utils.helpers import delete_latex_md


class AIExtractor(Stage):
    def __init__(self, api_key: str, proxies: dict[str:str], model: str = "gpt-4o", text: str = "", tables: str = "",
                 formulas: str = "", base_url: str | None = None):
        key = os.path.expandvars(api_key)
        self.client = None
        if proxies.get("http"):
            print(proxies["http"])
            self.client = OpenAI(api_key=key, http_client=DefaultHttpxClient(
                proxy=proxies["http"],
                transport=httpx.HTTPTransport(local_address="0.0.0.0"),
            ), base_url=base_url)
        else:
            print("no proxies")
            self.client = OpenAI(api_key=key, base_url=base_url)
        self.model = model
        self.extracted_text_key = text
        self.extracted_tables_key = tables
        self.extracted_formulas_key = formulas

    def process(self, data):
        with open(data['img'], "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        uploaded_files = self.upload_files(data)
        prompt_text = self.get_text_prompt()

        print(prompt_text)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt_text
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        },
                        {
                            "type": "file",
                            "file": {"file_id": uploaded_files["ocr_text.pdf"]}
                        },
                        {
                            "type": "file",
                            "file": {"file_id": uploaded_files["ocr_tables.pdf"]}
                        },
                        {
                            "type": "file",
                            "file": {"file_id": uploaded_files["ocr_formulas.pdf"]}
                        },
                    ],
                }
            ],
        )

        return delete_latex_md(response.choices[0].message.content)

    def upload_files(self, data) -> dict[str, str]:
        files_data = [
            ("ocr_text.pdf", self.json_to_pdf_bytes(data[self.extracted_text_key])),
            ("ocr_tables.pdf", self.json_to_pdf_bytes(data[self.extracted_tables_key])),
            ("ocr_formulas.pdf", self.json_to_pdf_bytes(data[self.extracted_formulas_key])),
        ]

        uploaded = {}
        for filename, content_bytes in files_data:
            buf = io.BytesIO(content_bytes)
            f = self.client.files.create(
                file=(filename, buf),
                purpose="assistants"
            )
            uploaded[filename] = f.id
        return uploaded

    def get_text_prompt(self):
        try:
            with open(f"config/prompts/{self.model}.txt", encoding="utf-8") as f:
                prompt_text = f.read()
                return prompt_text
        except FileNotFoundError:
            return ""

    def json_to_pdf_bytes(self, json_data: dict) -> bytes:
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.setFont("Helvetica", 12)
        pretty_json = json.dumps(json_data, indent=2, ensure_ascii=False)

        text = c.beginText(40, 750)
        text.textLines(pretty_json)
        c.drawText(text)
        c.save()

        return buf.getvalue()
