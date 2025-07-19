from pydantic_settings import BaseSettings


class CommonSettings(BaseSettings):
    PROGRAM_NAME: str = 'Capitulador'
    PROGRAM_VERSION: str = '0.0.1'
    DEBUG_MODE: bool = False
    ENV: str = 'dev'


class BookSettings(BaseSettings):
    TITLE: str
    ALIAS: str
    AUTHORS: str
    LANGUAGE: str
    PUBLISHER: str
    DESCRIPTION: str
    IDENTIFIER: str
    PUBDATE: str
    SUBJECT: str
    PAGES: str
    COVER: str
    COMMENTS: str

    class Config:
        env_file = f'config/{CommonSettings().ENV}.env'


class PathSettings(BaseSettings):
    SOURCE_FILE: str = "manuscript/manuscript.txt"
    @property
    def AZW3_FILE(self) -> str:
        return f"generated/{BookSettings().ALIAS}.azw3"
    @property
    def LATEX_FILE(self) -> str:
        return f"generated/{BookSettings().ALIAS}.tex"
    @property
    def PDF_FILE(self) -> str:
        return f"generated/{BookSettings().ALIAS}.pdf"
    @property
    def AUX_FILE(self) -> str:
        return f"generated/{BookSettings().ALIAS}.aux"
    @property
    def LOG_FILE(self) -> str:
        return f"generated/{BookSettings().ALIAS}.log"
    BACKUPS_FOLDER: str = "generated/backups"


class LaTexSettings(BaseSettings):
    LATEX_BEGIN: str = r"""
\pdfminorversion=4
\documentclass[]{book}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[utf8]{inputenc}
\usepackage[spanish]{babel}
\usepackage{amssymb,latexsym,amsmath}
\usepackage[a4paper,top=3cm,bottom=2cm,left=3cm,right=3cm,marginparwidth=1.75cm]{geometry}
\usepackage{graphicx}
\usepackage{bookmark}
\usepackage{titlesec}

\titleformat{\section}[block]{\normalfont\Large\bfseries}{}{0pt}{}
\titleformat{\subsection}[block]{\normalfont\large\bfseries}{}{0pt}{}
\titleformat{\subsubsection}[block]{\normalfont\large\bfseries}{}{0pt}{}

\begin{document}

"""
    LATEX_END: str = r"""

\end{document}
"""


class Settings(CommonSettings, LaTexSettings, PathSettings, BookSettings):
    class Config:
        env_file = f'config/{CommonSettings().ENV}.env'


settings = Settings()