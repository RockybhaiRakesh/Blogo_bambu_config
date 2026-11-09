"""
PRINTMATE AI – Production Logging Engine.
Writes human-readable, structured .txt logs for every system action,
enabling persistent inspection, clicking, and file downloads.
"""

import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from printmate.core.config import Config

# Ensure logs directory exists in workspace
LOGS_DIR = os.path.join(Config.WORKSPACE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Master system log path
MASTER_LOG_FILE = os.path.join(LOGS_DIR, "system_master.txt")


class ActionLogger:
    """Manages creation and retrieval of human-readable .txt log files."""

    @staticmethod
    def get_logs_dir() -> str:
        os.makedirs(LOGS_DIR, exist_ok=True)
        return LOGS_DIR

    @staticmethod
    def log_action(
        action: str,
        title: str,
        model_name: Optional[str] = None,
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
        steps: Optional[List[str]] = None,
        error: Optional[str] = None
    ) -> str:
        """
        Creates an action-specific .txt log file and appends to the master log.
        Returns the filename of the generated .txt log.
        """
        os.makedirs(LOGS_DIR, exist_ok=True)
        timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_action = "".join(c if c.isalnum() or c in "-_" else "_" for c in action).lower()
        clean_model = "".join(c if c.isalnum() or c in "-_" else "_" for c in (model_name or "general")).lower()
        
        filename = f"{clean_action}_{clean_model}_{timestamp_slug}.txt"
        file_path = os.path.join(LOGS_DIR, filename)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            "=" * 80,
            f"PRINTMATE AI – EXECUTION LOG: {title.upper()}",
            "=" * 80,
            f"File Name:     {filename}",
            f"Action:        {action}",
            f"Model / Asset: {model_name or 'N/A'}",
            f"Timestamp:     {now_str}",
            f"Status:        {status}",
            f"Target Hardware: {Config.hardware.printer_name} (0.4mm nozzle, {Config.hardware.build_volume_x}x{Config.hardware.build_volume_y}x{Config.hardware.build_volume_z}mm)",
            "=" * 80,
            "",
            "--- EXECUTION SUMMARY ---",
            f"Result: {status}",
        ]

        if error:
            lines.extend([
                "",
                "--- ERROR DETAILS ---",
                f"Error Message: {error}",
            ])

        if steps:
            lines.extend([
                "",
                "--- STEP-BY-STEP PROGRESS ---",
            ])
            for i, step in enumerate(steps, 1):
                lines.append(f"  [{i:02d}] {step}")

        if details:
            lines.extend([
                "",
                "--- TECHNICAL METRICS & PARAMETERS ---",
            ])
            for key, val in details.items():
                if isinstance(val, (dict, list)):
                    import json
                    val_str = json.dumps(val, indent=2)
                    lines.append(f"  {key}:")
                    for subline in val_str.splitlines():
                        lines.append(f"    {subline}")
                else:
                    lines.append(f"  {key:30s} : {val}")

        lines.extend([
            "",
            "=" * 80,
            f"PRINTMATE AI (c) 2026 – END OF LOG [{filename}]",
            "=" * 80,
            ""
        ])

        content = "\n".join(lines)

        # Write action-specific .txt file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Append summary to master log file
        master_entry = (
            f"[{now_str}] [{status:7s}] [{action:20s}] Model: {model_name or 'N/A':20s} "
            f"-> Log: {filename}\n"
        )
        try:
            with open(MASTER_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(master_entry)
        except Exception:
            pass

        return filename

    @staticmethod
    def list_logs() -> List[Dict[str, Any]]:
        """Lists all available .txt log files ordered from newest to oldest."""
        os.makedirs(LOGS_DIR, exist_ok=True)
        log_files = []

        # Include master log if exists
        all_files = [f for f in os.listdir(LOGS_DIR) if f.endswith(".txt")]
        for f in all_files:
            fp = os.path.join(LOGS_DIR, f)
            stat = os.stat(fp)
            
            # Deduce action type from filename
            parts = f.replace(".txt", "").split("_")
            action = parts[0] if parts else "system"
            
            log_files.append({
                "filename": f,
                "file_path": fp,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_epoch": stat.st_mtime,
                "action": action
            })

        log_files.sort(key=lambda x: x["timestamp_epoch"], reverse=True)
        return log_files

    @staticmethod
    def read_log(filename: str) -> Optional[str]:
        """Reads the full plain text content of a log file."""
        safe_name = os.path.basename(filename)
        fp = os.path.join(LOGS_DIR, safe_name)
        if not os.path.exists(fp):
            return None
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
