# Web Client Development Guide

## Overview

The web client has been completely redesigned using modern technologies:
- **Vite** - Fast build tool and dev server
- **React** - Component-based UI framework
- **Tailwind CSS** - Utility-first CSS framework
- **JavaScript & JSX** - Modern ES6+ syntax

## Features

### 1. **Multiple Controller Configurations**
- Create unlimited custom controller layouts
- Save/load configurations in browser storage
- Import/export configurations as JSON
- Duplicate existing configurations
- Default templates (Standard Gamepad, Minimal)

### 2. **Edit Mode**
- Drag and drop buttons to reposition
- Resize buttons with drag handles
- Add new buttons (Action, D-Pad, Shoulder, Trigger, Special, Joystick)
- Delete unwanted buttons
- Real-time visual feedback
- Adjustable scale (0.5x - 1.5x)

### 3. **Responsive Design**
- Optimized for mobile landscape mode
- Touch-friendly controls
- Prevents pull-to-refresh and overscroll
- Fullscreen support
- Works on desktop and mobile devices

### 4. **WebSocket Integration**
- Real-time button and axis events
- Automatic reconnection
- Connection status indicator
- Low-latency input transmission

## Project Structure

```
web/
├── index.html                  # Entry HTML with mobile optimizations
├── package.json                # Dependencies and scripts
├── vite.config.js             # Vite configuration
├── tailwind.config.js         # Tailwind CSS configuration
├── postcss.config.js          # PostCSS configuration
└── src/
    ├── main.jsx               # React entry point
    ├── index.css              # Global styles with Tailwind
    ├── App.jsx                # Main application component
    ├── components/
    │   ├── Button.jsx         # Individual button/joystick component
    │   ├── Controller.jsx     # Controller display with buttons
    │   ├── ConnectionScreen.jsx # Initial connection screen
    │   ├── Toolbar.jsx        # Top toolbar with controls
    │   └── ConfigMenu.jsx     # Configuration management modal
    └── utils/
        ├── WebSocketManager.js    # WebSocket connection handler
        ├── storage.js             # LocalStorage management
        └── defaultConfigs.js      # Default controller templates
```

## Development

### Setup
```bash
cd web
npm install
```

### Development Server
```bash
npm run dev
# or from project root:
./start.sh
```

The dev server will start on port 8000 (configurable via WEB_PORT env var).

### Production Build
```bash
npm run build
# or from project root:
./build.sh
```

Outputs to `web/dist/` directory.

## Component Architecture

### App.jsx
- Main application state management
- WebSocket connection lifecycle
- Configuration management
- Button event handling

### Button.jsx
- Individual button rendering
- Touch/pointer event handling
- Drag and resize in edit mode
- Joystick analog input
- Visual feedback (press states, selection)

### Controller.jsx
- Button layout container
- Passes events to Button components
- Handles controller-level interactions

### ConnectionScreen.jsx
- Initial connection UI
- Server configuration form
- Connection status feedback

### Toolbar.jsx
- Edit mode toggle
- Add button menu
- Save configuration
- Scale adjustment
- Config menu access
- Disconnect button

### ConfigMenu.jsx
- List all saved configurations
- Create new configurations
- Rename, duplicate, delete
- Import/export JSON
- Load default templates

## WebSocket Protocol

The client communicates with the Python backend using WebSocket messages:

### Button Press/Release
```javascript
{
  event: 'button',
  device: 'standard',
  name: 'a',           // Button ID
  pressed: true/false
}
```

### Joystick Axis
```javascript
{
  event: 'axis',
  device: 'standard',
  name: 'lx',          // 'lx', 'ly', 'rx', 'ry'
  value: 0.5           // Range: -1.0 to 1.0
}
```

### Connection
```javascript
{
  event: 'connect',
  device: 'standard',
  name: 'Virtual Gamepad'
}
```

### Disconnection
```javascript
{
  event: 'disconnect'
}
```

## Configuration Format

Configurations are stored in localStorage and can be exported as JSON:

```json
{
  "id": "config-1234567890",
  "name": "My Custom Controller",
  "buttons": [
    {
      "id": "btn-a",
      "label": "A",
      "type": "action",
      "x": 75,          // Position X (percentage)
      "y": 60,          // Position Y (percentage)
      "width": 8,       // Width (percentage)
      "height": 8,      // Height (percentage)
      "color": "#22c55e",
      "isJoystick": false
    },
    {
      "id": "ls",
      "label": "LS",
      "type": "joystick",
      "x": 25,
      "y": 70,
      "width": 15,
      "height": 15,
      "color": "#8b5cf6",
      "isJoystick": true,
      "axis": "left"    // 'left' or 'right'
    }
  ]
}
```

## Button Types

- **action** - Standard action buttons (A, B, X, Y)
- **dpad** - Directional pad buttons (Up, Down, Left, Right)
- **shoulder** - Shoulder buttons (LB, RB)
- **trigger** - Trigger buttons (LT, RT)
- **special** - Special buttons (Start, Select, Home)
- **joystick** - Analog joysticks (Left Stick, Right Stick)

## Mobile Optimization

The web client is optimized for mobile landscape mode:

1. **Viewport Settings**
   - Prevents zoom and scaling
   - Fullscreen viewport coverage
   - Status bar styling for iOS

2. **Touch Handling**
   - Multi-touch support for simultaneous button presses
   - Prevent default touch behaviors
   - No text selection or context menus

3. **Performance**
   - Minimal re-renders with React optimization
   - CSS transitions for smooth interactions
   - Efficient WebSocket communication

4. **Layout**
   - Responsive grid system
   - Percentage-based positioning
   - Scale adjustment for different screen sizes

## Customization Tips

### Adding Custom Button Colors
Edit `tailwind.config.js`:
```javascript
theme: {
  extend: {
    colors: {
      gamepad: {
        primary: '#3b82f6',    // Customize these
        secondary: '#6366f1',
        accent: '#8b5cf6',
        // ... add more
      }
    }
  }
}
```

### Changing Default Configurations
Edit `src/utils/defaultConfigs.js` to add or modify default templates.

### Custom Button Shapes
Modify button rendering in `src/components/Button.jsx`:
- Change `rounded-lg` class for different border radius
- Add custom SVG icons
- Implement gradient backgrounds

## Troubleshooting

### WebSocket Connection Issues
- Ensure Python backend is running
- Check firewall settings
- Verify host and port configuration
- Check browser console for errors

### Touch Events Not Working
- Disable browser zoom
- Check touch-action CSS property
- Ensure pointer events are not disabled

### Performance Issues
- Reduce number of buttons
- Decrease scale factor
- Disable browser extensions
- Clear browser cache

### Configuration Not Saving
- Check localStorage quota
- Ensure browser allows localStorage
- Check browser privacy settings

## Future Enhancements

Potential improvements:
- Haptic feedback support
- Custom button images/icons
- Button grouping and layers
- Gesture controls (swipe, pinch)
- Keyboard shortcut support
- Gamepad API integration
- Multi-device support
- Cloud configuration sync
- Theme customization
- Button animation effects
