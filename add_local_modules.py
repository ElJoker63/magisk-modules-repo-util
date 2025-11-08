#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to automatically add local zip modules to the repository tracking system.
Scans the local/ folder for .zip files, extracts module information from module.prop,
and adds them as tracks using the CLI.
"""

import os
import sys
import subprocess
from pathlib import Path
from zipfile import ZipFile

def extract_module_id(zip_path):
    """
    Extract the module ID from module.prop inside the zip file.
    Args:
        zip_path (Path): Path to the zip file
    Returns:
        str: Module ID if found, None otherwise
    """
    try:
        with ZipFile(zip_path, 'r') as zip_file:
            # Check if it's a valid Magisk module
            if ("META-INF/com/google/android/updater-script" not in zip_file.namelist() or
                "META-INF/com/google/android/update-binary" not in zip_file.namelist()):
                print(f"Warning: {zip_path.name} is not a valid Magisk module (missing updater-script or update-binary)")
                return None

            # Read module.prop
            if "module.prop" not in zip_file.namelist():
                print(f"Warning: {zip_path.name} does not contain module.prop")
                return None

            module_prop = zip_file.read("module.prop").decode("utf-8")

            # Parse module.prop for id
            for line in module_prop.splitlines():
                line = line.strip()
                if line.startswith("id="):
                    module_id = line.split("=", 1)[1].strip()
                    if module_id:
                        return module_id

            print(f"Warning: Could not find 'id=' in module.prop of {zip_path.name}")
            return None

    except Exception as e:
        print(f"Error reading {zip_path.name}: {e}")
        return None

def add_track(module_id, zip_filename):
    """
    Add a track for the module using the CLI.

    Args:
        module_id (str): The module ID
        zip_filename (str): The zip filename in local/ folder
    """
    cmd = [
        sys.executable, "cli.py", "track", "--add",
        f"id={module_id}",
        f"update_to={zip_filename}",
        "changelog="
    ]

    print(f"Executing: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)

        if result.returncode == 0:
            print(f"Successfully added track for {module_id}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
        else:
            print(f"Failed to add track for {module_id}")
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")

    except Exception as e:
        print(f"Error executing command for {module_id}: {e}")

def main():
    """Main function to scan local folder and add modules."""
    local_dir = Path("local")

    if not local_dir.exists():
        print("Error: local/ directory does not exist")
        return 1

    # Find all .zip files in local/
    zip_files = list(local_dir.glob("*.zip"))

    if not zip_files:
        print("No .zip files found in local/ directory")
        return 0

    print(f"Found {len(zip_files)} zip files in local/ directory")

    added_count = 0

    for zip_file in zip_files:
        print(f"\nProcessing {zip_file.name}...")

        module_id = extract_module_id(zip_file)

        if module_id:
            print(f"Found module ID: {module_id}")
            add_track(module_id, zip_file.name)
            added_count += 1
        else:
            print(f"Skipping {zip_file.name} - could not extract module ID")

    print(f"\nProcessed {len(zip_files)} files, added {added_count} tracks")

    if added_count > 0:
        print("\nTo sync the modules, run: python cli.py sync")
        print("To generate the index, run: python cli.py index")

    return 0

if __name__ == "__main__":
    sys.exit(main())