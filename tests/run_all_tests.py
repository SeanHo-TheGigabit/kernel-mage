#!/usr/bin/env python3
"""Run all tests for KernelMage."""
import sys
import subprocess


def run_test_file(filename):
    """Run a test file."""
    print(f"\n{'='*60}")
    print(f"Running {filename}")
    print('='*60)

    result = subprocess.run(
        [sys.executable, filename],
        capture_output=False,
        cwd='/home/user/kernel-mage/tests'
    )

    return result.returncode == 0


def main():
    """Run all tests."""
    print("╔════════════════════════════════════════════╗")
    print("║   KernelMage - Test Suite                 ║")
    print("╚════════════════════════════════════════════╝")

    test_files = [
        'test_entities.py',
        'test_magic.py',
        'test_network.py',
        'test_combat.py',
    ]

    results = {}

    for test_file in test_files:
        success = run_test_file(test_file)
        results[test_file] = success

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    all_passed = True
    for test_file, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_file}")
        if not success:
            all_passed = False

    print("="*60)

    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
