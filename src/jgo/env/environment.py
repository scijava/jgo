"""
Environment class for jgo 2.0.

An environment is a materialized directory containing JAR files ready for
execution.
"""

from pathlib import Path
from typing import List, Optional
import json

class Environment:
    """
    A materialized Maven environment - a directory containing JARs.
    """

    def __init__(self, path: Path):
        self.path = path
        self._manifest = None

    @property
    def manifest_path(self) -> Path:
        return self.path / "manifest.json"

    @property
    def manifest(self) -> dict:
        """Load manifest.json with metadata about this environment."""
        if self._manifest is None:
            if self.manifest_path.exists():
                with open(self.manifest_path) as f:
                    self._manifest = json.load(f)
            else:
                self._manifest = {}
        return self._manifest

    def save_manifest(self):
        """Save manifest.json."""
        with open(self.manifest_path, 'w') as f:
            json.dump(self._manifest, f, indent=2)

    @property
    def classpath(self) -> List[Path]:
        """List of JAR files in this environment."""
        jars_dir = self.path / "jars"
        if not jars_dir.exists():
            return []
        return sorted(jars_dir.glob("*.jar"))

    @property
    def main_class(self) -> Optional[str]:
        """Main class for this environment (if detected/specified)."""
        main_class_file = self.path / "main-class.txt"
        if main_class_file.exists():
            return main_class_file.read_text().strip()
        return self.manifest.get("main_class")

    def set_main_class(self, main_class: str):
        """Set the main class for this environment."""
        main_class_file = self.path / "main-class.txt"
        main_class_file.write_text(main_class)
        self.manifest["main_class"] = main_class
        self.save_manifest()
