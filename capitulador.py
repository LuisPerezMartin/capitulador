import logging
import os
import platform
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List

import panflute as pf

from config.config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CapituladorError(Exception):
    pass


class FileHandler:
    @staticmethod
    def read_file(file_path: str, encoding: str = "utf-8") -> str:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                content = file.read()
                logger.info(f"Archivo leído exitosamente: {file_path}")
                return content
        except FileNotFoundError:
            error_msg = f"Archivo no encontrado: {file_path}"
            logger.error(error_msg)
            raise CapituladorError(error_msg)
        except Exception as e:
            error_msg = f"Error leyendo archivo {file_path}: {e}"
            logger.error(error_msg)
            raise CapituladorError(error_msg)
    
    @staticmethod
    def write_file(file_path: str, content: str, encoding: str = "utf-8") -> None:
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "w", encoding=encoding) as file:
                file.write(content)
                logger.info(f"Archivo escrito exitosamente: {file_path}")
        except Exception as e:
            error_msg = f"Error escribiendo archivo {file_path}: {e}"
            logger.error(error_msg)
            raise CapituladorError(error_msg)
    
    @staticmethod
    def ensure_directory_exists(directory: str) -> None:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Directorio asegurado: {directory}")
        except Exception as e:
            error_msg = f"Error creando directorio {directory}: {e}"
            logger.error(error_msg)
            raise CapituladorError(error_msg)


class ContentProcessor:
    @staticmethod
    def process_content(content: str) -> str:
        lines = content.splitlines()
        new_content = []

        for i, line in enumerate(lines):
            if line.strip():
                new_content.append(line)
                if i < len(lines) - 1:
                    if lines[i + 1].strip():
                        new_content.append("")
                    else:
                        skip_lines = ContentProcessor._count_empty_lines(lines, i + 1)
                        ContentProcessor._add_spacing(new_content, skip_lines)

        logger.info("Contenido procesado exitosamente")
        return "\n".join(new_content)
    
    @staticmethod
    def _count_empty_lines(lines: List[str], start_index: int) -> int:
        skip_lines = 0
        j = start_index
        while j < len(lines) and not lines[j].strip():
            skip_lines += 1
            j += 1
        return skip_lines
    
    @staticmethod
    def _add_spacing(content_list: List[str], skip_lines: int) -> None:
        if skip_lines == 1:
            content_list.append("")
        elif skip_lines == 2:
            content_list.extend(["", r"\vspace{12pt}", ""])
        elif skip_lines >= 3:
            content_list.extend(["", r"\newpage", ""])


class LatexConverter:
    @staticmethod
    def convert_to_latex(content: str) -> str:
        try:
            latex_content = pf.convert_text(
                content, 
                input_format="markdown", 
                output_format="latex"
            )
            logger.info("Conversión a LaTeX exitosa")
            return latex_content
        except Exception as e:
            error_msg = f"Error convirtiendo a LaTeX: {e}"
            logger.error(error_msg)
            raise CapituladorError(error_msg)
    
    @staticmethod
    def create_complete_latex_document(content: str) -> str:
        return f"{settings.LATEX_BEGIN}{content}{settings.LATEX_END}"


class PDFGenerator:
    """Genera archivos PDF usando pdflatex."""
    
    @staticmethod
    def generate_pdf() -> None:
        output_directory = "generated"
        
        try:
            result = subprocess.run(
                ["pdflatex", "-output-directory", output_directory, settings.LATEX_FILE],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("PDF generado exitosamente")
        except subprocess.CalledProcessError as e:
            error_msg = f"Error ejecutando pdflatex: {e}"
            logger.error(error_msg)
            raise CapituladorError(error_msg)
        except FileNotFoundError:
            error_msg = "pdflatex no encontrado. Asegúrese de tener LaTeX instalado."
            logger.error(error_msg)
            raise CapituladorError(error_msg)


class BackupManager:
    @staticmethod
    def create_backup() -> str:
        try:
            FileHandler.ensure_directory_exists(settings.BACKUPS_FOLDER)
            
            current_date = datetime.now().strftime("%Y-%m-%d")
            backup_name = f"{current_date}_manuscript.txt"
            backup_path = os.path.join(settings.BACKUPS_FOLDER, backup_name)
            
            shutil.copy(settings.SOURCE_FILE, backup_path)
            logger.info(f"Backup creado: {backup_name}")
            return backup_name
        except Exception as e:
            error_msg = f"Error creando backup: {e}"
            logger.error(error_msg)
            raise CapituladorError(error_msg)


class ChapterGenerator:
    CHAPTER_PATTERN = re.compile(r"^# Chapter \d+")
    
    @staticmethod
    def generate_chapters() -> int:
        try:
            content = FileHandler.read_file(settings.SOURCE_FILE)
            lines = content.splitlines(keepends=True)
            
            FileHandler.ensure_directory_exists("generated/chapters")
            
            chapter_count = 0
            current_chapter = None
            chapter_text = []
            
            for line in lines:
                if ChapterGenerator.CHAPTER_PATTERN.match(line):
                    if current_chapter is not None:
                        ChapterGenerator._write_chapter(chapter_count + 1, chapter_text)
                        chapter_count += 1
                        chapter_text = []
                    current_chapter = line.strip()
                
                chapter_text.append(line)
            
            if current_chapter is not None:
                chapter_count += 1
                ChapterGenerator._write_chapter(chapter_count, chapter_text)
            
            logger.info(f"{chapter_count} capítulos generados")
            return chapter_count
        except Exception as e:
            error_msg = f"Error generando capítulos: {e}"
            logger.error(error_msg)
            raise CapituladorError(error_msg)
    
    @staticmethod
    def _write_chapter(chapter_number: int, chapter_text: List[str]) -> None:
        """Escribe un capítulo individual a un archivo."""
        chapter_path = f"generated/chapters/chapter{chapter_number}.txt"
        content = "".join(chapter_text)
        FileHandler.write_file(chapter_path, content)


class EbookConverter:
    @staticmethod
    def convert_to_ebook() -> None:
        metadata_args = [
            f'--authors="{settings.AUTHORS}"',
            f'--title="{settings.TITLE}"',
            f'--language="{settings.LANGUAGE}"',
            f'--publisher="{settings.PUBLISHER}"',
            f'--comments="{settings.DESCRIPTION}"',
            f'--pubdate="{settings.PUBDATE}"',
            f'--tags="{settings.SUBJECT}"'
        ]

        command = f"ebook-convert {settings.PDF_FILE} {settings.AZW3_FILE} {' '.join(metadata_args)}"

        try:
            subprocess.run(command, shell=True, check=True)
            logger.info("Conversión a AZW3 exitosa")
        except subprocess.CalledProcessError as e:
            error_msg = f"Error convirtiendo a AZW3: {e}"
            logger.error(error_msg)
            raise CapituladorError(error_msg)
        except FileNotFoundError:
            error_msg = "ebook-convert no encontrado. Asegúrese de tener Calibre instalado."
            logger.error(error_msg)
            raise CapituladorError(error_msg)


class SystemCleaner:
    @staticmethod
    def clean_dot_files() -> None:
        if platform.system() == "Darwin":
            try:
                subprocess.run("dot_clean .", shell=True, check=True)
                logger.info("Archivos .DS_Store limpiados")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Error ejecutando dot_clean: {e}")
        else:
            logger.info("Limpieza de archivos .DS_Store omitida (solo macOS)")


class Capitulador:
    def __init__(self):
        self.file_handler = FileHandler()
        self.content_processor = ContentProcessor()
        self.latex_converter = LatexConverter()
        self.pdf_generator = PDFGenerator()
        self.backup_manager = BackupManager()
        self.chapter_generator = ChapterGenerator()
        self.ebook_converter = EbookConverter()
        self.system_cleaner = SystemCleaner()
    
    def process_manuscript(self) -> None:
        try:
            logger.info("Iniciando procesamiento del manuscrito")
            
            # 1. Leer y procesar contenido
            content = self.file_handler.read_file(settings.SOURCE_FILE)
            processed_content = self.content_processor.process_content(content)
            self.file_handler.write_file(settings.WORK_FILE, processed_content)
            
            # 2. Convertir a LaTeX
            latex_content = self.latex_converter.convert_to_latex(processed_content)
            complete_latex = self.latex_converter.create_complete_latex_document(latex_content)
            self.file_handler.write_file(settings.LATEX_FILE, complete_latex)
            
            # 3. Generar PDF
            self.pdf_generator.generate_pdf()
            
            # 4. Crear backup
            backup_name = self.backup_manager.create_backup()
            
            # 5. Generar capítulos
            chapter_count = self.chapter_generator.generate_chapters()
            
            # 6. Convertir a ebook
            self.ebook_converter.convert_to_ebook()
            
            # 7. Limpiar archivos temporales
            self.system_cleaner.clean_dot_files()
            
            logger.info(f"Procesamiento completado exitosamente")
            logger.info(f"Backup: {backup_name} en {settings.BACKUPS_FOLDER}")
            logger.info(f"Capítulos generados: {chapter_count}")
            
        except CapituladorError as e:
            logger.error(f"Error durante el procesamiento: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            raise CapituladorError(f"Error inesperado durante el procesamiento: {e}")


def main() -> None:
    try:
        capitulador = Capitulador()
        capitulador.process_manuscript()
    except CapituladorError as e:
        logger.error(f"Error del Capitulador: {e}")
        exit(1)
    except KeyboardInterrupt:
        logger.info("Procesamiento interrumpido por el usuario")
        exit(1)
    except Exception as e:
        logger.error(f"Error crítico inesperado: {e}")
        exit(1)

if __name__ == "__main__":
    main()