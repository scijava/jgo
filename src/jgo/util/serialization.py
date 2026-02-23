"""
TOML serialization mixins.

Provides reusable serialization/deserialization capabilities for TOML files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, ClassVar, TypeVar

import tomli_w

from .toml import tomllib

_T = TypeVar("_T", bound="TOMLSerializableMixin")


class TOMLSerializableMixin:
    """
    Mixin providing TOML serialization/deserialization capabilities.

    Classes using this mixin must implement:
    - _to_dict(self) -> dict
    - _from_dict(cls, data: dict, path: Path | None = None) -> Self

    Optional overrides:
    - _validate_loaded_data(cls, data: dict, path: Path) -> None
    """

    # Override to customize error messages
    FILE_NOT_FOUND_MESSAGE: ClassVar[str] = "{class_name} not found: {path}"
    PARSE_ERROR_MESSAGE: ClassVar[str] = "Failed to parse {path}: {error}"
    VALIDATION_ERROR_MESSAGE: ClassVar[str] = "Invalid {class_name} in {path}: {error}"

    @classmethod
    def load(cls: type[_T], path: Path | str) -> _T:
        """Load instance from a TOML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                cls.FILE_NOT_FOUND_MESSAGE.format(class_name=cls.__name__, path=path)
            )

        # Parse TOML
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise ValueError(cls.PARSE_ERROR_MESSAGE.format(path=path, error=e)) from e

        # Validate and deserialize
        try:
            if hasattr(cls, "_validate_loaded_data"):
                cls._validate_loaded_data(data, path)  # type: ignore[attr-defined]

            return cls._from_dict(data, path)
        except Exception as e:
            raise ValueError(
                cls.VALIDATION_ERROR_MESSAGE.format(
                    class_name=cls.__name__, path=path, error=e
                )
            ) from e

    def save(self, path: Path | str) -> None:
        """Save instance to a TOML file."""
        path = Path(path)
        data = self._to_dict()

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:
            tomli_w.dump(data, f)

    # Abstract methods - subclasses must implement
    def _to_dict(self) -> dict:
        """Convert instance to dict for TOML serialization."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _to_dict()"
        )

    @classmethod
    def _from_dict(cls: type[_T], data: dict, path: Path | None = None) -> _T:
        """Create instance from parsed TOML dict."""
        raise NotImplementedError(f"{cls.__name__} must implement _from_dict()")

    @staticmethod
    def _parse_entrypoints_section(
        data: dict,
    ) -> tuple[dict[str, str], str | None]:
        """
        Parse [entrypoints] section from TOML data.

        Validates that if "default" exists, it references another entrypoint name
        and is not itself being used as an entrypoint.

        Returns:
            tuple of (entrypoints dict, default_entrypoint name)

        Raises:
            ValueError: If "default" appears to be used as an entrypoint name
        """
        entrypoints_section = data.get("entrypoints", {})

        # If "default" exists, check if it looks like an entrypoint name or a reference
        default_value = entrypoints_section.get("default")
        if default_value is not None:
            # If default_value contains a dot, it's likely a main class (entrypoint),
            # not a reference to another entrypoint name
            if "." in str(default_value):
                raise ValueError(
                    'Entrypoint name "default" is reserved for specifying the default entrypoint. '
                    f'The value "{default_value}" appears to be a main class. '
                    "Create a named entrypoint and reference it: "
                    'e.g., main = "{}", default = "main"'.format(default_value)
                )

        default_entrypoint = entrypoints_section.pop("default", None)
        entrypoints = entrypoints_section
        return entrypoints, default_entrypoint

    @staticmethod
    def _serialize_entrypoints_section(
        entrypoints: dict[str, str],
        default_entrypoint: str | None,
    ) -> dict[str, str]:
        """
        Serialize entrypoints to TOML section dict.

        Args:
            entrypoints: Dict of entrypoint_name -> main_class
            default_entrypoint: Name of default entrypoint (optional)

        Returns:
            Dict ready for TOML serialization
        """
        entrypoints_section = dict(entrypoints)
        if default_entrypoint:
            entrypoints_section["default"] = default_entrypoint
        return entrypoints_section


class FieldValidatorMixin:
    """Provides common validation patterns for TOML deserialization."""

    @staticmethod
    def validate_required(data: dict, field: str, context: str = "data") -> Any:
        """Validate that a required field exists."""
        if field not in data or data[field] is None:
            raise ValueError(f"Missing required field '{field}' in {context}")
        return data[field]

    @staticmethod
    def validate_type(
        value: Any,
        expected_type: type | tuple[type, ...],
        field_name: str,
        context: str = "field",
    ) -> None:
        """Validate that a value has the expected type."""
        if not isinstance(value, expected_type):
            expected = (
                expected_type.__name__
                if isinstance(expected_type, type)
                else " or ".join(t.__name__ for t in expected_type)
            )
            actual = type(value).__name__
            raise ValueError(
                f"{context} '{field_name}' must be {expected}, got {actual}"
            )

    @staticmethod
    def validate_list_items(
        items: list,
        validator: Callable[[Any], None],
        field_name: str,
    ) -> None:
        """Validate each item in a list."""
        for i, item in enumerate(items):
            try:
                validator(item)
            except ValueError as e:
                raise ValueError(
                    f"Invalid item at index {i} in '{field_name}': {e}"
                ) from e

    @staticmethod
    def validate_choice(
        value: Any,
        choices: tuple | list | set,
        field_name: str,
    ) -> None:
        """Validate that a value is one of allowed choices."""
        if value not in choices:
            choices_str = ", ".join(str(c) for c in choices)
            raise ValueError(
                f"Invalid value for '{field_name}': '{value}'. "
                f"Expected one of: {choices_str}"
            )
