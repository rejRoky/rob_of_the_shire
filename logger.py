"""
Logging system for Rob of the Shire game.

Provides centralized logging configuration with both file and console handlers.
Supports different log levels and formatted output for debugging and monitoring.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from functools import wraps
from time import perf_counter

from config import config


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds color coding to log messages for console output.
    
    Uses ANSI escape codes for terminal coloring based on log level.
    """
    
    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with appropriate coloring."""
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Format the message
        formatted = super().format(record)
        
        # Apply color to level name
        if record.levelname in self.COLORS:
            formatted = formatted.replace(
                record.levelname,
                f"{color}{self.BOLD}{record.levelname}{self.RESET}"
            )
        
        return formatted


class GameLogger:
    """
    Centralized game logging system.
    
    Provides a singleton logger instance with configurable handlers for
    file and console output. Supports structured logging with context.
    
    Attributes:
        logger: The underlying logging.Logger instance.
        log_file: Path to the current log file.
    """
    
    _instance: Optional['GameLogger'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'GameLogger':
        """Ensure singleton pattern for logger."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the logging system (only runs once)."""
        if GameLogger._initialized:
            return
        
        self.logger = logging.getLogger("RobOfTheShire")
        self.logger.setLevel(logging.DEBUG)
        self.log_file = Path(config.LOG_FILE)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        GameLogger._initialized = True
        self.info("Logging system initialized")
    
    def _setup_handlers(self) -> None:
        """Configure file and console handlers."""
        # File handler - detailed logging
        file_handler = logging.FileHandler(
            self.log_file, 
            mode='a', 
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler - info and above
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_formatter = ColoredFormatter(
            "%(levelname)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def set_console_level(self, level: int) -> None:
        """Change the console logging level."""
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(level)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with optional context."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message with optional context."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with optional context."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message with optional context."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with optional context."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, exc_info: bool = True, **kwargs) -> None:
        """Log exception with traceback."""
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs) -> None:
        """Internal logging method with context handling."""
        exc_info = kwargs.pop('exc_info', False)
        
        if kwargs:
            context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            message = f"{message} [{context}]"
        
        self.logger.log(level, message, exc_info=exc_info)
    
    def log_combat_action(
        self, 
        attacker: str, 
        defender: str, 
        damage: int, 
        weapon: str
    ) -> None:
        """Log a combat action with structured data."""
        self.info(
            f"Combat: {attacker} attacks {defender}",
            weapon=weapon,
            damage=damage
        )
    
    def log_item_action(
        self, 
        character: str, 
        action: str, 
        item: str,
        effect: Optional[str] = None
    ) -> None:
        """Log an item-related action."""
        msg = f"Item: {character} {action} {item}"
        if effect:
            msg += f" - {effect}"
        self.info(msg)
    
    def log_save_action(
        self, 
        action: str, 
        character: str, 
        file_path: str
    ) -> None:
        """Log a save/load action."""
        self.info(f"Save System: {action} character '{character}'", file=file_path)
    
    def log_level_up(
        self, 
        character: str, 
        old_level: int, 
        new_level: int
    ) -> None:
        """Log character level up."""
        self.info(
            f"Level Up: {character}",
            old_level=old_level,
            new_level=new_level
        )


def log_execution_time(func):
    """
    Decorator to log function execution time.
    
    Useful for performance monitoring and optimization.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        start_time = perf_counter()
        
        try:
            result = func(*args, **kwargs)
            elapsed = perf_counter() - start_time
            logger.debug(f"Function '{func.__name__}' executed in {elapsed:.4f}s")
            return result
        except Exception as e:
            elapsed = perf_counter() - start_time
            logger.error(
                f"Function '{func.__name__}' failed after {elapsed:.4f}s",
                error=str(e)
            )
            raise
    
    return wrapper


def log_function_call(func):
    """
    Decorator to log function entry and exit.
    
    Logs function name and arguments on entry, return value on exit.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        func_name = func.__name__
        
        # Log entry
        args_repr = [repr(a) for a in args[:3]]  # Limit args logged
        kwargs_repr = [f"{k}={v!r}" for k, v in list(kwargs.items())[:3]]
        signature = ", ".join(args_repr + kwargs_repr)
        logger.debug(f"Entering {func_name}({signature})")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Exiting {func_name} -> success")
            return result
        except Exception as e:
            logger.debug(f"Exiting {func_name} -> exception: {type(e).__name__}")
            raise
    
    return wrapper


def get_logger() -> GameLogger:
    """
    Get the singleton game logger instance.
    
    Returns:
        The GameLogger singleton instance.
    """
    return GameLogger()


# Module-level convenience functions
def debug(message: str, **kwargs) -> None:
    """Log debug message."""
    get_logger().debug(message, **kwargs)


def info(message: str, **kwargs) -> None:
    """Log info message."""
    get_logger().info(message, **kwargs)


def warning(message: str, **kwargs) -> None:
    """Log warning message."""
    get_logger().warning(message, **kwargs)


def error(message: str, **kwargs) -> None:
    """Log error message."""
    get_logger().error(message, **kwargs)


def critical(message: str, **kwargs) -> None:
    """Log critical message."""
    get_logger().critical(message, **kwargs)
