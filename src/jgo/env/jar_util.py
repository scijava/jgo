"""
Utilities for working with JAR files.
"""

from pathlib import Path
from typing import Optional
import re
import zipfile


def detect_main_class_from_jar(jar_path: Path) -> Optional[str]:
    """
    Detect the Main-Class from a JAR file's MANIFEST.MF.

    Args:
        jar_path: Path to JAR file

    Returns:
        Main class name if found in manifest, None otherwise
    """
    try:
        with zipfile.ZipFile(jar_path) as jar_file:
            try:
                with jar_file.open("META-INF/MANIFEST.MF") as manifest:
                    main_class_pattern = re.compile(r".*Main-Class:\s*")
                    main_class = None
                    for line in manifest.readlines():
                        line = line.strip().decode("utf-8")
                        if main_class_pattern.match(line):
                            main_class = main_class_pattern.sub("", line)
                            break
                    return main_class
            except KeyError:
                # No MANIFEST.MF in this JAR
                return None
    except (zipfile.BadZipFile, FileNotFoundError):
        return None
