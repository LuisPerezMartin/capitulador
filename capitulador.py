import panflute as pf
import os
import shutil
import subprocess
import re
from datetime import datetime

from config.config import settings

def processContent(content):
    lines = content.splitlines()
    new_content = []

    for i, linea in enumerate(lines):
        if linea.strip():
            new_content.append(linea)
            if i < len(lines) - 1:
                if lines[i + 1].strip():
                    new_content.append("")
                else:
                    j = i + 1
                    skip_lines = 0
                    while j < len(lines) and not lines[j].strip():
                        skip_lines += 1
                        j += 1
                    if skip_lines == 1:
                        new_content.append("")
                    if skip_lines == 2:
                        new_content.extend(["", r"\vspace{12pt}", ""])
                    elif skip_lines >= 3:
                        new_content.extend(["", r"\newpage", ""])

    return "\n".join(new_content)

with open(settings.SOURCE_FILE, "r", encoding="utf-8") as file:
    dev_content = file.read()

content_work = processContent(dev_content)

with open(settings.WORK_FILE, "w", encoding="utf-8") as file:
    file.write(content_work)

latex_content = pf.convert_text(content_work, input_format="markdown", output_format="latex")

with open(settings.LATEX_FILE, "w", encoding="utf-8") as latex_file:
    latex_file.write(settings.LATEX_BEGIN)
    latex_file.write(latex_content)
    latex_file.write(settings.LATEX_END)

output_directory = "generated"
subprocess.run(["pdflatex", "-output-directory", output_directory, settings.LATEX_FILE], check=True)

print("LaTeX conversion finished")

subprocess.run(["mkdir", "-p", settings.BACKUPS_FOLDER], check=True)

current_date = datetime.now().strftime("%Y-%m-%d")
backup_name = f"{current_date}_manuscript.txt"
shutil.copy(settings.SOURCE_FILE, os.path.join(settings.BACKUPS_FOLDER, backup_name))

with open(settings.SOURCE_FILE, "r", encoding="utf-8") as archivo:
    lines = archivo.readlines()

chapter_count = 0
capitulo = None
capitulo_text = []
chapter_pattern = re.compile(r"^# Chapter \d+")

with open(settings.SOURCE_FILE, "r", encoding="utf-8") as file:
    lines = file.readlines()

for line in lines:
    if chapter_pattern.match(line):
        if capitulo is not None:
            with open(f"generated/chapters/chapter{chapter_count+1}.txt", "w", encoding="utf-8") as capitulo_file:
                capitulo_file.writelines(capitulo_text)
            chapter_count += 1
            capitulo_text = []
        capitulo = line.strip()
        capitulo_text.append(line)
    else:
        capitulo_text.append(line)

chapter_count += 1
if capitulo is not None:
    with open(f"generated/chapters/chapter{chapter_count}.txt", "w", encoding="utf-8") as capitulo_file:
        capitulo_file.writelines(capitulo_text)


print(f"{chapter_count} Chapter files generated")
print(f"Backup {backup_name} in {settings.BACKUPS_FOLDER}")

metadata = {
    "authors": "Luis Pérez Martín",
    "title": "Los Machistas del Campo de Margaritas",
    "language": "es",
    "publisher": "Editorial XYZ",
    "description": "Una descripción del libro.",
    "identifier": "ISBN-123456789",
    "pubdate": current_date,
    "subject": "Ficción",
    "pages": "200",
    "cover": "ruta_a_la_portada.jpg",
    "comments": "Comentarios del lector"
}

metadata_args = " ".join([f"--metadata {key}=\"{value}\"" for key, value in metadata.items()])

command = f"ebook-convert {settings.PDF_FILE} {settings.AZW3_FILE}"

subprocess.run(command, shell=True)

subprocess.run("dot_clean .", shell=True)