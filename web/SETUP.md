# React Virtual Gamepad - Quick Setup

## Modern Stack
- **Vite** - Lightning-fast build tool
- **React 19** - Latest React with hooks
- **Tailwind CSS v4** - Modern utility-first CSS with @import
- **pnpm** - Fast, disk-efficient package manager

## Setup Complete ✓

### What's Been Created:
1. ✅ Vite + React project with pnpm
2. ✅ Tailwind CSS v4 with @tailwindcss/vite plugin
3. ✅ Custom CSS variables (@theme) for gamepad colors
4. ✅ Mobile-optimized index.html
5. ✅ WebSocketManager utility
6. ✅ Storage & defaultConfigs utilities
7. ✅ ConnectionScreen component

### What's Needed:
Create the following component files in `web/src/components/`:

**Button.jsx** - Individual button/joystick (drag, resize, press)
**Controller.jsx** - Layout container for buttons
**Toolbar.jsx** - Top controls (edit mode, scale, save)
**ConfigMenu.jsx** - Configuration management modal

## Quick Start

```bash
cd web
pnpm install     # Already done
pnpm run dev     # Start dev server on :8000
```

## Build for Production

```bash
cd web
pnpm run build   # Outputs to dist/
```

## Key Features
- ✅ No PostCSS config needed
- ✅ No autoprefixer needed  
- ✅ Clean Tailwind v4 setup with @import
- ✅ Custom theme colors via CSS variables
- ✅ Mobile landscape optimized
- ✅ Touch-friendly, no zoom/pull-to-refresh
- ✅ WebSocket integration ready

## File Structure

```
web/
├── src/
│   ├── App.jsx              ✓ Main app logic
│   ├── index.css            ✓ Tailwind @import + @theme
│   ├── main.jsx             ✓ React entry
│   ├── components/
│   │   ├── ConnectionScreen.jsx  ✓ Created
│   │   ├── Button.jsx       ⚠️  Need to create
│   │   ├── Controller.jsx   ⚠️  Need to create
│   │   ├── Toolbar.jsx      ⚠️  Need to create
│   │   └── ConfigMenu.jsx   ⚠️  Need to create
│   └── utils/
│       ├── WebSocketManager.js   ✓ Created
│       ├── storage.js            ✓ Created
│       └── defaultConfigs.js     ✓ Created
├── index.html           ✓ Mobile-optimized
├── vite.config.js       ✓ Tailwind plugin configured
└── package.json         ✓ pnpm setup

```

## Tailwind v4 Modernization

### Old Way (v3):
```js
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,jsx}'],
  theme: { extend: { colors: {...} } }
}

// postcss.config.js  
module.exports = {
  plugins: { tailwindcss: {}, autoprefixer: {} }
}

// CSS
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### New Way (v4 - What We Use):
```js
// vite.config.js
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({
  plugins: [react(), tailwindcss()]
})

// No tailwind.config.js needed!
// No postcss.config.js needed!

// index.css
@import "tailwindcss";

@theme {
  --color-gamepad-primary: #3b82f6;
  --color-gamepad-secondary: #6366f1;
  /* etc */
}
```

## Usage in Components

```jsx
// Use CSS variables
<div className="bg-gamepad-background">

// Or use standard Tailwind
<div className="bg-blue-500 rounded-lg p-4">
```

## Next Steps

1. Copy component implementations from the docs
2. Test with `pnpm run dev`
3. Connect to Python WebSocket server
4. Build for production with `pnpm run build`

See WebClientDevelopment.md for full component code and architecture details.
