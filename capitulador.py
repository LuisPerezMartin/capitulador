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

    for i, line in enumerate(lines):
        if line.strip():
            new_content.append(line)
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

def read_source_file():
    try:
        with open(settings.SOURCE_FILE, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        print(f"Error reading source file: {e}")
        exit(1)

def write_work_file(content):
    try:
        with open(settings.WORK_FILE, "w", encoding="utf-8") as file:
            file.write(content)
    except Exception as e:
        print(f"Error writing work file: {e}")
        exit(1)

def convert_to_latex(content):
    try:
        return pf.convert_text(content, input_format="markdown", output_format="latex")
    except Exception as e:
        print(f"Error converting to LaTeX: {e}")
        exit(1)

def write_latex_file(content):
    try:
        with open(settings.LATEX_FILE, "w", encoding="utf-8") as latex_file:
            latex_file.write(settings.LATEX_BEGIN)
            latex_file.write(content)
            latex_file.write(settings.LATEX_END)
    except Exception as e:
        print(f"Error writing LaTeX file: {e}")
        exit(1)

def generate_pdf():
    output_directory = "generated"
    try:
        subprocess.run(["pdflatex", "-output-directory", output_directory, settings.LATEX_FILE], check=True)
        print("LaTeX conversion finished")
    except subprocess.CalledProcessError as e:
        print(f"Error running pdflatex: {e}")
        exit(1)

def create_backup():
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
    return backup_name

def generate_chapters():
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

def convert_to_ebook():
    metadata_args = [
        f"--authors=\"{settings.AUTHORS}\"",
        f"--title=\"{settings.TITLE}\"",
        f"--language=\"{settings.LANGUAGE}\"",
        f"--publisher=\"{settings.PUBLISHER}\"",
        f"--comments=\"{settings.DESCRIPTION}\"",
        f"--pubdate=\"{settings.PUBDATE}\"",
        f"--tags=\"{settings.SUBJECT}\""
    ]

    command = f"ebook-convert {settings.PDF_FILE} {settings.AZW3_FILE} {' '.join(metadata_args)}"

    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error converting to AZW3: {e}")
        exit(1)

def clean_dot_files():
    import platform
    # dot_clean is a macOS-only command
    if platform.system() == "Darwin":
        try:
            subprocess.run("dot_clean .", shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running dot_clean: {e}")
            exit(1)
    else:
        print("Skipping dot_clean (macOS only command)")

def main():
    content = read_source_file()
    content_work = processContent(content)
    write_work_file(content_work)
    latex_content = convert_to_latex(content_work)
    write_latex_file(latex_content)
    generate_pdf()
    backup = create_backup()
    generate_chapters()
    print(f"Backup {backup} in {settings.BACKUPS_FOLDER}")
    convert_to_ebook()
    clean_dot_files()

if __name__ == "__main__":
    main()