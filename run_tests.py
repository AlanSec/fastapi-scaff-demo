"""Test runner — runs both legacy (app/test/) and new (tests/) test suites."""

import subprocess
import sys
import os


def run_all_tests():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)

    cmd = [
        sys.executable, "-m", "pytest",
        "app/test/", "tests/",
        "-v",
        "--tb=short",
    ]

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def run_specific_test(test_path):
    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-v",
        "--tb=short",
    ]

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) > 1:
        exit_code = run_specific_test(sys.argv[1])
    else:
        exit_code = run_all_tests()

    sys.exit(exit_code)
