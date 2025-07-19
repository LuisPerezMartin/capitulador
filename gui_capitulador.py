# Professional manuscript editor GUI - Main application interface

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from threading import Thread
import os
import re
import subprocess
from pathlib import Path

from capitulador import Capitulador, CapituladorError
from config.config import settings, BookSettings


class CapituladorGUI:
    # GUI Editor for manuscript processing with multiple export capabilities
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Capitulador")
        self.root.geometry("900x600")
        self.root.minsize(700, 500)
        
        self.file_path = settings.SOURCE_FILE
        self.is_modified = False
        self.capitulador = Capitulador()
        self.book_settings = BookSettings()
        
        self._initialize_ui()
    
    def _initialize_ui(self):
        # Initialize all UI components
        self._create_menu()
        self._create_editor()
        self._create_status_bar()
        self._load_file()
        self._setup_events()
    
    def _create_menu(self):
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Abrir", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Guardar", command=self._save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self._on_closing, accelerator="Ctrl+Q")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Editar", menu=edit_menu)
        edit_menu.add_command(label="Nuevo capítulo", command=self._insert_new_chapter, accelerator="Ctrl+N")
        edit_menu.add_separator()
        edit_menu.add_command(label="Salto de página", command=self._insert_page_break, accelerator="Ctrl+P")
        edit_menu.add_command(label="Espacio de párrafo", command=self._insert_paragraph_space, accelerator="Ctrl+Shift+P")
        
        # Process menu
        process_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Procesar", menu=process_menu)
        process_menu.add_command(label="Todo", command=self._process_all, accelerator="F5")
        process_menu.add_command(label="PDF", command=self._generate_pdf_only, accelerator="F6")
        process_menu.add_command(label="Capítulos", command=self._generate_chapters_only, accelerator="F7")
        process_menu.add_command(label="eBook", command=self._generate_ebook_only, accelerator="F8")
    
    def _create_editor(self):
        # Create main text editor
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
        # Create status bar
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=5)
        
        self.status_var = tk.StringVar(value="Listo")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT)
        
        self.word_count_var = tk.StringVar(value="Palabras: 0")
        self.word_count_label = ttk.Label(status_frame, textvariable=self.word_count_var)
        self.word_count_label.pack(side=tk.RIGHT)
    
    def _setup_events(self):
        # Configure keyboard shortcuts and events
        # File shortcuts
        self.root.bind("<Control-o>", lambda e: self._open_file())
        self.root.bind("<Control-s>", lambda e: self._save_file())
        self.root.bind("<Control-q>", lambda e: self._on_closing())
        
        # Edit shortcuts
        self.root.bind("<Control-n>", lambda e: self._insert_new_chapter())
        self.root.bind("<Control-p>", lambda e: self._insert_page_break())
        self.root.bind("<Control-Shift-P>", lambda e: self._insert_paragraph_space())
        self.root.bind("<Control-z>", self._undo)
        self.root.bind("<Control-y>", self._redo)
        self.root.bind("<Control-Shift-Z>", self._redo)
        
        # Processing shortcuts
        self.root.bind("<F5>", lambda e: self._process_all())
        self.root.bind("<F6>", lambda e: self._generate_pdf_only())
        self.root.bind("<F7>", lambda e: self._generate_chapters_only())
        self.root.bind("<F8>", lambda e: self._generate_ebook_only())
        
        # Window closing
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    # === FILE HANDLING ===
    
    def _load_file(self):
        # Load main manuscript file
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
        # Open existing file
        if not self._check_unsaved_changes():
            return  # User cancelled operation
            
        file_path = filedialog.askopenfilename(
            title="Abrir archivo",
            filetypes=[("Archivos de texto", "*.txt"), ("Archivos Markdown", "*.md"), ("Todos los archivos", "*.*")]
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
                    self.status_var.set(f"Archivo abierto: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}")
                self.status_var.set("Error al abrir archivo")
    
    def _save_file(self):
        # Save current file
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
    
    def _save_current_content(self):
        # Save current content to manuscript file
        try:
            content = self.text_editor.get(1.0, tk.END + "-1c")
            with open(settings.SOURCE_FILE, 'w', encoding='utf-8') as file:
                file.write(content)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
    
    # === INTERFACE FUNCTIONS ===
    
    def _check_unsaved_changes(self):
        # Check for unsaved changes and ask user
        if not self.is_modified:
            return True  # No hay cambios, se puede continuar
            
        result = messagebox.askyesnocancel(
            "Cambios sin guardar",
            "El documento tiene cambios sin guardar.\n¿Desea guardar los cambios antes de continuar?",
            icon="question"
        )
        
        if result is True:  # Usuario quiere guardar
            self._save_file()
            return not self.is_modified  # Continúa solo si se guardó exitosamente
        elif result is False:  # Usuario NO quiere guardar
            return True  # Continúa sin guardar
        else:  # Usuario canceló (result is None)
            return False  # NO continúa
    
    def _on_closing(self):
        # Handle application closing
        if self._check_unsaved_changes():
            self.root.destroy()
    
    def _on_text_change(self, event=None):
        # Handle text changes
        if not self.is_modified:
            self.is_modified = True
            self._update_title()
    
    def _undo(self, event=None):
        # Undo last action
        try:
            self.text_editor.edit_undo()
        except tk.TclError:
            pass
        return "break"
    
    def _redo(self, event=None):
        # Redo last undone action
        try:
            self.text_editor.edit_redo()
        except tk.TclError:
            pass
        return "break"
    
    def _update_title(self):
        # Update window title
        filename = os.path.basename(self.file_path)
        indicator = " *" if self.is_modified else ""
        self.root.title(f"Capitulador - {filename}{indicator}")
    
    def _update_status(self, event=None):
        # Update status bar with word count
        try:
            content = self.text_editor.get(1.0, tk.END + "-1c")
            words = len(re.findall(r'\b\w+\b', content))
            self.word_count_var.set(f"Palabras: {words:,}")
        except:
            self.word_count_var.set("Palabras: 0")
    
    # === EDITING FUNCTIONS ===
    
    def _get_next_chapter_number(self):
        # Calculate next chapter number
        content = self.text_editor.get(1.0, tk.END + "-1c")
        chapter_pattern = r'# Chapter (\d+)'
        chapter_numbers = [int(match.group(1)) for match in re.finditer(chapter_pattern, content)]
        return max(chapter_numbers) + 1 if chapter_numbers else 1
    
    def _insert_new_chapter(self):
        # Insert new chapter template at end of document
        chapter_number = self._get_next_chapter_number()
        chapter_template = f"""

\\newpage

# Chapter {chapter_number}

## Chapter title

## Chapter subtitle

"""
        self.text_editor.insert(tk.END, chapter_template)
        self.text_editor.mark_set(tk.INSERT, tk.END)
        self.text_editor.see(tk.END)
        self._mark_modified()
    
    def _insert_page_break(self):
        # Insert page break at cursor position
        cursor_pos = self.text_editor.index(tk.INSERT)
        self.text_editor.insert(cursor_pos, "\n\n\\newpage\n\n")
        self._mark_modified()
    
    def _insert_paragraph_space(self):
        # Insert paragraph space at cursor position
        cursor_pos = self.text_editor.index(tk.INSERT)
        self.text_editor.insert(cursor_pos, "\n\n\\vspace{12pt}\n\n")
        self._mark_modified()
    
    def _mark_modified(self):
        # Mark document as modified and update interface
        self.is_modified = True
        self._update_title()
        self._update_status()
        self.text_editor.edit_separator()
    
    # === PROCESSING FUNCTIONS ===
    
    def _get_documents_folder(self):
        # Get system Documents folder cross-platform
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Windows Documents folder
            import os
            return Path(os.path.expanduser("~/Documents"))
        elif system == "Darwin":  # macOS
            return Path.home() / "Documents"
        else:  # Linux and other Unix-like systems
            return Path.home() / "Documents"
    
    def _select_output_folder(self):
        # Allow user to select output folder for generated files
        documents_folder = self._get_documents_folder()
        
        folder = filedialog.askdirectory(
            title="Select base folder for generated files",
            initialdir=str(documents_folder)
        )
        if folder:
            # Create folder with book title
            book_settings = BookSettings()
            book_title = book_settings.TITLE.replace(" ", "_").replace("/", "_").replace("\\", "_")
            book_folder = Path(folder) / book_title
            book_folder.mkdir(exist_ok=True)
            return book_folder
        return None
    
    def _cleanup_intermediate_files(self, output_folder):
        # Remove intermediate files after processing
        try:
            intermediate_extensions = ['.aux', '.log', '.toc', '.out', '.fdb_latexmk', '.fls']
            for ext in intermediate_extensions:
                for file in output_folder.glob(f"*{ext}"):
                    file.unlink(missing_ok=True)
        except Exception as e:
            print(f"Warning: Could not remove some intermediate files: {e}")
    
    def _process_all(self):
        # Process everything: PDF, chapters and eBook
        output_folder = self._select_output_folder()
        if output_folder:
            self._save_current_content()
            Thread(target=self._run_process_all, args=(output_folder,), daemon=True).start()
    
    def _generate_pdf_only(self):
        # Generate PDF only
        output_folder = self._select_output_folder()
        if output_folder:
            self._save_current_content()
            Thread(target=self._run_generate_pdf, args=(output_folder,), daemon=True).start()
    
    def _generate_chapters_only(self):
        # Generate chapters only
        output_folder = self._select_output_folder()
        if output_folder:
            self._save_current_content()
            Thread(target=self._run_generate_chapters, args=(output_folder,), daemon=True).start()
    
    def _generate_ebook_only(self):
        # Generate eBook only
        output_folder = self._select_output_folder()
        if output_folder:
            self._save_current_content()
            Thread(target=self._run_generate_ebook, args=(output_folder,), daemon=True).start()
    
    # === THREADED PROCESSING ===
    
    def _run_process_all(self, output_folder):
        # Execute complete processing: LaTeX, PDF, chapters and eBook
        try:
            self.root.after(0, lambda: self.status_var.set("Procesando..."))
            
            # Read and process content
            content = self.capitulador.file_handler.read_file(settings.SOURCE_FILE)
            processed_content = self.capitulador.content_processor.process_content(content)
            
            # Definir archivos de salida
            latex_file = output_folder / f"{self.book_settings.ALIAS}.tex"
            pdf_file = output_folder / f"{self.book_settings.ALIAS}.pdf"
            azw3_file = output_folder / f"{self.book_settings.ALIAS}.azw3"
            
            # Generate LaTeX
            latex_content = self.capitulador.latex_converter.convert_to_latex(processed_content)
            complete_latex = self.capitulador.latex_converter.create_complete_latex_document(latex_content)
            self.capitulador.file_handler.write_file(str(latex_file), complete_latex)
            
            # Generate PDF
            subprocess.run(["pdflatex", "-output-directory", str(output_folder), str(latex_file)], 
                         check=True, capture_output=True, text=True)
            
            # Generate chapters
            chapters_folder = output_folder / "chapters"
            chapters_folder.mkdir(exist_ok=True)
            count = self._generate_chapters_in_folder(processed_content, chapters_folder)
            
            # Generate eBook
            subprocess.run(["ebook-convert", str(pdf_file), str(azw3_file)], 
                         check=True, capture_output=True, text=True)
            
            # Clean intermediate files
            self._cleanup_intermediate_files(output_folder)
            
            self.root.after(0, lambda: self.status_var.set("Completado"))
            self.root.after(0, lambda: messagebox.showinfo("Éxito", 
                f"Archivos generados en:\n{output_folder}\n\nPDF: {pdf_file.name}\neBook: {azw3_file.name}\nCapítulos: {count}"))
        except subprocess.CalledProcessError as e:
            error_msg = f"Error en procesamiento: {e.stderr if e.stderr else str(e)}"
            self.root.after(0, lambda: self.status_var.set("Error"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set("Error"))
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    
    def _run_generate_pdf(self, output_folder):
        # Execute PDF generation only
        try:
            self.root.after(0, lambda: self.status_var.set("Generando PDF..."))
            
            content = self.capitulador.file_handler.read_file(settings.SOURCE_FILE)
            processed_content = self.capitulador.content_processor.process_content(content)
            latex_content = self.capitulador.latex_converter.convert_to_latex(processed_content)
            complete_latex = self.capitulador.latex_converter.create_complete_latex_document(latex_content)
            
            latex_file = output_folder / f"{self.book_settings.ALIAS}.tex"
            self.capitulador.file_handler.write_file(str(latex_file), complete_latex)
            
            subprocess.run(["pdflatex", "-output-directory", str(output_folder), str(latex_file)], 
                         check=True, capture_output=True, text=True)
            
            # Limpiar archivos intermedios
            self._cleanup_intermediate_files(output_folder)
            
            self.root.after(0, lambda: self.status_var.set("PDF generado"))
            self.root.after(0, lambda: messagebox.showinfo("Éxito", f"PDF generado en:\n{output_folder}"))
        except subprocess.CalledProcessError as e:
            error_msg = f"Error generando PDF: {e.stderr if e.stderr else str(e)}"
            self.root.after(0, lambda: self.status_var.set("Error"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set("Error"))
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    
    def _run_generate_chapters(self, output_folder):
        # Execute chapters generation only
        try:
            self.root.after(0, lambda: self.status_var.set("Generando capítulos..."))
            
            content = self.capitulador.file_handler.read_file(settings.SOURCE_FILE)
            processed_content = self.capitulador.content_processor.process_content(content)
            
            chapters_folder = output_folder / "chapters"
            chapters_folder.mkdir(exist_ok=True)
            count = self._generate_chapters_in_folder(processed_content, chapters_folder)
            
            self.root.after(0, lambda: self.status_var.set(f"{count} capítulos generados"))
            self.root.after(0, lambda: messagebox.showinfo("Éxito", 
                f"{count} capítulos generados en:\n{chapters_folder}"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set("Error"))
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    
    def _run_generate_ebook(self, output_folder):
        # Execute eBook generation only
        try:
            self.root.after(0, lambda: self.status_var.set("Generando eBook..."))
            
            content = self.capitulador.file_handler.read_file(settings.SOURCE_FILE)
            processed_content = self.capitulador.content_processor.process_content(content)
            latex_content = self.capitulador.latex_converter.convert_to_latex(processed_content)
            complete_latex = self.capitulador.latex_converter.create_complete_latex_document(latex_content)
            
            latex_file = output_folder / f"{self.book_settings.ALIAS}.tex"
            pdf_file = output_folder / f"{self.book_settings.ALIAS}.pdf"
            azw3_file = output_folder / f"{self.book_settings.ALIAS}.azw3"
            
            self.capitulador.file_handler.write_file(str(latex_file), complete_latex)
            
            subprocess.run(["pdflatex", "-output-directory", str(output_folder), str(latex_file)], 
                         check=True, capture_output=True, text=True)
            subprocess.run(["ebook-convert", str(pdf_file), str(azw3_file)], 
                         check=True, capture_output=True, text=True)
            
            # Limpiar archivos intermedios
            self._cleanup_intermediate_files(output_folder)
            
            self.root.after(0, lambda: self.status_var.set("eBook generado"))
            self.root.after(0, lambda: messagebox.showinfo("Éxito", f"eBook generado en:\n{output_folder}"))
        except subprocess.CalledProcessError as e:
            error_msg = f"Error generando eBook: {e.stderr if e.stderr else str(e)}"
            self.root.after(0, lambda: self.status_var.set("Error"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set("Error"))
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
    
    def _generate_chapters_in_folder(self, content, chapters_folder):
        # Generate chapter files in specified folder
        try:
            chapter_count = 0
            chapter_pattern = r'# Chapter \d+'
            chapters = re.split(chapter_pattern, content)
            
            if len(chapters) > 1:
                chapters = chapters[1:]  # Remover contenido antes del primer capítulo
                
                for i, chapter_content in enumerate(chapters, 1):
                    if chapter_content.strip():
                        chapter_file = chapters_folder / f"chapter{i}.txt"
                        with open(chapter_file, 'w', encoding='utf-8') as f:
                            f.write(f"# Chapter {i}\n{chapter_content.strip()}")
                        chapter_count += 1
            
            return chapter_count
        except Exception as e:
            raise CapituladorError(f"Error generating chapters: {e}")
    
    def run(self):
        # Execute the application
        self.root.mainloop()


def main():
    try:
        app = CapituladorGUI()
        app.run()
    except Exception as e:
        print(f"Error iniciando la aplicación: {e}")


if __name__ == "__main__":
    main()
