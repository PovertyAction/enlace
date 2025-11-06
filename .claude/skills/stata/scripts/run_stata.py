#!/usr/bin/env python3
"""Helper script to execute Stata code with proper error handling and output capture.

Usage:
    python run_stata.py --command "summarize var1"
    python run_stata.py --dofile "path/to/script.do"
    python run_stata.py --stata-path "C:\\Program Files\\Stata18" --edition "se"
"""

import argparse
import sys
from pathlib import Path


def setup_stata(stata_path: str, edition: str):
    """Configure Stata setup with the specified path and edition."""
    try:
        import stata_setup

        stata_setup.config(stata_path, edition)
        print(f"✓ Stata configured: {stata_path} ({edition} edition)")
        return True
    except ImportError:
        print(
            "Error: stata_setup package not found. Install with: pip install stata-setup"
        )
        return False
    except Exception as e:
        print(f"Error configuring Stata: {e}")
        return False


def run_stata_command(command: str):
    """Execute a Stata command and capture output."""
    try:
        from pystata import stata

        print(f"\nExecuting Stata command:\n{command}\n")
        print("=" * 80)

        stata.run(command, quietly=False, echo=True)

        print("=" * 80)
        print("✓ Command completed successfully")
        return True

    except ImportError:
        print("Error: pystata not available. Ensure Stata is properly configured.")
        return False
    except Exception as e:
        print(f"Error executing Stata command: {e}")
        return False


def run_stata_dofile(dofile_path: str):
    """Execute a Stata .do file and capture output."""
    dofile = Path(dofile_path)

    if not dofile.exists():
        print(f"Error: .do file not found: {dofile_path}")
        return False

    try:
        from pystata import stata

        print(f"\nExecuting Stata .do file: {dofile_path}\n")
        print("=" * 80)

        # Use absolute path to avoid issues
        abs_path = str(dofile.resolve())
        stata.run(f'do "{abs_path}"', quietly=False, echo=True)

        print("=" * 80)
        print("✓ .do file completed successfully")
        return True

    except ImportError:
        print("Error: pystata not available. Ensure Stata is properly configured.")
        return False
    except Exception as e:
        print(f"Error executing .do file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Execute Stata commands or .do files from Python"
    )

    # Stata configuration
    parser.add_argument(
        "--stata-path",
        default="C:\\Program Files\\Stata18/",
        help="Path to Stata installation (default: C:\\Program Files\\Stata18/)",
    )
    parser.add_argument(
        "--edition",
        choices=["ic", "se", "mp"],
        default="se",
        help="Stata edition: ic (Intercooled), se (Standard), mp (Multiprocessor)",
    )

    # Execution options (mutually exclusive)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--command", help="Stata command to execute")
    group.add_argument("--dofile", help="Path to .do file to execute")

    args = parser.parse_args()

    # Configure Stata
    if not setup_stata(args.stata_path, args.edition):
        sys.exit(1)

    # Execute command or .do file
    success = False
    if args.command:
        success = run_stata_command(args.command)
    elif args.dofile:
        success = run_stata_dofile(args.dofile)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
