"""
Enhanced Error Handling and Recovery Module for UnQTube

This module provides comprehensive error handling, automatic recovery mechanisms,
and detailed error reporting for robust video generation.
"""

import os
import sys
import traceback
import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from functools import wraps
import asyncio

class UnQTubeLogger:
    """Enhanced logging system for UnQTube"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.setup_logging()
        
    def setup_logging(self):
        """Setup comprehensive logging system"""
        # Create logs directory
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configure logging
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Main logger
        self.logger = logging.getLogger('UnQTube')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler for all logs
        file_handler = logging.FileHandler(
            os.path.join(self.log_dir, f'unqtube_{datetime.now().strftime("%Y%m%d")}.log')
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Error file handler
        error_handler = logging.FileHandler(
            os.path.join(self.log_dir, f'errors_{datetime.now().strftime("%Y%m%d")}.log')
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(log_format))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
    def log_error(self, error: Exception, context: str = "", additional_info: Dict = None):
        """Log detailed error information"""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "additional_info": additional_info or {}
        }
        
        self.logger.error(f"ERROR in {context}: {error}")
        self.logger.debug(f"Full error details: {json.dumps(error_info, indent=2)}")
        
        return error_info
        
    def log_recovery(self, context: str, recovery_action: str, success: bool):
        """Log recovery attempt results"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"RECOVERY {status} in {context}: {recovery_action}")

class ErrorRecovery:
    """Automatic error recovery mechanisms"""
    
    def __init__(self, logger: UnQTubeLogger):
        self.logger = logger
        self.recovery_strategies = {
            "api_error": self._recover_api_error,
            "file_error": self._recover_file_error,
            "network_error": self._recover_network_error,
            "memory_error": self._recover_memory_error,
            "timeout_error": self._recover_timeout_error
        }
        
    def _recover_api_error(self, error: Exception, context: Dict) -> bool:
        """Recover from API-related errors"""
        error_msg = str(error).lower()
        
        if "rate limit" in error_msg or "429" in error_msg:
            # Rate limit recovery
            wait_time = context.get("retry_delay", 30)
            self.logger.logger.info(f"Rate limit detected. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            return True
            
        elif "unauthorized" in error_msg or "401" in error_msg:
            # API key issue
            self.logger.logger.error("API authentication failed. Please check your API keys.")
            return False
            
        elif "network" in error_msg or "connection" in error_msg:
            # Network connectivity issue
            self.logger.logger.info("Network issue detected. Retrying in 10 seconds...")
            time.sleep(10)
            return True
            
        return False
        
    def _recover_file_error(self, error: Exception, context: Dict) -> bool:
        """Recover from file-related errors"""
        error_msg = str(error).lower()
        
        if "permission" in error_msg:
            # Permission error
            file_path = context.get("file_path", "")
            try:
                if file_path and os.path.exists(file_path):
                    os.chmod(file_path, 0o666)
                    return True
            except:
                pass
                
        elif "disk space" in error_msg or "no space" in error_msg:
            # Disk space issue
            self._cleanup_temp_files()
            return True
            
        elif "file not found" in error_msg:
            # Missing file
            file_path = context.get("file_path", "")
            if file_path:
                # Try to recreate directory
                try:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    return True
                except:
                    pass
                    
        return False
        
    def _recover_network_error(self, error: Exception, context: Dict) -> bool:
        """Recover from network-related errors"""
        # Wait and retry for network issues
        retry_delay = context.get("retry_delay", 5)
        max_retries = context.get("max_retries", 3)
        current_retry = context.get("current_retry", 0)
        
        if current_retry < max_retries:
            self.logger.logger.info(f"Network error. Retrying in {retry_delay} seconds... (attempt {current_retry + 1}/{max_retries})")
            time.sleep(retry_delay)
            return True
            
        return False
        
    def _recover_memory_error(self, error: Exception, context: Dict) -> bool:
        """Recover from memory-related errors"""
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Try to reduce video quality if applicable
        video_settings = context.get("video_settings", {})
        if "quality" in video_settings and video_settings["quality"] > 480:
            video_settings["quality"] = 480
            self.logger.logger.info("Reduced video quality to 480p due to memory constraints")
            return True
            
        return False
        
    def _recover_timeout_error(self, error: Exception, context: Dict) -> bool:
        """Recover from timeout errors"""
        # Increase timeout for next attempt
        current_timeout = context.get("timeout", 30)
        new_timeout = min(current_timeout * 2, 300)  # Max 5 minutes
        context["timeout"] = new_timeout
        
        self.logger.logger.info(f"Timeout occurred. Increasing timeout to {new_timeout} seconds")
        return True
        
    def _cleanup_temp_files(self):
        """Clean up temporary files to free space"""
        temp_dirs = ["temp", "tmp", "cache", ".temp"]
        cleaned_files = 0
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    for file in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                            cleaned_files += 1
                except Exception as e:
                    self.logger.logger.warning(f"Could not clean {temp_dir}: {e}")
                    
        self.logger.logger.info(f"Cleaned {cleaned_files} temporary files")
        
    def attempt_recovery(self, error: Exception, error_type: str, context: Dict) -> bool:
        """Attempt to recover from an error"""
        if error_type in self.recovery_strategies:
            try:
                recovery_func = self.recovery_strategies[error_type]
                success = recovery_func(error, context)
                self.logger.log_recovery(error_type, recovery_func.__name__, success)
                return success
            except Exception as recovery_error:
                self.logger.logger.error(f"Recovery attempt failed: {recovery_error}")
                
        return False

def robust_execution(max_retries: int = 3, recovery_types: List[str] = None, 
                    logger: UnQTubeLogger = None):
    """
    Decorator for robust function execution with automatic error handling and recovery
    
    Args:
        max_retries: Maximum number of retry attempts
        recovery_types: List of error types to attempt recovery for
        logger: Logger instance to use
    """
    if logger is None:
        logger = UnQTubeLogger()
    
    if recovery_types is None:
        recovery_types = ["api_error", "network_error", "timeout_error"]
    
    recovery = ErrorRecovery(logger)
    
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_error = None
            context = {
                "function": func.__name__,
                "args": str(args)[:200],  # Truncate for logging
                "kwargs": str(kwargs)[:200],
                "max_retries": max_retries,
                "current_retry": 0
            }
            
            for attempt in range(max_retries + 1):
                try:
                    context["current_retry"] = attempt
                    
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                        
                    if attempt > 0:
                        logger.logger.info(f"Function {func.__name__} succeeded on retry {attempt}")
                    
                    return result
                    
                except Exception as error:
                    last_error = error
                    error_info = logger.log_error(error, f"{func.__name__} (attempt {attempt + 1})", context)
                    
                    # Don't retry on the last attempt
                    if attempt >= max_retries:
                        break
                    
                    # Determine error type and attempt recovery
                    error_type = classify_error(error)
                    if error_type in recovery_types:
                        recovery_success = recovery.attempt_recovery(error, error_type, context)
                        if not recovery_success:
                            logger.logger.warning(f"Recovery failed for {error_type}. Continuing with retry...")
                    
                    # Wait before retry (exponential backoff)
                    wait_time = min(2 ** attempt, 30)
                    logger.logger.info(f"Retrying {func.__name__} in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
            
            # All retries exhausted
            logger.logger.error(f"Function {func.__name__} failed after {max_retries + 1} attempts")
            raise last_error
            
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Convert to async and run
            async def run_async():
                return await async_wrapper(*args, **kwargs)
            
            if asyncio.iscoroutinefunction(func):
                return run_async()
            else:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(run_async())
                finally:
                    loop.close()
        
        # Return the appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator

def classify_error(error: Exception) -> str:
    """Classify error type for appropriate recovery strategy"""
    error_msg = str(error).lower()
    error_type_name = type(error).__name__.lower()
    
    # API-related errors
    if any(term in error_msg for term in ["api", "unauthorized", "forbidden", "rate limit", "quota"]):
        return "api_error"
    
    # Network-related errors
    if any(term in error_msg for term in ["network", "connection", "timeout", "dns", "resolve"]):
        return "network_error"
    
    # File-related errors
    if any(term in error_msg for term in ["file", "directory", "permission", "disk space"]):
        return "file_error"
    
    # Memory-related errors
    if any(term in error_msg for term in ["memory", "out of memory", "allocation"]):
        return "memory_error"
    
    # Timeout errors
    if "timeout" in error_msg or "timeouterror" in error_type_name:
        return "timeout_error"
    
    return "unknown_error"

def safe_file_operation(operation: Callable, file_path: str, max_attempts: int = 3) -> Any:
    """
    Safely perform file operations with automatic retry
    
    Args:
        operation: Function to execute
        file_path: Path to the file
        max_attempts: Maximum retry attempts
        
    Returns:
        Result of the operation
    """
    logger = UnQTubeLogger()
    
    for attempt in range(max_attempts):
        try:
            return operation(file_path)
        except PermissionError:
            if attempt < max_attempts - 1:
                logger.logger.warning(f"Permission error for {file_path}. Retrying...")
                time.sleep(1)
                try:
                    os.chmod(file_path, 0o666)
                except:
                    pass
            else:
                raise
        except FileNotFoundError:
            # Try to create directory if it doesn't exist
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                if attempt < max_attempts - 1:
                    continue
            except:
                pass
            raise
        except Exception as e:
            if attempt >= max_attempts - 1:
                raise
            logger.logger.warning(f"File operation failed for {file_path}: {e}. Retrying...")
            time.sleep(1)

class VideoGenerationMonitor:
    """Monitor and track video generation progress with error detection"""
    
    def __init__(self, logger: UnQTubeLogger = None):
        self.logger = logger or UnQTubeLogger()
        self.start_time = None
        self.checkpoints = {}
        self.errors = []
        
    def start_monitoring(self, video_topic: str):
        """Start monitoring video generation"""
        self.start_time = time.time()
        self.video_topic = video_topic
        self.logger.logger.info(f"Started monitoring video generation for: {video_topic}")
        
    def checkpoint(self, stage: str, details: str = ""):
        """Record a checkpoint in the video generation process"""
        timestamp = time.time()
        elapsed = timestamp - self.start_time if self.start_time else 0
        
        self.checkpoints[stage] = {
            "timestamp": timestamp,
            "elapsed": elapsed,
            "details": details
        }
        
        self.logger.logger.info(f"Checkpoint - {stage}: {details} (elapsed: {elapsed:.1f}s)")
        
    def record_error(self, stage: str, error: Exception):
        """Record an error during video generation"""
        error_record = {
            "stage": stage,
            "timestamp": time.time(),
            "error": str(error),
            "error_type": type(error).__name__
        }
        
        self.errors.append(error_record)
        self.logger.log_error(error, f"Video generation - {stage}")
        
    def generate_report(self) -> Dict:
        """Generate a comprehensive generation report"""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        report = {
            "video_topic": getattr(self, "video_topic", "Unknown"),
            "total_time": total_time,
            "success": len(self.errors) == 0,
            "checkpoints": self.checkpoints,
            "errors": self.errors,
            "performance_metrics": self._calculate_metrics()
        }
        
        return report
        
    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.checkpoints:
            return {}
            
        stages = list(self.checkpoints.keys())
        stage_times = []
        
        for i, stage in enumerate(stages):
            if i == 0:
                stage_time = self.checkpoints[stage]["elapsed"]
            else:
                stage_time = (self.checkpoints[stage]["elapsed"] - 
                            self.checkpoints[stages[i-1]]["elapsed"])
            stage_times.append(stage_time)
            
        return {
            "average_stage_time": sum(stage_times) / len(stage_times) if stage_times else 0,
            "slowest_stage": stages[stage_times.index(max(stage_times))] if stage_times else None,
            "fastest_stage": stages[stage_times.index(min(stage_times))] if stage_times else None,
            "stage_breakdown": dict(zip(stages, stage_times))
        }

# Global instances
global_logger = UnQTubeLogger()
global_monitor = VideoGenerationMonitor(global_logger)

def get_logger() -> UnQTubeLogger:
    """Get the global logger instance"""
    return global_logger

def get_monitor() -> VideoGenerationMonitor:
    """Get the global monitor instance"""
    return global_monitor