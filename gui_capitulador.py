# Interfaz gráfica minimalista para el Capitulador

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from threading import Thread
import os
import re
from pathlib import Path

from capitulador import Capitulador
from config.config import settings


class CapituladorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Capitulador")
        self.root.geometry("900x600")
        self.root.minsize(700, 500)
        
        self.file_path = settings.SOURCE_FILE
        self.is_modified = False
        self.capitulador = Capitulador()
        
        self._create_menu()
        self._create_editor()
        self._create_status_bar()
        self._load_file()
        self._setup_events()
    
    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Abrir", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Guardar", command=self._save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self._on_closing, accelerator="Ctrl+Q")
        
        # Menú Editar
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Editar", menu=edit_menu)
        edit_menu.add_command(label="Nuevo capítulo", command=self._insert_new_chapter, accelerator="Ctrl+N")
        
        # Menú Procesar
        process_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Procesar", menu=process_menu)
        process_menu.add_command(label="Todo", command=self._process_all, accelerator="F5")
        process_menu.add_command(label="PDF", command=self._generate_pdf_only, accelerator="F6")
        process_menu.add_command(label="Capítulos", command=self._generate_chapters_only, accelerator="F7")
        process_menu.add_command(label="eBook", command=self._generate_ebook_only, accelerator="F8")
    
    def _create_editor(self):
        self.text_editor = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            undo=True,
            autoseparators=True,
            font=("monospace", 10),
            padx=10,
            pady=10,
            relief=tk.FLAT,
            borderwidth=0
        )
        self.text_editor.pack(fill=tk.BOTH, expand=True, padx=10)
        self.text_editor.bind("<Key>", self._on_text_change)
        self.text_editor.bind("<KeyRelease>", self._update_status, add="+")
    
    def _create_status_bar(self):
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=5)
        
        self.status_var = tk.StringVar(value="Listo")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT)
        
        self.word_count_var = tk.StringVar(value="Palabras: 0")
        self.word_count_label = ttk.Label(status_frame, textvariable=self.word_count_var)
        self.word_count_label.pack(side=tk.RIGHT)
    
    def _setup_events(self):
        # Atajos de teclado para archivo
        self.root.bind("<Control-o>", lambda e: self._open_file())
        self.root.bind("<Control-s>", lambda e: self._save_file())
        self.root.bind("<Control-q>", lambda e: self._on_closing())
        
        # Atajos de teclado para edición
        self.root.bind("<Control-n>", lambda e: self._insert_new_chapter())
        self.root.bind("<Control-z>", self._undo)
        self.root.bind("<Control-y>", self._redo)
        self.root.bind("<Control-Shift-Z>", self._redo)
        
        # Atajos de teclado para procesamiento
        self.root.bind("<F5>", lambda e: self._process_all())
        self.root.bind("<F6>", lambda e: self._generate_pdf_only())
        self.root.bind("<F7>", lambda e: self._generate_chapters_only())
        self.root.bind("<F8>", lambda e: self._generate_ebook_only())
        
        # Manejo del cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _load_file(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.text_editor.delete(1.0, tk.END)
                    self.text_editor.insert(1.0, content)
                    self.text_editor.edit_separator()
                    self.is_modified = False
                    self._update_title()
                    self._update_status()
            except Exception as e:
                self.text_editor.delete(1.0, tk.END)
                messagebox.showerror("Error", f"No se pudo cargar: {e}")
        else:
            self.text_editor.delete(1.0, tk.END)
            self._update_status()
    
    def _open_file(self):
        if not self._check_unsaved_changes():
            return
            
        file_path = filedialog.askopenfilename(
            filetypes=[("Archivos de texto", "*.txt"), ("Archivos Markdown", "*.md")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.text_editor.delete(1.0, tk.END)
                    self.text_editor.insert(1.0, content)
                    self.text_editor.edit_separator()
                    self.file_path = file_path
                    self.is_modified = False
                    self._update_title()
                    self._update_status()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir: {e}")
    
    def _save_file(self):
        try:
            content = self.text_editor.get(1.0, tk.END + "-1c")
            Path(self.file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            self.is_modified = False
            self._update_title()
            self.status_var.set("Guardado")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
    
    def _check_unsaved_changes(self):
        # Verifica si hay cambios sin guardar y pregunta al usuario qué hacer
        if self.is_modified:
            result = messagebox.askyesnocancel(
                "Cambios sin guardar",
                "¿Desea guardar los cambios antes de continuar?"
            )
            if result is True:
                self._save_file()
                return not self.is_modified
            elif result is False:
                return True
            else:
                return False
        return True
    
    def _on_closing(self):
        # Maneja el cierre de la aplicación con verificación de cambios
        if self._check_unsaved_changes():
            self.root.destroy()
    
    def _on_text_change(self, event=None):
        if not self.is_modified:
            self.is_modified = True
            self._update_title()
    
    def _undo(self, event=None):
        try:
            self.text_editor.edit_undo()
        except tk.TclError:
            pass
        return "break"
    
    def _redo(self, event=None):
        try:
            self.text_editor.edit_redo()
        except tk.TclError:
            pass
        return "break"
    
    def _update_title(self):
        filename = os.path.basename(self.file_path)
        indicator = " *" if self.is_modified else ""
        self.root.title(f"Capitulador - {filename}{indicator}")
    
    def _update_status(self, event=None):
        try:
            content = self.text_editor.get(1.0, tk.END + "-1c")
            words = len(re.findall(r'\b\w+\b', content))
            self.word_count_var.set(f"Palabras: {words:,}")
        except:
            self.word_count_var.set("Palabras: 0")
    
    def _get_next_chapter_number(self):
        # Calcula el siguiente número de capítulo basado en el contenido actual
        content = self.text_editor.get(1.0, tk.END + "-1c")
        
        # Buscar patrones de capítulos existentes (# Chapter X)
        chapter_pattern = r'# Chapter (\d+)'
        chapter_numbers = []
        
        for match in re.finditer(chapter_pattern, content):
            chapter_numbers.append(int(match.group(1)))
        
        # Retornar el siguiente número de capítulo
        if chapter_numbers:
            return max(chapter_numbers) + 1
        else:
            return 1
    
    def _insert_new_chapter(self):
        # Inserta una nueva plantilla de capítulo al final del documento
        chapter_number = self._get_next_chapter_number()
        
        chapter_template = f"""
        
\\newpage

# Chapter {chapter_number}

## Chapter title

## Chapter subtitle

"""
        
        # Insertar al final del documento
        self.text_editor.insert(tk.END, chapter_template)
        
        # Mover el cursor al final del documento
        self.text_editor.mark_set(tk.INSERT, tk.END)
        self.text_editor.see(tk.END)
        
        # Marcar como modificado
        self.is_modified = True
        self._update_title()
        self._update_status()
        
        # Crear separador en el historial de undo
        self.text_editor.edit_separator()
    
    def _save_current_content(self):
        # Guarda el contenido actual al archivo de manuscrito
        try:
            content = self.text_editor.get(1.0, tk.END + "-1c")
            with open(settings.SOURCE_FILE, 'w', encoding='utf-8') as file:
                file.write(content)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
    
    # Funciones de procesamiento en hilos separados
    def _process_all(self):
        self._save_current_content()
        Thread(target=self._run_process_all, daemon=True).start()
    
    def _generate_pdf_only(self):
        self._save_current_content()
        Thread(target=self._run_generate_pdf, daemon=True).start()
    
    def _generate_chapters_only(self):
        self._save_current_content()
        Thread(target=self._run_generate_chapters, daemon=True).start()
    
    def _generate_ebook_only(self):
        self._save_current_content()
        Thread(target=self._run_generate_ebook, daemon=True).start()
    
    def _run_process_all(self):
        try:
            self.root.after(0, lambda: self.status_var.set("Procesando..."))
            self.capitulador.process_manuscript()
            self.root.after(0, lambda: self.status_var.set("Completado"))
            self.root.after(0, lambda: messagebox.showinfo("Éxito", "Procesado exitosamente"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)[:50]}"))
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    
    def _run_generate_pdf(self):
        try:
            self.root.after(0, lambda: self.status_var.set("Generando PDF..."))
            content = self.capitulador.file_handler.read_file(settings.SOURCE_FILE)
            processed_content = self.capitulador.content_processor.process_content(content)
            latex_content = self.capitulador.latex_converter.convert_to_latex(processed_content)
            complete_latex = self.capitulador.latex_converter.create_complete_latex_document(latex_content)
            self.capitulador.file_handler.write_file(settings.LATEX_FILE, complete_latex)
            self.capitulador.pdf_generator.generate_pdf()
            self.root.after(0, lambda: self.status_var.set("PDF generado"))
            self.root.after(0, lambda: messagebox.showinfo("Éxito", "PDF generado"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)[:50]}"))
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    
    def _run_generate_chapters(self):
        try:
            self.root.after(0, lambda: self.status_var.set("Generando capítulos..."))
            count = self.capitulador.chapter_generator.generate_chapters()
            self.root.after(0, lambda: self.status_var.set(f"{count} capítulos generados"))
            self.root.after(0, lambda: messagebox.showinfo("Éxito", f"{count} capítulos generados"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)[:50]}"))
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    
    def _run_generate_ebook(self):
        try:
            self.root.after(0, lambda: self.status_var.set("Generando eBook..."))
            content = self.capitulador.file_handler.read_file(settings.SOURCE_FILE)
            processed_content = self.capitulador.content_processor.process_content(content)
            latex_content = self.capitulador.latex_converter.convert_to_latex(processed_content)
            complete_latex = self.capitulador.latex_converter.create_complete_latex_document(latex_content)
            self.capitulador.file_handler.write_file(settings.LATEX_FILE, complete_latex)
            self.capitulador.pdf_generator.generate_pdf()
            self.capitulador.ebook_converter.convert_to_ebook()
            self.root.after(0, lambda: self.status_var.set("eBook generado"))
            self.root.after(0, lambda: messagebox.showinfo("Éxito", "eBook generado"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)[:50]}"))
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    
    def run(self):
        self.root.mainloop()


def main():
    try:
        app = CapituladorGUI()
        app.run()
    except Exception as e:
        print(f"Error iniciando la aplicación: {e}")


if __name__ == "__main__":
    main()
