import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from threading import Thread
import os
import re
import subprocess
from pathlib import Path

from capitulador import Capitulador
from config.config import settings, BookSettings


class CapituladorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Capitulador")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        self.file_path = None
        self.is_modified = False
        self.capitulador = Capitulador()
        self.book_settings = BookSettings()
        self.animation_job = None
        
        self._setup_ui()
        self._show_welcome_message()
    
    def _setup_ui(self):
        self._create_menu()
        self._create_toolbar()
        self._create_editor()
        self._create_status_bar()
        self._bind_events()
    
    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Abrir", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Guardar", command=self._save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Guardar como...", command=self._save_as_file, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self._close_app, accelerator="Ctrl+Q")
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Editar", menu=edit_menu)
        edit_menu.add_command(label="Metadatos", command=self._edit_metadata, accelerator="Ctrl+M")
        edit_menu.add_command(label="Nuevo capítulo", command=self._insert_chapter, accelerator="Ctrl+N")
        edit_menu.add_command(label="Salto de página", command=self._insert_page_break, accelerator="Ctrl+P")
        
        process_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Procesar", menu=process_menu)
        process_menu.add_command(label="Todo", command=self._process_all, accelerator="F5")
        process_menu.add_command(label="PDF", command=self._generate_pdf, accelerator="F6")
        process_menu.add_command(label="Capítulos", command=self._generate_chapters, accelerator="F7")
        process_menu.add_command(label="eBook", command=self._generate_ebook, accelerator="F8")
    
    def _create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        ttk.Button(toolbar, text="📁 Abrir", command=self._open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Guardar", command=self._save_file).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="📋 Metadatos", command=self._edit_metadata).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📄 Capítulo", command=self._insert_chapter).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="🔄 Todo", command=self._process_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📖 PDF", command=self._generate_pdf).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📚 eBook", command=self._generate_ebook).pack(side=tk.LEFT, padx=2)
    
    def _create_editor(self):
        self.text_editor = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, undo=True, font=("monospace", 11),
            padx=15, pady=15, relief=tk.FLAT, borderwidth=1)
        self.text_editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.text_editor.bind("<Key>", self._on_text_change)
        self.text_editor.bind("<KeyRelease>", self._update_status, add="+")
    
    def _create_status_bar(self):
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        self.status_var = tk.StringVar(value="Listo")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT)
        
        self.word_count_var = tk.StringVar(value="Palabras: 0")
        ttk.Label(status_frame, textvariable=self.word_count_var).pack(side=tk.RIGHT)
    
    def _bind_events(self):
        shortcuts = [
            ("<Control-o>", self._open_file), ("<Control-s>", self._save_file),
            ("<Control-Shift-S>", self._save_as_file), ("<Control-q>", self._close_app), 
            ("<Control-m>", self._edit_metadata), ("<Control-n>", self._insert_chapter), 
            ("<Control-p>", self._insert_page_break), ("<F5>", self._process_all), 
            ("<F6>", self._generate_pdf), ("<F7>", self._generate_chapters), 
            ("<F8>", self._generate_ebook)
        ]
        for key, cmd in shortcuts:
            self.root.bind(key, lambda e, c=cmd: c())
        
        self.root.protocol("WM_DELETE_WINDOW", self._close_app)
    
    def _load_file(self):
        if self.file_path and os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_editor.delete(1.0, tk.END)
                self.text_editor.insert(1.0, content)
                self.is_modified = False
                self._update_title()
                self._update_status()
            except Exception as e:
                self._set_status(f"Error cargando archivo: {e}", "error")
        self._update_status()

    def _show_welcome_message(self):
        """Muestra un mensaje de bienvenida cuando no hay archivo seleccionado"""
        welcome_text = """Bienvenido a Capitulador

Para comenzar, selecciona un archivo de manuscrito:
• Usa Ctrl+O o el menú Archivo > Abrir
• Puedes abrir archivos .txt, .md o cualquier archivo de texto
• El archivo puede estar en cualquier directorio de tu sistema

Una vez abierto el archivo, podrás:
• Editar el texto directamente
• Procesar capítulos automáticamente
• Generar archivos PDF y AZW3
• Configurar metadatos del libro

¡Comienza abriendo tu manuscrito!"""
        
        self.text_editor.delete(1.0, tk.END)
        self.text_editor.insert(1.0, welcome_text)
        self.text_editor.config(state='disabled') 
        self._update_title()
        self._update_status()
    
    def _open_file(self):
        if self.file_path and not self._check_unsaved():
            return
        
        file_path = filedialog.askopenfilename(
            title="Abrir archivo",
            filetypes=[("Archivos de texto", "*.txt"), ("Archivos Markdown", "*.md"), ("Todos", "*.*")])
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_editor.config(state='normal')  # Habilitar edición
                self.text_editor.delete(1.0, tk.END)
                self.text_editor.insert(1.0, content)
                self.file_path = file_path
                self.is_modified = False
                self._update_title()
                self._update_status()
                self._set_status(f"Archivo abierto: {os.path.basename(file_path)}", "success")
            except Exception as e:
                self._set_status(f"Error abriendo archivo: {e}", "error")
    
    def _save_file(self):
        if not self.file_path:
            # Si no hay archivo seleccionado, abrir diálogo "Guardar como"
            file_path = filedialog.asksaveasfilename(
                title="Guardar archivo",
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Archivos Markdown", "*.md"), ("Todos", "*.*")])
            
            if not file_path:
                return
            self.file_path = file_path
            
        try:
            content = self.text_editor.get(1.0, tk.END + "-1c")
            Path(self.file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.is_modified = False
            self._update_title()
            self._set_status("Archivo guardado", "success")
        except Exception as e:
            self._set_status(f"Error guardando: {e}", "error")

    def _save_as_file(self):
        """Guardar archivo con un nombre diferente"""
        file_path = filedialog.asksaveasfilename(
            title="Guardar archivo como",
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Archivos Markdown", "*.md"), ("Todos", "*.*")])
        
        if file_path:
            try:
                content = self.text_editor.get(1.0, tk.END + "-1c")
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.file_path = file_path
                self.is_modified = False
                self._update_title()
                self._set_status(f"Archivo guardado como: {os.path.basename(file_path)}", "success")
            except Exception as e:
                self._set_status(f"Error guardando: {e}", "error")
    
    def _check_unsaved(self):
        if not self.file_path or not self.is_modified:
            return True
        
        result = messagebox.askyesnocancel(
            "Cambios sin guardar",
            "¿Guardar cambios antes de continuar?")
        
        if result is True:
            self._save_file()
            return not self.is_modified
        return result is False
    
    def _close_app(self):
        if self.animation_job:
            self.root.after_cancel(self.animation_job)
        if self._check_unsaved():
            self.root.destroy()
    
    def _on_text_change(self, event=None):
        # Solo marcar como modificado si hay un archivo seleccionado
        if self.file_path and not self.is_modified:
            self.is_modified = True
            self._update_title()
    
    def _update_title(self):
        if self.file_path:
            filename = os.path.basename(self.file_path)
            indicator = " *" if self.is_modified else ""
            self.root.title(f"Capitulador - {filename}{indicator}")
        else:
            self.root.title("Capitulador - Sin archivo")
    
    def _update_status(self, event=None):
        try:
            content = self.text_editor.get(1.0, tk.END + "-1c")
            words = len(re.findall(r'\b\w+\b', content))
            self.word_count_var.set(f"Palabras: {words:,}")
        except:
            self.word_count_var.set("Palabras: 0")
    
    def _set_status(self, message, status_type="normal"):
        self.status_var.set(message)
    
    def _animate_status(self, base_text):
        if not hasattr(self, '_animation_running') or not self._animation_running:
            return
        
        dots = "." * (getattr(self, '_animation_dots', 0) + 1)
        self._set_status(f"{base_text}{dots}", "processing")
        self._animation_dots = (getattr(self, '_animation_dots', 0) + 1) % 3
        self.animation_job = self.root.after(500, lambda: self._animate_status(base_text))
    
    def _start_animation(self, text):
        self._animation_running = True
        self._animation_dots = 0
        self._animate_status(text)
    
    def _stop_animation(self):
        self._animation_running = False
        if self.animation_job:
            self.root.after_cancel(self.animation_job)
    
    def _edit_metadata(self):
        window = tk.Toplevel(self.root)
        window.title("Metadatos del Libro")
        window.geometry("500x400")
        window.transient(self.root)
        window.grab_set()
        
        main_frame = ttk.Frame(window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        fields = {}
        field_names = [
            ("Título:", 'title', self.book_settings.TITLE),
            ("Alias:", 'alias', self.book_settings.ALIAS),
            ("Autor(es):", 'authors', self.book_settings.AUTHORS),
            ("Idioma:", 'language', self.book_settings.LANGUAGE),
            ("Editorial:", 'publisher', self.book_settings.PUBLISHER),
            ("Fecha:", 'pubdate', self.book_settings.PUBDATE),
            ("Etiquetas:", 'subject', self.book_settings.SUBJECT),
            ("ID:", 'identifier', self.book_settings.IDENTIFIER)
        ]
        
        for i, (label, key, value) in enumerate(field_names):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky="w", pady=5)
            fields[key] = tk.StringVar(value=value)
            ttk.Entry(main_frame, textvariable=fields[key], width=40).grid(row=i, column=1, pady=5, padx=10)
        
        ttk.Label(main_frame, text="Descripción:").grid(row=len(field_names), column=0, sticky="nw", pady=5)
        desc_text = tk.Text(main_frame, width=35, height=4)
        desc_text.grid(row=len(field_names), column=1, pady=5, padx=10)
        desc_text.insert(1.0, self.book_settings.DESCRIPTION)
        
        def save_metadata():
            try:
                env_file = Path("config/dev.env")
                new_values = {k: v.get() for k, v in fields.items()}
                new_values['DESCRIPTION'] = desc_text.get(1.0, tk.END + "-1c")
                
                content = []
                if env_file.exists():
                    with open(env_file, 'r', encoding='utf-8') as f:
                        content = f.readlines()
                
                updated = []
                keys_updated = set()
                
                for line in content:
                    if '=' in line and not line.strip().startswith('#'):
                        key = line.split('=')[0].strip()
                        if key in new_values:
                            updated.append(f"{key}={new_values[key]}\n")
                            keys_updated.add(key)
                        else:
                            updated.append(line)
                    else:
                        updated.append(line)
                
                for key, value in new_values.items():
                    if key not in keys_updated:
                        updated.append(f"{key.upper()}={value}\n")
                
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.writelines(updated)
                
                self.book_settings = BookSettings()
                self._set_status("Metadatos actualizados", "success")
                window.destroy()
            except Exception as e:
                self._set_status(f"Error guardando metadatos: {e}", "error")
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(field_names)+1, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Guardar", command=save_metadata).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=window.destroy).pack(side=tk.LEFT, padx=5)
    
    def _insert_chapter(self):
        content = self.text_editor.get(1.0, tk.END + "-1c")
        chapter_numbers = [int(m.group(1)) for m in re.finditer(r'# Chapter (\d+)', content)]
        next_number = max(chapter_numbers) + 1 if chapter_numbers else 1
        
        template = f"\n\n\\newpage\n\n# Chapter {next_number}\n\n## Chapter title\n\n"
        self.text_editor.insert(tk.END, template)
        self.text_editor.see(tk.END)
        self._mark_modified()
    
    def _insert_page_break(self):
        pos = self.text_editor.index(tk.INSERT)
        self.text_editor.insert(pos, "\n\n\\newpage\n\n")
        self._mark_modified()
    
    def _mark_modified(self):
        self.is_modified = True
        self._update_title()
        self._update_status()

    def _validate_file_selected(self):
        """Valida que hay un archivo seleccionado y muestra mensaje si no"""
        if not self.file_path:
            messagebox.showwarning(
                "Sin archivo",
                "Primero debes abrir un archivo de manuscrito.\n\nUsa Ctrl+O o el menú Archivo > Abrir para seleccionar tu archivo.")
            return False
        return True

    def _get_current_content(self):
        """Obtiene el contenido actual del editor y lo guarda si hay cambios"""
        if self.is_modified:
            # Guardar cambios automáticamente antes de procesar
            self._save_file()
        # Leer el contenido del archivo para asegurar consistencia
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _get_output_folder(self):
        import platform
        system = platform.system()
        
        if system == "Windows":
            documents_folder = Path.home() / "Documents"
        elif system == "Darwin":  # macOS
            documents_folder = Path.home() / "Documents"
        else:  # Linux and other Unix-like systems
            documents_folder = Path.home() / "Documents"
        
        folder = filedialog.askdirectory(
            title="Seleccionar carpeta de salida",
            initialdir=str(documents_folder))
        
        if folder:
            book_title = self.book_settings.TITLE.replace(" ", "_").replace("/", "_").replace("\\", "_")
            output_path = Path(folder) / book_title
            output_path.mkdir(exist_ok=True)
            return output_path
        return None
    
    def _cleanup_files(self, output_folder):
        for ext in ['.aux', '.log', '.toc', '.out', '.fdb_latexmk', '.fls']:
            for file in output_folder.glob(f"*{ext}"):
                file.unlink(missing_ok=True)
    
    def _save_current_content(self):
        content = self.text_editor.get(1.0, tk.END + "-1c")
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _process_all(self):
        if not self._validate_file_selected():
            return
        output_folder = self._get_output_folder()
        if output_folder:
            self._save_current_content()
            Thread(target=self._run_process_all, args=(output_folder,), daemon=True).start()
    
    def _generate_pdf(self):
        if not self._validate_file_selected():
            return
        output_folder = self._get_output_folder()
        if output_folder:
            self._save_current_content()
            Thread(target=self._run_generate_pdf, args=(output_folder,), daemon=True).start()
    
    def _generate_chapters(self):
        if not self._validate_file_selected():
            return
        output_folder = self._get_output_folder()
        if output_folder:
            self._save_current_content()
            Thread(target=self._run_generate_chapters, args=(output_folder,), daemon=True).start()
    
    def _generate_ebook(self):
        if not self._validate_file_selected():
            return
        output_folder = self._get_output_folder()
        if output_folder:
            self._save_current_content()
            Thread(target=self._run_generate_ebook, args=(output_folder,), daemon=True).start()
    
    def _run_process_all(self, output_folder):
        try:
            self.root.after(0, lambda: self._start_animation("Procesando"))
            
            content = self._get_current_content()
            processed = self.capitulador.content_processor.process_content(content)
            
            latex_file = output_folder / f"{self.book_settings.ALIAS}.tex"
            pdf_file = output_folder / f"{self.book_settings.ALIAS}.pdf"
            azw3_file = output_folder / f"{self.book_settings.ALIAS}.azw3"
            
            latex_content = self.capitulador.latex_converter.convert_to_latex(processed)
            complete_latex = self.capitulador.latex_converter.create_complete_latex_document(latex_content)
            self.capitulador.file_handler.write_file(str(latex_file), complete_latex)
            
            subprocess.run(["pdflatex", "-output-directory", str(output_folder), str(latex_file)], 
                         check=True, capture_output=True, text=True)
            
            chapters_folder = output_folder / "chapters"
            chapters_folder.mkdir(exist_ok=True)
            count = self._generate_chapters_in_folder(processed, chapters_folder)
            
            subprocess.run(["ebook-convert", str(pdf_file), str(azw3_file)], 
                         check=True, capture_output=True, text=True)
            
            manuscript_dest = output_folder / "manuscript.txt"
            with open(self.file_path, 'r', encoding='utf-8') as src, \
                 open(manuscript_dest, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
            
            self._cleanup_files(output_folder)
            
            self.root.after(0, lambda: self._stop_animation())
            self.root.after(0, lambda: self._set_status(f"Completado: PDF, eBook, {count} capítulos", "success"))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._stop_animation())
            self.root.after(0, lambda: self._set_status(f"Error: {error_msg}", "error"))
    
    def _run_generate_pdf(self, output_folder):
        try:
            self.root.after(0, lambda: self._start_animation("Generando PDF"))
            
            content = self._get_current_content()
            processed = self.capitulador.content_processor.process_content(content)
            latex_content = self.capitulador.latex_converter.convert_to_latex(processed)
            complete_latex = self.capitulador.latex_converter.create_complete_latex_document(latex_content)
            
            latex_file = output_folder / f"{self.book_settings.ALIAS}.tex"
            self.capitulador.file_handler.write_file(str(latex_file), complete_latex)
            
            subprocess.run(["pdflatex", "-output-directory", str(output_folder), str(latex_file)], 
                         check=True, capture_output=True, text=True)
            
            self._cleanup_files(output_folder)
            
            self.root.after(0, lambda: self._stop_animation())
            self.root.after(0, lambda: self._set_status("PDF generado correctamente", "success"))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._stop_animation())
            self.root.after(0, lambda: self._set_status(f"Error generando PDF: {error_msg}", "error"))
    
    def _run_generate_chapters(self, output_folder):
        try:
            self.root.after(0, lambda: self._start_animation("Generando capítulos"))
            
            content = self._get_current_content()
            processed = self.capitulador.content_processor.process_content(content)
            
            chapters_folder = output_folder / "chapters"
            chapters_folder.mkdir(exist_ok=True)
            count = self._generate_chapters_in_folder(processed, chapters_folder)
            
            self.root.after(0, lambda: self._stop_animation())
            self.root.after(0, lambda: self._set_status(f"{count} capítulos generados", "success"))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._stop_animation())
            self.root.after(0, lambda: self._set_status(f"Error generando capítulos: {error_msg}", "error"))
    
    def _run_generate_ebook(self, output_folder):
        try:
            self.root.after(0, lambda: self._start_animation("Generando eBook"))
            
            content = self._get_current_content()
            processed = self.capitulador.content_processor.process_content(content)
            latex_content = self.capitulador.latex_converter.convert_to_latex(processed)
            complete_latex = self.capitulador.latex_converter.create_complete_latex_document(latex_content)
            
            latex_file = output_folder / f"{self.book_settings.ALIAS}.tex"
            pdf_file = output_folder / f"{self.book_settings.ALIAS}.pdf"
            azw3_file = output_folder / f"{self.book_settings.ALIAS}.azw3"
            
            self.capitulador.file_handler.write_file(str(latex_file), complete_latex)
            
            subprocess.run(["pdflatex", "-output-directory", str(output_folder), str(latex_file)], 
                         check=True, capture_output=True, text=True)
            subprocess.run(["ebook-convert", str(pdf_file), str(azw3_file)], 
                         check=True, capture_output=True, text=True)
            
            self._cleanup_files(output_folder)
            
            self.root.after(0, lambda: self._stop_animation())
            self.root.after(0, lambda: self._set_status("eBook generado correctamente", "success"))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._stop_animation())
            self.root.after(0, lambda: self._set_status(f"Error generando eBook: {error_msg}", "error"))
    
    def _generate_chapters_in_folder(self, content, chapters_folder):
        chapter_count = 0
        chapters = re.split(r'# Chapter \d+', content)
        
        if len(chapters) > 1:
            chapters = chapters[1:]
            for i, chapter_content in enumerate(chapters, 1):
                if chapter_content.strip():
                    chapter_file = chapters_folder / f"chapter{i}.txt"
                    with open(chapter_file, 'w', encoding='utf-8') as f:
                        f.write(f"# Chapter {i}\n{chapter_content.strip()}")
                    chapter_count += 1
        
        return chapter_count
    
    def run(self):
        self.root.mainloop()


def main():
    app = CapituladorGUI()
    app.run()


if __name__ == "__main__":
    main()
