from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from datetime import datetime, date
import io
import tempfile
import os
from fastapi.responses import FileResponse


router = APIRouter(prefix="/documents", tags=["documents"])


class HolidayDocumentRequest(BaseModel):
    surname: str
    name: str
    patronymic: str
    holiday_date: str



DOCUMENT_TEMPLATE = """
<html xmlns:o='urn:schemas-microsoft-com:office:office' 
      xmlns:w='urn:schemas-microsoft-com:office:word' 
      xmlns='http://www.w3.org/TR/REC-html40'>
<head>
    <meta charset='utf-8'>
    <title>Справка о выходном дне</title>
    <style>
        body { font-family: 'Times New Roman'; font-size: 14pt; margin: 1in; }
        .header { text-align: center; font-weight: bold; font-size: 16pt; margin-bottom: 20pt; }
        .subheader { text-align: center; font-size: 14pt; margin-bottom: 30pt; }
        .section { margin-bottom: 15pt; text-align: justify; line-height: 1.5; }
        .employee-info { margin: 20pt 0; }
        .employee-info table { border-collapse: collapse; }
        .employee-info td { padding: 5pt 10pt; vertical-align: top; }
        .signature { margin-top: 50pt; text-align: right; }
    </style>
</head>
<body>
    <div class='header'>СПРАВКА</div>
    <div class='subheader'>о предоставлении выходного дня</div>

    <div class='section'>
        Настоящая справка подтверждает, что сотруднику:
    </div>

    <div class='employee-info'>
        <table>
            <tr><td><b>Фамилия:</b></td><td>{{surname}}</td></tr>
            <tr><td><b>Имя:</b></td><td>{{name}}</td></tr>
            <tr><td><b>Отчество:</b></td><td>{{patronymic}}</td></tr>
        </table>
    </div>

    <div class='section'>
        на основании приказа руководства предоставлен дополнительный
        выходной день <b>{{holiday_date}}</b>.
    </div>

    <div class='section'>
        Выходной день предоставляется в счет переработки рабочих часов
        и не подлежит денежной компенсации.
    </div>

    <div class='section'>
        Справка выдана для предъявления по месту требования.
    </div>

    <div class='signature'>
        <div>Дата выдачи справки: <b>{{current_date}}</b></div>
        <div style='margin-top: 50pt;'>_________________________</div>
        <div>М.П.</div>
    </div>
</body>
</html>
"""


def generate_holiday_document(surname: str, name: str, patronymic: str, holiday_date: str) -> str:
    """
    Генерация документа с заменой переменных в шаблоне
    """
    try:
        # Парсим дату
        holiday_dt = datetime.strptime(holiday_date, "%Y-%m-%d")
        current_date = datetime.now()

        # Замена переменных в шаблоне
        document = DOCUMENT_TEMPLATE \
            .replace("{{surname}}", surname) \
            .replace("{{name}}", name) \
            .replace("{{patronymic}}", patronymic) \
            .replace("{{holiday_date}}", holiday_dt.strftime("%d.%m.%Y")) \
            .replace("{{current_date}}", current_date.strftime("%d.%m.%Y"))

        return document

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Неверный формат даты: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации документа: {str(e)}")


@router.post("/holiday")
async def create_holiday_document(request: HolidayDocumentRequest):
    """
    Создание справки о выходном дне
    """
    temp_path = None
    try:
        # Генерируем документ
        document_content = generate_holiday_document(
            surname=request.surname,
            name=request.name,
            patronymic=request.patronymic,
            holiday_date=request.holiday_date
        )

        # Создаем временный файл с UTF-8 кодировкой
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.doc', delete=False) as f:
            f.write(document_content)
            temp_path = f.name

        filename = f"holiday_document_{datetime.now().strftime('%Y%m%d%H%M%S')}.doc"

        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type='application/msword'
        )

    except Exception as e:
        # Удаляем временный файл в случае ошибки
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"Ошибка при создании документа: {str(e)}")