#!/usr/bin/env python3

import shutil
from pathlib import Path
from datetime import datetime, timedelta


def cleanup_project():
    project_root = Path(__file__).parent
    
    cleanup_patterns = [
        "**/__pycache__", "**/*.pyc", "**/*.pyo", "**/*.pyd", "**/.DS_Store",
        "**/.vscode", "**/*.aux", "**/*.log", "**/*.toc", "**/*.out",
        "**/*.fdb_latexmk", "**/*.fls", "**/*.synctex.gz"
    ]
    
    cleaned_count = 0
    
    for pattern in cleanup_patterns:
        for item in project_root.glob(pattern):
            try:
                if item.is_file():
                    item.unlink()
                    print(f"Eliminado archivo: {item}")
                    cleaned_count += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    print(f"Eliminado directorio: {item}")
                    cleaned_count += 1
            except Exception as e:
                print(f"Error eliminando {item}: {e}")
    
    backup_folder = project_root / "generated" / "backups"
    if backup_folder.exists():
        cutoff_date = datetime.now() - timedelta(days=30)
        for backup_file in backup_folder.glob("*.txt"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                try:
                    backup_file.unlink()
                    print(f"Eliminado backup antiguo: {backup_file}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"Error eliminando backup {backup_file}: {e}")
    
    print(f"\n✅ Limpieza completada. {cleaned_count} elementos eliminados.")


if __name__ == "__main__":
    cleanup_project()
