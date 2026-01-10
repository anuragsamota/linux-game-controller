# Touchpad & Multi-Device Connection Fixes

## Date: 2026-01-10

## Issues Fixed

### 1. Server Multi-Device Connection Support
**Problem:** Server only allowed one device connection per WebSocket, causing `ValueError: Already connected to 'standard'; disconnect first` when trying to connect mouse for touchpad.

**Solution:**
- Changed `client_device` from single string to `connected_devices: set[str]`
- Modified connect handler to add devices to set instead of checking for single connection
- Updated disconnect handler to remove specific device from set
- Modified cleanup to release all connected devices on disconnect
- Button/axis events auto-acquire devices if not already connected

### 2. Improved Touchpad with New Features

**Features Added:**
1. **Adjustable Sensitivity** (0.5x to 3.0x)
   - Configurable speed multiplier for mouse movement
   - UI slider in edit mode
   - Default: 1.0x

2. **Tap-to-Click**
   - Quick tap (< 200ms) without movement triggers left mouse click
   - Configurable via checkbox in edit mode
   - Movement threshold: 3 pixels

3. **Simplified Visual Feedback**
   - Shows simple white dot indicator only when pressed
   - Removed complex delta-based position tracking
   - Cleaner, more intuitive visual

4. **Delta Movement Tracking**
   - Tracks last pointer position for accurate delta calculation
   - Applies sensitivity scaling before normalization
   - Prevents tap detection on significant movement

## Files Modified

### Backend
- `src/controller_server/server.py`: Multi-device connection support

### Frontend
- `web/src/components/Touchpad.jsx`: Sensitivity, tap-to-click, simplified UI
- `web/src/components/Controller.jsx`: Pass onTouchpadTap prop
- `web/src/App.jsx`: Handle tap-to-click with mouse button event
- `web/src/utils/WebSocketManager.js`: Added sendMouseButton() method

## Technical Details

### Server Changes
```python
# Before: Single device tracking
client_device: Optional[str] = None

# After: Multiple device set
connected_devices: set[str] = set()
```

### Touchpad Features
```javascript
// Sensitivity scaling (default 1.0)
const sensitivity = touchpad.sensitivity ?? 1.0;
const scaledDelta = delta * sensitivity;

// Tap detection (< 200ms, movement < 3px)
const isTap = tapDuration < 200 && !moved;
if (isTap && touchpad.tapToClick) {
  onTap?.(touchpad.id); // Sends left mouse click
}
```

## Testing

✅ Build successful: `pnpm run build`
✅ All 6 unit tests passing
✅ Server allows multiple device connections
✅ Touchpad supports:
  - Sensitivity adjustment (0.5x - 3.0x)
  - Tap-to-click toggle
  - Smooth delta movement tracking

## Configuration

### Touchpad Settings (Edit Mode)
- **Scale**: 0.5x - 2.0x (visual size)
- **Speed**: 0.5x - 3.0x (movement sensitivity)
- **Tap**: Checkbox to enable/disable tap-to-click

### Mouse Events Sent
- Movement: `{ event: 'axis', device: 'mouse', name: 'dx/dy', value: delta }`
- Tap Click: `{ event: 'button', device: 'mouse', name: 'left', pressed: true/false }`

## Usage

1. **Connect to Server**: Both 'standard' and 'mouse' devices connect automatically
2. **Adjust Sensitivity**: Enter edit mode and use Speed slider
3. **Enable Tap-to-Click**: Check the "Tap" checkbox in edit mode
4. **Use Touchpad**: 
   - Drag finger to move mouse (relative movement)
   - Quick tap to left-click (if enabled)
