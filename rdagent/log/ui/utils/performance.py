"""Performance optimization utilities for RD-Agent UI."""

import functools
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

import pandas as pd
import streamlit as st


class CacheManager:
    """Manages caching for expensive operations."""

    @staticmethod
    def create_cache_key(*args, **kwargs) -> str:
        """Create a unique cache key from arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Unique cache key string
        """
        # Convert args and kwargs to string representation
        key_data = {
            "args": [str(arg) for arg in args],
            "kwargs": {k: str(v) for k, v in kwargs.items()}
        }

        # Create hash of the key data
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    @staticmethod
    def cached_file_operation(ttl_hours: int = 1):
        """Decorator for caching file operations.

        Args:
            ttl_hours: Time to live in hours

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            @st.cache_data(ttl=ttl_hours * 3600, show_spinner="Loading data...")
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def cached_dataframe_operation(ttl_minutes: int = 30):
        """Decorator for caching DataFrame operations.

        Args:
            ttl_minutes: Time to live in minutes

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            @st.cache_data(ttl=ttl_minutes * 60, show_spinner="Processing data...")
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def cached_computation(ttl_minutes: int = 15):
        """Decorator for caching expensive computations.

        Args:
            ttl_minutes: Time to live in minutes

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            @st.cache_data(ttl=ttl_minutes * 60, show_spinner="Computing...")
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator


class LazyLoader:
    """Handles lazy loading of data."""

    def __init__(self, load_func: Callable, *args, **kwargs):
        """Initialize lazy loader.

        Args:
            load_func: Function to call for loading data
            *args: Arguments for load function
            **kwargs: Keyword arguments for load function
        """
        self.load_func = load_func
        self.args = args
        self.kwargs = kwargs
        self._data: Optional[Any] = None
        self._loaded = False

    def load(self) -> Any:
        """Load data if not already loaded.

        Returns:
            Loaded data
        """
        if not self._loaded:
            self._data = self.load_func(*self.args, **self.kwargs)
            self._loaded = True
        return self._data

    @property
    def data(self) -> Any:
        """Get data, loading if necessary."""
        return self.load()

    def reset(self):
        """Reset loader to unloaded state."""
        self._data = None
        self._loaded = False


class ProgressTracker:
    """Tracks progress for long-running operations."""

    def __init__(self, total_steps: int, description: str = "Processing"):
        """Initialize progress tracker.

        Args:
            total_steps: Total number of steps
            description: Description of the operation
        """
        self.total_steps = total_steps
        self.description = description
        self.current_step = 0
        self.start_time = time.time()
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()

    def update(self, step: int, status: str = ""):
        """Update progress.

        Args:
            step: Current step number
            status: Status message
        """
        self.current_step = step
        progress = min(step / self.total_steps, 1.0)
        self.progress_bar.progress(progress)

        elapsed_time = time.time() - self.start_time
        if step > 0:
            estimated_total = elapsed_time / step * self.total_steps
            remaining_time = estimated_total - elapsed_time
            time_info = f" (ETA: {remaining_time:.1f}s)"
        else:
            time_info = ""

        self.status_text.text(f"{self.description}: {step}/{self.total_steps}{time_info} {status}")

    def finish(self, message: str = "Complete"):
        """Mark progress as finished.

        Args:
            message: Completion message
        """
        self.progress_bar.progress(1.0)
        elapsed_time = time.time() - self.start_time
        self.status_text.text(f"{message} (took {elapsed_time:.1f}s)")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.finish()
        else:
            self.status_text.text("Operation failed")


class MemoryManager:
    """Manages memory usage for large datasets."""

    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage.

        Args:
            df: DataFrame to optimize

        Returns:
            Memory-optimized DataFrame
        """
        optimized_df = df.copy()

        # Optimize numeric columns
        for col in optimized_df.select_dtypes(include=['int64']).columns:
            col_min = optimized_df[col].min()
            col_max = optimized_df[col].max()

            if col_min >= -128 and col_max <= 127:
                optimized_df[col] = optimized_df[col].astype('int8')
            elif col_min >= -32768 and col_max <= 32767:
                optimized_df[col] = optimized_df[col].astype('int16')
            elif col_min >= -2147483648 and col_max <= 2147483647:
                optimized_df[col] = optimized_df[col].astype('int32')

        # Optimize float columns
        for col in optimized_df.select_dtypes(include=['float64']).columns:
            optimized_df[col] = pd.to_numeric(optimized_df[col], downcast='float')

        # Optimize object columns
        for col in optimized_df.select_dtypes(include=['object']).columns:
            if optimized_df[col].nunique() / len(optimized_df) < 0.5:
                optimized_df[col] = optimized_df[col].astype('category')

        return optimized_df

    @staticmethod
    def get_memory_usage(obj: Any) -> Dict[str, Union[int, str]]:
        """Get memory usage information for an object.

        Args:
            obj: Object to analyze

        Returns:
            Dictionary with memory usage info
        """
        if isinstance(obj, pd.DataFrame):
            memory_usage = obj.memory_usage(deep=True).sum()
            return {
                "total_bytes": memory_usage,
                "human_readable": f"{memory_usage / 1024 / 1024:.2f} MB",
                "type": "DataFrame",
                "shape": str(obj.shape)
            }
        else:
            import sys
            size = sys.getsizeof(obj)
            return {
                "total_bytes": size,
                "human_readable": f"{size / 1024:.2f} KB",
                "type": type(obj).__name__
            }


class BatchProcessor:
    """Processes data in batches to manage memory."""

    def __init__(self, batch_size: int = 1000):
        """Initialize batch processor.

        Args:
            batch_size: Size of each batch
        """
        self.batch_size = batch_size

    def process_dataframe(self, df: pd.DataFrame, process_func: Callable) -> pd.DataFrame:
        """Process DataFrame in batches.

        Args:
            df: DataFrame to process
            process_func: Function to apply to each batch

        Returns:
            Processed DataFrame
        """
        if len(df) <= self.batch_size:
            return process_func(df)

        results = []
        total_batches = len(df) // self.batch_size + (1 if len(df) % self.batch_size else 0)

        with ProgressTracker(total_batches, "Processing batches") as progress:
            for i in range(0, len(df), self.batch_size):
                batch = df.iloc[i:i + self.batch_size]
                processed_batch = process_func(batch)
                results.append(processed_batch)
                progress.update(len(results))

        return pd.concat(results, ignore_index=True)

    def process_list(self, items: list, process_func: Callable) -> list:
        """Process list in batches.

        Args:
            items: List to process
            process_func: Function to apply to each batch

        Returns:
            Processed results list
        """
        if len(items) <= self.batch_size:
            return process_func(items)

        results = []
        total_batches = len(items) // self.batch_size + (1 if len(items) % self.batch_size else 0)

        with ProgressTracker(total_batches, "Processing batches") as progress:
            for i in range(0, len(items), self.batch_size):
                batch = items[i:i + self.batch_size]
                processed_batch = process_func(batch)
                results.extend(processed_batch if isinstance(processed_batch, list) else [processed_batch])
                progress.update(len(results) // self.batch_size + 1)

        return results


# Pre-configured cache decorators for common use cases
cache_file_operations = CacheManager.cached_file_operation(ttl_hours=2)
cache_dataframe_operations = CacheManager.cached_dataframe_operation(ttl_minutes=30)
cache_computations = CacheManager.cached_computation(ttl_minutes=15)