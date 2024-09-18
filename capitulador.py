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

try:
    with open(settings.SOURCE_FILE, "r", encoding="utf-8") as file:
        dev_content = file.read()
except Exception as e:
    print(f"Error reading source file: {e}")
    exit(1)

content_work = processContent(dev_content)

try:
    with open(settings.WORK_FILE, "w", encoding="utf-8") as file:
        file.write(content_work)
except Exception as e:
    print(f"Error writing work file: {e}")
    exit(1)

try:
    latex_content = pf.convert_text(content_work, input_format="markdown", output_format="latex")
except Exception as e:
    print(f"Error converting to LaTeX: {e}")
    exit(1)

try:
    with open(settings.LATEX_FILE, "w", encoding="utf-8") as latex_file:
        latex_file.write(settings.LATEX_BEGIN)
        latex_file.write(latex_content)
        latex_file.write(settings.LATEX_END)
except Exception as e:
    print(f"Error writing LaTeX file: {e}")
    exit(1)

output_directory = "generated"
try:
    subprocess.run(["pdflatex", "-output-directory", output_directory, settings.LATEX_FILE], check=True)
    print("LaTeX conversion finished")
except subprocess.CalledProcessError as e:
    print(f"Error running pdflatex: {e}")
    exit(1)

try:
    subprocess.run(["mkdir", "-p", settings.BACKUPS_FOLDER], check=True)
except subprocess.CalledProcessError as e:
    print(f"Error creating backups folder: {e}")
    exit(1)

current_date = datetime.now().strftime("%Y-%m-%d")
backup_name = f"{current_date}_manuscript.txt"
try:
    shutil.copy(settings.SOURCE_FILE, os.path.join(settings.BACKUPS_FOLDER, backup_name))
except Exception as e:
    print(f"Error copying backup file: {e}")
    exit(1)

try:
    with open(settings.SOURCE_FILE, "r", encoding="utf-8") as archivo:
        lines = archivo.readlines()
except Exception as e:
    print(f"Error reading source file for chapters: {e}")
    exit(1)

chapter_count = 0
capitulo = None
capitulo_text = []
chapter_pattern = re.compile(r"^# Chapter \d+")

for line in lines:
    if chapter_pattern.match(line):
        if capitulo is not None:
            try:
                with open(f"generated/chapters/chapter{chapter_count+1}.txt", "w", encoding="utf-8") as capitulo_file:
                    capitulo_file.writelines(capitulo_text)
            except Exception as e:
                print(f"Error writing chapter file: {e}")
                exit(1)
            chapter_count += 1
            capitulo_text = []
        capitulo = line.strip()
        capitulo_text.append(line)
    else:
        capitulo_text.append(line)

chapter_count += 1
if capitulo is not None:
    try:
        with open(f"generated/chapters/chapter{chapter_count}.txt", "w", encoding="utf-8") as capitulo_file:
            capitulo_file.writelines(capitulo_text)
    except Exception as e:
        print(f"Error writing final chapter file: {e}")
        exit(1)

print(f"{chapter_count} Chapter files generated")
print(f"Backup {backup_name} in {settings.BACKUPS_FOLDER}")

metadata = {
    "authors": "",
    "title": "",
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

try:
    subprocess.run(command, shell=True, check=True)
except subprocess.CalledProcessError as e:
    print(f"Error converting to AZW3: {e}")
    exit(1)

try:
    subprocess.run("dot_clean .", shell=True, check=True)
except subprocess.CalledProcessError as e:
    print(f"Error running dot_clean: {e}")
    exit(1)