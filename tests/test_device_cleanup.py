#!/usr/bin/env python3
"""Test that virtual devices are properly cleaned up."""

import sys
import time
import subprocess

def check_virtual_devices():
    """Check for virtual gamepad/mouse devices."""
    result = subprocess.run(
        ["ls", "-la", "/dev/input/by-id/"],
        capture_output=True,
        text=True
    )
    
    virtual_devices = []
    for line in result.stdout.split('\n'):
        if 'Virtual' in line or 'LibrePad' in line:
            virtual_devices.append(line.strip())
    
    return virtual_devices

def main():
    print("=== Device Cleanup Verification ===\n")
    
    # Check before test
    print("1. Checking for virtual devices BEFORE test...")
    devices_before = check_virtual_devices()
    if devices_before:
        print(f"   Found {len(devices_before)} virtual device(s):")
        for dev in devices_before:
            print(f"   - {dev}")
    else:
        print("   ✓ No virtual devices found (clean state)")
    
    print("\n2. Running UDP test...")
    test_result = subprocess.run(
        [sys.executable, "tests/test_udp_client.py"],
        capture_output=True,
        text=True
    )
    
    if test_result.returncode != 0:
        print(f"   ✗ Test failed with code {test_result.returncode}")
        print(f"   Error: {test_result.stderr[-500:]}")
        return 1
    
    print("   ✓ Test completed successfully")
    
    # Wait a moment for cleanup
    print("\n3. Waiting 2 seconds for cleanup...")
    time.sleep(2)
    
    # Check after test
    print("\n4. Checking for virtual devices AFTER test...")
    devices_after = check_virtual_devices()
    if devices_after:
        print(f"   ✗ Found {len(devices_after)} virtual device(s) still present:")
        for dev in devices_after:
            print(f"   - {dev}")
        print("\n   ERROR: Virtual devices not properly cleaned up!")
        print("   This will interfere with physical input devices.")
        return 1
    else:
        print("   ✓ No virtual devices found (properly cleaned up)")
    
    print("\n=== Test Summary ===")
    print("✓ Device cleanup working correctly")
    print("✓ Physical touchpad should work normally")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
