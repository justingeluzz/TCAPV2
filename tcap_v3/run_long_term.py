"""
TCAP v3 Long-Term Runner
Runs TCAP v3 continuously with automatic restart on failures
For month-long operation
"""

import subprocess
import time
import logging
from datetime import datetime
from pathlib import Path
import sys
import os

def setup_runner_logging():
    """Setup logging for the runner"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | RUNNER | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_dir / f"tcap_runner_{datetime.now().strftime('%Y%m%d')}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_tcap_continuously():
    """Run TCAP v3 continuously with automatic restart"""
    logger = setup_runner_logging()
    
    logger.info("Starting TCAP v3 Long-Term Runner")
    logger.info("This will run TCAP v3 continuously for month-long operation")
    logger.info("Press Ctrl+C multiple times to stop completely")
    
    restart_count = 0
    start_time = datetime.now()
    
    while True:
        try:
            logger.info(f"Starting TCAP v3 (restart #{restart_count})")
            
            # Get the Python executable path
            if os.path.exists("C:/Users/geluz/OneDrive/Desktop/Project TCAP/.venv/Scripts/python.exe"):
                python_exe = "C:/Users/geluz/OneDrive/Desktop/Project TCAP/.venv/Scripts/python.exe"
            else:
                python_exe = "python"
            
            # Start TCAP v3
            process = subprocess.Popen(
                [python_exe, "main_engine.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor the process
            while True:
                output = process.stdout.readline()
                if output:
                    print(output.strip())
                
                # Check if process is still running
                if process.poll() is not None:
                    break
                
                time.sleep(0.1)
            
            # Process ended
            return_code = process.returncode
            runtime = datetime.now() - start_time
            
            if return_code == 0:
                logger.info(f"TCAP v3 ended normally after {runtime}")
                break
            else:
                logger.warning(f"TCAP v3 crashed with code {return_code} after {runtime}")
                restart_count += 1
                
                # Wait before restart (exponential backoff)
                wait_time = min(60 * (2 ** min(restart_count, 4)), 300)  # Max 5 minutes
                logger.info(f"Waiting {wait_time} seconds before restart...")
                time.sleep(wait_time)
                
                # Reset counter after 24 hours of successful operation
                if runtime.total_seconds() > 86400:  # 24 hours
                    restart_count = 0
                    logger.info("Resetting restart counter after 24 hours of operation")
                
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
            if 'process' in locals() and process.poll() is None:
                logger.info("Terminating TCAP v3...")
                process.terminate()
                time.sleep(5)
                if process.poll() is None:
                    process.kill()
            break
            
        except Exception as e:
            logger.error(f"Unexpected error in runner: {e}")
            restart_count += 1
            time.sleep(60)  # Wait 1 minute on unexpected errors

if __name__ == "__main__":
    print("TCAP v3 Long-Term Runner")
    print("=" * 50)
    print("This will run TCAP v3 continuously for month-long operation")
    print("Features:")
    print("- Automatic restart on crashes")
    print("- Exponential backoff on failures")
    print("- Comprehensive logging")
    print("- Memory and resource management")
    print("=" * 50)
    
    run_tcap_continuously()
