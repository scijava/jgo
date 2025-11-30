"""
JVM configuration for jgo 2.0.

Handles JVM arguments like heap size, GC options, and system properties.
"""

from typing import List, Optional, Dict
import psutil


class JVMConfig:
    """
    Configuration for JVM execution.

    Handles memory settings, GC options, system properties, and other JVM arguments.
    """

    def __init__(
        self,
        max_heap: Optional[str] = None,
        min_heap: Optional[str] = None,
        gc_options: Optional[List[str]] = None,
        system_properties: Optional[Dict[str, str]] = None,
        extra_args: Optional[List[str]] = None,
        auto_heap: bool = True,
        default_gc: str = "-XX:+UseG1GC",
    ):
        """
        Initialize JVM configuration.

        Args:
            max_heap: Maximum heap size (e.g., "2G", "512M"). If None and auto_heap=True,
                     auto-detects based on system memory.
            min_heap: Minimum heap size (e.g., "512M")
            gc_options: Garbage collection options (e.g., ["-XX:+UseG1GC"])
            system_properties: System properties as dict (e.g., {"foo": "bar"} -> -Dfoo=bar)
            extra_args: Additional JVM arguments
            auto_heap: If True and max_heap is None, auto-detect max heap size
            default_gc: Default GC option to use if gc_options is None
        """
        self.max_heap = max_heap
        self.min_heap = min_heap
        self.gc_options = gc_options or []
        self.system_properties = system_properties or {}
        self.extra_args = extra_args or []
        self.auto_heap = auto_heap
        self.default_gc = default_gc

    def to_jvm_args(self) -> List[str]:
        """
        Convert configuration to JVM arguments list.

        Returns:
            List of JVM arguments suitable for java command
        """
        args = []

        # Add GC options
        gc_args = (
            self.gc_options
            if self.gc_options
            else ([self.default_gc] if self.default_gc else [])
        )
        args.extend(gc_args)

        # Add heap settings
        if self.min_heap:
            args.append(f"-Xms{self.min_heap}")

        max_heap = self.max_heap
        if max_heap is None and self.auto_heap:
            max_heap = self._auto_detect_max_heap()

        if max_heap:
            args.append(f"-Xmx{max_heap}")

        # Add system properties
        for key, value in self.system_properties.items():
            args.append(f"-D{key}={value}")

        # Add extra args
        args.extend(self.extra_args)

        return args

    def _auto_detect_max_heap(self) -> str:
        """
        Auto-detect maximum heap size based on system memory.

        Sets max heap to half of system memory, rounded to a reasonable value.
        Uses GB for systems with >2GB RAM, MB otherwise.

        Returns:
            Heap size string (e.g., "2G", "512M")
        """
        total_memory = psutil.virtual_memory().total

        # Use GB for systems with >2GB, otherwise MB
        if total_memory > 2 * 1024**3:
            # GB mode
            max_heap_gb = max(total_memory // (1024**3) // 2, 1)
            return f"{max_heap_gb}G"
        else:
            # MB mode
            max_heap_mb = max(total_memory // (1024**2) // 2, 1)
            return f"{max_heap_mb}M"

    def with_system_property(self, key: str, value: str) -> "JVMConfig":
        """
        Return a new JVMConfig with an additional system property.

        Args:
            key: Property key
            value: Property value

        Returns:
            New JVMConfig instance
        """
        new_props = self.system_properties.copy()
        new_props[key] = value

        return JVMConfig(
            max_heap=self.max_heap,
            min_heap=self.min_heap,
            gc_options=self.gc_options.copy(),
            system_properties=new_props,
            extra_args=self.extra_args.copy(),
            auto_heap=self.auto_heap,
            default_gc=self.default_gc,
        )

    def with_extra_arg(self, arg: str) -> "JVMConfig":
        """
        Return a new JVMConfig with an additional JVM argument.

        Args:
            arg: JVM argument to add

        Returns:
            New JVMConfig instance
        """
        new_args = self.extra_args.copy()
        new_args.append(arg)

        return JVMConfig(
            max_heap=self.max_heap,
            min_heap=self.min_heap,
            gc_options=self.gc_options.copy(),
            system_properties=self.system_properties.copy(),
            extra_args=new_args,
            auto_heap=self.auto_heap,
            default_gc=self.default_gc,
        )
