"""
PDDL Plan Validator using VAL (Validation and Analysis of PDDL)

Simple wrapper for VAL validator - the standard tool for PDDL plan validation.
VAL Repository: https://github.com/KCL-Planning/VAL
"""

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

# Import configuration
try:
    from .configuration import load_config
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.utils.configuration import load_config


def get_val_executable() -> str:
    """
    Get the VAL executable path from configuration.

    Platform-aware: if the configured VAL_EXECUTABLE has a .exe suffix
    (Windows convention) but we're on a non-Windows host, the .exe is
    stripped automatically — and vice versa. This prevents a single
    config.yml synced between a Windows dev machine and a Linux cluster
    from breaking either side.

    Returns:
        str: Full path to the VAL executable
    """
    import platform

    is_windows = platform.system() == "Windows"

    try:
        config = load_config()
        val_path = config.get("VAL_PATH", "VAL/build/linux64/Release/bin")
        val_executable = config.get("VAL_EXECUTABLE", "Validate")

        # Normalize the executable name to the host's convention. Caller's
        # config.yml may carry either spelling — match what's actually on disk.
        if is_windows and not val_executable.lower().endswith(".exe"):
            candidates = [val_executable + ".exe", val_executable]
        elif not is_windows and val_executable.lower().endswith(".exe"):
            candidates = [val_executable[:-4], val_executable]
        else:
            candidates = [val_executable]

        # Create absolute path from project root
        project_root = Path(__file__).parent.parent.parent

        for cand in candidates:
            full_val_path = project_root / val_path / cand
            if full_val_path.exists():
                return str(full_val_path)

        # Fallback to system PATH (last resort)
        return candidates[0]

    except Exception:
        # Fallback to platform-appropriate default
        return "Validate.exe" if is_windows else "Validate"


def validate_plan(domain_path: str, problem_path: str, plan_path: str, val_executable: Optional[str] = None) -> Dict:
    """
    Validate a PDDL plan using VAL.
    
    Args:
        domain_path (str): Path to the PDDL domain file
        problem_path (str): Path to the PDDL problem file
        plan_path (str): Path to the plan file to validate
        val_executable (Optional[str]): VAL executable path (auto-detected if None)
        
    Returns:
        Dict: {"valid": bool, "error": str or None}
    """
    try:
        # Get VAL executable path
        if val_executable is None:
            val_executable = get_val_executable()
        
        # Get timeout from config
        try:
            config = load_config()
            timeout = config.get("VAL_TIMEOUT", 300)
        except:
            timeout = 300
        
        # Run VAL: Validate domain.pddl problem.pddl plan.txt
        cmd = [val_executable, domain_path, problem_path, plan_path]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Log for debugging
        import logging
        logger = logging.getLogger(__name__)
        # Comment for readability 
        # logger.debug(f"VAL command: {' '.join(cmd)}")
        logger.debug(f"VAL return code: {result.returncode}")
        # Comment for readability 
        # logger.debug(f"VAL stdout: {result.stdout}")
        # logger.debug(f"VAL stderr: {result.stderr}")
        
        # VAL returns 0 for valid plans, non-zero for invalid
        is_valid = result.returncode == 0
        
        error_msg = result.stderr.strip() if result.stderr else None
        if not is_valid and not error_msg:
            error_msg = result.stdout.strip() if result.stdout else "Unknown validation error"
        
        return {
            "valid": is_valid,
            "error": error_msg
        }
        
    except FileNotFoundError:
        return {
            "valid": False,
            "error": f"VAL executable '{val_executable}' not found. Please install VAL."
        }
    except subprocess.TimeoutExpired:
        return {
            "valid": False,
            "error": "VAL validation timeout"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"VAL execution error: {str(e)}"
        }


def validate_plan_verbose(
    domain_path: str,
    problem_path: str,
    plan_text: str,
    val_executable: Optional[str] = None,
    timeout: Optional[int] = None,
) -> Tuple[bool, str]:
    """Run VAL with -v on plan_text, return (is_valid, raw_stdout).

    Canonical entry point for every VAL call in the pipeline: metrics
    extraction, iteration-loop validity checks, and feedback prompt
    construction all go through this function.

    Non-PDDL lines (e.g. a trailing "Generated in N iterations." header
    left over from Project A plan files) are stripped before VAL sees
    the plan so trailing prose cannot poison the parse.
    """
    import logging
    log = logging.getLogger(__name__)

    if val_executable is None:
        val_executable = get_val_executable()
    if timeout is None:
        try:
            timeout = load_config().get("VAL_TIMEOUT", 300)
        except Exception:
            timeout = 300

    kept = [
        line for line in plan_text.splitlines()
        if not line.strip() or line.lstrip().startswith(("(", ";"))
    ]
    cleaned = "\n".join(kept)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".plan", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(cleaned)
        tmp_path = tmp.name

    try:
        try:
            result = subprocess.run(
                [val_executable, "-v", domain_path, problem_path, tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError:
            log.error("VAL executable '%s' not found", val_executable)
            return False, ""
        except subprocess.TimeoutExpired:
            log.error("VAL -v validation timeout (%ss)", timeout)
            return False, ""
        return result.returncode == 0, result.stdout
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def validate_plan_from_text(domain_path: str, problem_path: str, plan_text: str, val_executable: Optional[str] = None) -> Dict:
    """
    Validate a plan from text content by creating a temporary plan file.
    
    Args:
        domain_path (str): Path to domain file
        problem_path (str): Path to problem file
        plan_text (str): Plan content as text
        val_executable (Optional[str]): VAL executable path (auto-detected if None)
        
    Returns:
        Dict: {"valid": bool, "error": str or None}
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Create temporary plan file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.plan', delete=False, encoding='utf-8') as temp_plan:
            temp_plan.write(plan_text)
            temp_plan_path = temp_plan.name
        
        logger.debug(f"Created temp plan file: {temp_plan_path}")
        logger.debug(f"Plan content:\n{plan_text}")
        
        # Validate using VAL
        result = validate_plan(domain_path, problem_path, temp_plan_path, val_executable)
        
        # Clean up
        try:
            os.unlink(temp_plan_path)
        except OSError:
            pass
            
        return result
        
    except Exception as e:
        logger.exception("Error in validate_plan_from_text")
        return {
            "valid": False,
            "error": f"Error creating temporary plan file: {str(e)}"
        }