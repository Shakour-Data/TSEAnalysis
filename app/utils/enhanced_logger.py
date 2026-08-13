"""
بہتر Logging نظام - تفصیلی logging structure
"""
import logging
import logging.handlers
import os
import json
from datetime import datetime
from pathlib import Path

class EnhancedLogger:
    """Enhanced logging کے ساتھ structured logging"""
    
    # Log levels
    CRITICAL = logging.CRITICAL  # 50
    ERROR = logging.ERROR         # 40
    WARNING = logging.WARNING     # 30
    INFO = logging.INFO           # 20
    DEBUG = logging.DEBUG         # 10
    
    # Log files location
    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    
    @staticmethod
    def setup_logging(name, log_level=logging.INFO, log_file=None, max_bytes=10485760, backup_count=5):
        """
        بہتر logging setup کریں
        - Console handler (رنگین output)
        - File handler (rotation کے ساتھ)
        """
        # Logs directory بنائیں
        os.makedirs(EnhancedLogger.LOG_DIR, exist_ok=True)
        
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        logger.propagate = False  # Parent logger کو propagate نہ کریں
        
        # صرف ایک بار handlers شامل کریں
        if logger.hasHandlers():
            return logger
        
        # Formatter
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console Handler (رنگین output)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
        
        # File Handler (rotation کے ساتھ)
        if log_file is None:
            log_file = os.path.join(EnhancedLogger.LOG_DIR, f'{name}.log')
        
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,  # 10 MB
                backupCount=backup_count,  # 5 backups
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"فائل logging setup ناکام: {e}")
        
        return logger
    
    @staticmethod
    def log_event(logger, event_type, level=logging.INFO, **kwargs):
        """
        Structured event logging
        event_type: 'api_call', 'database', 'error', etc.
        """
        event_data = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        message = json.dumps(event_data, ensure_ascii=False)
        if logger:
            logger.log(level, message)
    
    @staticmethod
    def log_api_call(logger, endpoint, method, status_code, duration_ms, **extra):
        """API call logging"""
        EnhancedLogger.log_event(
            logger,
            'api_call',
            level=logging.INFO,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            **extra
        )
    
    @staticmethod
    def log_database_operation(logger, operation, table, duration_ms, affected_rows=None, **extra):
        """Database operation logging"""
        EnhancedLogger.log_event(
            logger,
            'database',
            level=logging.DEBUG,
            operation=operation,
            table=table,
            duration_ms=duration_ms,
            affected_rows=affected_rows,
            **extra
        )
    
    @staticmethod
    def log_performance(logger, component, duration_ms, threshold_ms=1000):
        """Performance logging"""
        level = logging.WARNING if duration_ms > threshold_ms else logging.DEBUG
        
        EnhancedLogger.log_event(
            logger,
            'performance',
            level=level,
            component=component,
            duration_ms=duration_ms,
            slow=(duration_ms > threshold_ms)
        )
    
    @staticmethod
    def log_error_with_context(logger, exception, context=None, **extra):
        """Error logging with context"""
        logger.error(
            f"Exception: {type(exception).__name__}: {str(exception)}",
            exc_info=True,
            extra={
                'context': context or {},
                **extra
            }
        )
    
    @staticmethod
    def get_logger(name, level=logging.INFO):
        """آسانی سے logger حاصل کریں"""
        logger = logging.getLogger(name)
        
        if not logger.hasHandlers():
            EnhancedLogger.setup_logging(name, log_level=level)
        
        return logger
    
    @staticmethod
    def get_log_files():
        """تمام log files کو درج کریں"""
        log_files = []
        
        if os.path.exists(EnhancedLogger.LOG_DIR):
            for file in os.listdir(EnhancedLogger.LOG_DIR):
                if file.endswith('.log'):
                    full_path = os.path.join(EnhancedLogger.LOG_DIR, file)
                    size = os.path.getsize(full_path) / 1024  # KB میں
                    modified = datetime.fromtimestamp(os.path.getmtime(full_path))
                    
                    log_files.append({
                        'name': file,
                        'path': full_path,
                        'size_kb': size,
                        'modified': modified.isoformat()
                    })
        
        return sorted(log_files, key=lambda x: x['modified'], reverse=True)
    
    @classmethod
    def get_log_summary(cls):
        """
        Summarizes log files, counting errors, warnings, etc.
        """
        log_files = cls.get_log_files()
        summary = {
            'total_files': 0,
            'total_size_mb': 0.0,
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0,
            'debug_count': 0,
            'files': [],
            'log_directory': cls.LOG_DIR
        }
        
        for log_file in log_files:
            summary['total_files'] += 1
            summary['total_size_mb'] += log_file['size_kb'] / 1024  # Convert KB to MB
            
            # Read the log file and count occurrences of each log level
            try:
                with open(log_file['path'], 'r', encoding='utf-8') as f:
                    for line in f:
                        if '"levelname":"ERROR"' in line:
                            summary['error_count'] += 1
                        elif '"levelname":"WARNING"' in line:
                            summary['warning_count'] += 1
                        elif '"levelname":"INFO"' in line:
                            summary['info_count'] += 1
                        elif '"levelname":"DEBUG"' in line:
                            summary['debug_count'] += 1
            except Exception as e:
                print(f"Log file reading failed: {log_file['path']} - {e}")
        
        return summary

    @classmethod
    def clear_old_logs(cls, days_to_keep: int = 7):
        """
        Deletes log files older than a specified number of days.
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        cleared = 0
        
        if os.path.exists(EnhancedLogger.LOG_DIR):
            for file in os.listdir(EnhancedLogger.LOG_DIR):
                if file.endswith('.log'):
                    full_path = os.path.join(EnhancedLogger.LOG_DIR, file)
                    modified = datetime.fromtimestamp(os.path.getmtime(full_path))
                    
                    if modified < cutoff_time:
                        try:
                            os.remove(full_path)
                            cleared += 1
                        except Exception as e:
                            print(f"Log file deletion failed: {file} - {e}")
        
        return cleared
    
# Quick shortcuts
def get_app_logger():
    """Application کے لیے logger"""
    return EnhancedLogger.get_logger('TSEAnalysis.app', level=logging.INFO)

def get_api_logger():
    """API کے لیے logger"""
    return EnhancedLogger.get_logger('TSEAnalysis.api', level=logging.INFO)

def get_db_logger():
    """Database کے لیے logger"""
    return EnhancedLogger.get_logger('TSEAnalysis.database', level=logging.DEBUG)

def get_service_logger(service_name):
    """کسی service کے لیے logger"""
    return EnhancedLogger.get_logger(f'TSEAnalysis.{service_name}', level=logging.INFO)

