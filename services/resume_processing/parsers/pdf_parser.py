"""
PDF resume text parser.

Этот модуль предоставляет функции для извлечения текста из PDF файлов резюме
с использованием PyPDF2 и pdfplumber для сложных макетов.
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Union

import pdfplumber
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_pdf(
    file_path: Union[str, Path], use_fallback: bool = True
) -> Dict[str, Optional[str]]:
    """
    Извлечь текст из PDF файла с использованием PyPDF2 и pdfplumber как запасного варианта.

    Extract text from a PDF file using PyPDF2 and pdfplumber as fallback.

    Args:
        file_path: Путь к PDF файлу / Path to the PDF file
        use_fallback: Если True, попробовать pdfplumber при неудаче PyPDF2 / If True, try pdfplumber if PyPDF2 fails

    Returns:
        Словарь содержащий:
            - text: Извлеченный текст (None при ошибке) / Extracted text content (None if extraction fails)
            - method: Какая библиотека сработала ('pypdf2', 'pdfplumber', или None) / Which library succeeded
            - pages: Количество обнаруженных страниц / Number of pages detected
            - error: Сообщение об ошибке при неудаче / Error message if extraction failed

    Raises:
        FileNotFoundError: Если файл не существует / If the file doesn't exist
        ValueError: Если файл не является валидным PDF / If the file is not a valid PDF

    Examples:
        >>> result = extract_text_from_pdf("resume.pdf")
        >>> print(result["text"])
        'John Doe\\nSoftware Engineer...'
        >>> print(result["method"])
        'pypdf2'
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.suffix.lower() == ".pdf":
        raise ValueError(f"File is not a PDF: {file_path}")

    # Сначала попробуем PyPDF2 (быстрее) / Try PyPDF2 first (faster)
    try:
        result = _extract_with_pypdf2(file_path)
        # Проверим, получили ли мы содержательный контент / Check if we got meaningful content
        text_length = len(result["text"].strip()) if result["text"] else 0

        if text_length > 50 or not use_fallback:
            logger.info(f"Extracted {text_length} chars from {file_path.name} using PyPDF2")
            return result
        else:
            logger.warning(
                f"PyPDF2 extracted minimal text ({text_length} chars), trying pdfplumber"
            )
    except Exception as e:
        logger.warning(f"PyPDF2 extraction failed: {e}")
        if not use_fallback:
            return {
                "text": None,
                "method": None,
                "pages": 0,
                "error": f"PyPDF2 failed: {str(e)}",
            }

    # Запасной вариант - pdfplumber (лучше для сложных макетов) / Fallback to pdfplumber (better for complex layouts)
    if use_fallback:
        try:
            result = _extract_with_pdfplumber(file_path)
            text_length = len(result["text"].strip()) if result["text"] else 0
            logger.info(
                f"Extracted {text_length} chars from {file_path.name} using pdfplumber"
            )
            return result
        except Exception as e:
            logger.error(f"pdfplumber extraction also failed: {e}")
            return {
                "text": None,
                "method": None,
                "pages": 0,
                "error": f"All extraction methods failed: {str(e)}",
            }

    return {
        "text": None,
        "method": None,
        "pages": 0,
        "error": "No extraction method succeeded",
    }


def _extract_with_pypdf2(file_path: Path) -> Dict[str, Optional[str]]:
    """
    Извлечь текст с использованием библиотеки PyPDF2.

    Extract text using PyPDF2 library.

    Args:
        file_path: Путь к PDF файлу / Path to the PDF file

    Returns:
        Словарь с извлеченным текстом и метаданными / Dictionary with extracted text and metadata
    """
    try:
        reader = PdfReader(str(file_path))
        num_pages = len(reader.pages)

        text_parts = []
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            except Exception as e:
                logger.warning(f"Failed to extract page {page_num}: {e}")
                continue

        text = "\n\n".join(text_parts) if text_parts else ""

        return {
            "text": text if text.strip() else None,
            "method": "pypdf2",
            "pages": num_pages,
            "error": None,
        }

    except Exception as e:
        raise RuntimeError(f"PyPDF2 extraction error: {e}") from e


def _extract_with_pdfplumber(file_path: Path) -> Dict[str, Optional[str]]:
    """
    Извлечь текст с использованием библиотеки pdfplumber.

    Pdfplumber более надежен для сложных PDF макетов и лучше обрабатывает
    некоторые граничные случаи чем PyPDF2.

    Extract text using pdfplumber library.

    Pdfplumber is more robust for complex PDF layouts and handles
    some edge cases better than PyPDF2.

    Args:
        file_path: Путь к PDF файлу / Path to the PDF file

    Returns:
        Словарь с извлеченным текстом и метаданными / Dictionary with extracted text and metadata
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            num_pages = len(pdf.pages)
            text_parts = []

            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"pdfplumber failed to extract page {page_num}: {e}")
                    continue

            text = "\n\n".join(text_parts) if text_parts else ""

            return {
                "text": text if text.strip() else None,
                "method": "pdfplumber",
                "pages": num_pages,
                "error": None,
            }

    except Exception as e:
        raise RuntimeError(f"pdfplumber extraction error: {e}") from e


def validate_pdf_file(file_path: Union[str, Path]) -> Dict[str, Union[bool, str]]:
    """
    Валидировать PDF файл перед извлечением текста.

    Validate a PDF file before extraction.

    Проверки:
        - Файл существует / File exists
        - Имеет расширение .pdf / Has .pdf extension
        - Не пустой / Is not empty
        - Может быть открыт PDF библиотеками / Can be opened by PDF libraries

    Args:
        file_path: Путь к PDF файлу / Path to the PDF file

    Returns:
        Словарь с результатами валидации:
            - valid: Булево значение указывающее валидность файла / Boolean indicating if file is valid
            - reason: Строка объясняющая почему валидация не прошла (если применимо) / String explaining why validation failed

    Examples:
        >>> validation = validate_pdf_file("resume.pdf")
        >>> if validation["valid"]:
        ...     print("File is valid")
    """
    file_path = Path(file_path)

    # Проверка существования файла / Check file exists
    if not file_path.exists():
        return {
            "valid": False,
            "reason": f"File does not exist: {file_path}"
        }

    # Проверка расширения / Check extension
    if file_path.suffix.lower() != ".pdf":
        return {
            "valid": False,
            "reason": f"File does not have .pdf extension: {file_path.suffix}"
        }

    # Проверка размера файла / Check file size
    if file_path.stat().st_size == 0:
        return {
            "valid": False,
            "reason": "File is empty (0 bytes)"
        }

    # Проверка что файл может быть открыт / Check file can be opened
    try:
        with pdfplumber.open(file_path) as pdf:
            if len(pdf.pages) == 0:
                return {
                    "valid": False,
                    "reason": "PDF contains no pages"
                }
    except Exception as e:
        return {
            "valid": False,
            "reason": f"Cannot open PDF file: {str(e)}"
        }

    return {"valid": True, "reason": None}
