/**
 * Touchpad Mouse Controller
 * Provides touchpad interface for mouse control
 */

class TouchpadController {
    constructor(app) {
        this.app = app;
        this.canvas = document.getElementById('touchpadCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.enableBtn = document.getElementById('enableTouchpadBtn');
        this.sensitivityCheckbox = document.getElementById('touchpadSensitivity');
        this.mouseDeltaDisplay = document.getElementById('mouseDelta');
        
        this.mouseButtons = {
            left: document.getElementById('mouseLeftBtn'),
            right: document.getElementById('mouseRightBtn'),
            middle: document.getElementById('mouseMiddleBtn')
        };
        
        this.enabled = false;
        this.isTracking = false;
        this.lastX = 0;
        this.lastY = 0;
        this.sensitivity = 2.0;
        this.touchpadDevice = null;
        
        this.setupEventListeners();
        this.drawTouchpad();
    }
    
    setupEventListeners() {
        // Enable/disable touchpad
        this.enableBtn.addEventListener('click', () => this.toggleTouchpad());
        
        // Sensitivity toggle
        this.sensitivityCheckbox.addEventListener('change', (e) => {
            this.sensitivity = e.target.checked ? 2.0 : 1.0;
        });
        
        // Mouse button events
        Object.entries(this.mouseButtons).forEach(([button, elem]) => {
            elem.addEventListener('mousedown', () => this.mouseButtonPress(button, true));
            elem.addEventListener('mouseup', () => this.mouseButtonPress(button, false));
            elem.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.mouseButtonPress(button, true);
            });
            elem.addEventListener('touchend', (e) => {
                e.preventDefault();
                this.mouseButtonPress(button, false);
            });
        });
        
        // Touchpad canvas events - mouse
        this.canvas.addEventListener('mousedown', (e) => this.startTracking(e));
        this.canvas.addEventListener('mousemove', (e) => this.trackMovement(e));
        this.canvas.addEventListener('mouseup', () => this.stopTracking());
        this.canvas.addEventListener('mouseleave', () => this.stopTracking());
        
        // Touchpad canvas events - touch
        this.canvas.addEventListener('touchstart', (e) => this.startTracking(e));
        this.canvas.addEventListener('touchmove', (e) => this.trackMovement(e));
        this.canvas.addEventListener('touchend', () => this.stopTracking());
        this.canvas.addEventListener('touchcancel', () => this.stopTracking());
    }
    
    async toggleTouchpad() {
        if (!this.enabled) {
            // Just enable touchpad - device will be auto-acquired on first event
            this.enabled = true;
            this.enableBtn.textContent = 'Disable';
            this.enableBtn.classList.add('active');
            // Cache touchpad section element
            if (!this.touchpadSection) {
                this.touchpadSection = document.querySelector('.touchpad-section');
            }
            this.touchpadSection.classList.remove('disabled');
            this.touchpadDevice = 'mouse';
        } else {
            // Disable touchpad
            this.enabled = false;
            this.enableBtn.textContent = 'Enable';
            this.enableBtn.classList.remove('active');
            if (this.touchpadSection) {
                this.touchpadSection.classList.add('disabled');
            }
            this.touchpadDevice = null;
        }
    }
    
    async connectMouse() {
        // Send connect event for mouse device
        const connectMsg = {
            event: 'connect',
            device: 'mouse',
            name: 'Virtual Touchpad Mouse'
        };
        
        if (this.app.controller.transport === 'websocket' && this.app.controller.ws) {
            this.app.controller.ws.send(JSON.stringify(connectMsg));
        } else if (this.app.controller.transport === 'webrtc' && this.app.controller.dataChannel) {
            this.app.controller.dataChannel.send(JSON.stringify(connectMsg));
        } else {
            throw new Error('Not connected to server');
        }
        
        this.touchpadDevice = 'mouse';
    }
    
    async disconnectMouse() {
        if (!this.touchpadDevice) return;
        
        const disconnectMsg = {
            event: 'disconnect'
        };
        
        if (this.app.controller.transport === 'websocket' && this.app.controller.ws) {
            this.app.controller.ws.send(JSON.stringify(disconnectMsg));
        } else if (this.app.controller.transport === 'webrtc' && this.app.controller.dataChannel) {
            this.app.controller.dataChannel.send(JSON.stringify(disconnectMsg));
        }
        
        this.touchpadDevice = null;
    }
    
    startTracking(e) {
        if (!this.enabled) return;
        
        this.isTracking = true;
        this.canvas.classList.add('active');
        
        const rect = this.canvas.getBoundingClientRect();
        if (e.touches) {
            this.lastX = e.touches[0].clientX - rect.left;
            this.lastY = e.touches[0].clientY - rect.top;
        } else {
            this.lastX = e.clientX - rect.left;
            this.lastY = e.clientY - rect.top;
        }
        
        this.drawTouchpad(this.lastX, this.lastY);
    }
    
    trackMovement(e) {
        if (!this.enabled || !this.isTracking) return;
        
        e.preventDefault();
        
        const rect = this.canvas.getBoundingClientRect();
        let currentX, currentY;
        
        if (e.touches) {
            currentX = e.touches[0].clientX - rect.left;
            currentY = e.touches[0].clientY - rect.top;
        } else {
            currentX = e.clientX - rect.left;
            currentY = e.clientY - rect.top;
        }
        
        // Calculate delta movement
        const dx = Math.round((currentX - this.lastX) * this.sensitivity);
        const dy = Math.round((currentY - this.lastY) * this.sensitivity);
        
        if (dx !== 0 || dy !== 0) {
            this.sendMouseMovement(dx, dy);
            this.mouseDeltaDisplay.textContent = `${dx}, ${dy}`;
        }
        
        this.lastX = currentX;
        this.lastY = currentY;
        
        this.drawTouchpad(currentX, currentY);
    }
    
    stopTracking() {
        this.isTracking = false;
        this.canvas.classList.remove('active');
        this.drawTouchpad();
        this.mouseDeltaDisplay.textContent = '0, 0';
    }
    
    sendMouseMovement(dx, dy) {
        if (!this.enabled) return;
        
        // Send axis events with device parameter to target mouse device
        const msgX = {
            event: 'axis',
            device: 'mouse',
            name: 'dx',
            value: dx
        };
        
        const msgY = {
            event: 'axis',
            device: 'mouse',
            name: 'dy',
            value: dy
        };
        
        if (this.app.controller.transport === 'websocket' && this.app.controller.ws) {
            this.app.controller.ws.send(JSON.stringify(msgX));
            this.app.controller.ws.send(JSON.stringify(msgY));
        } else if (this.app.controller.transport === 'webrtc' && this.app.controller.dataChannel) {
            this.app.controller.dataChannel.send(JSON.stringify(msgX));
            this.app.controller.dataChannel.send(JSON.stringify(msgY));
        }
    }
    
    mouseButtonPress(button, pressed) {
        if (!this.enabled) return;
        
        // Send button event with device parameter
        const msg = {
            event: 'button',
            device: 'mouse',
            name: button,
            pressed: pressed
        };
        
        if (this.app.controller.transport === 'websocket' && this.app.controller.ws) {
            this.app.controller.ws.send(JSON.stringify(msg));
        } else if (this.app.controller.transport === 'webrtc' && this.app.controller.dataChannel) {
            this.app.controller.dataChannel.send(JSON.stringify(msg));
        }
        
        // Visual feedback
        this.mouseButtons[button].classList.toggle('active', pressed);
    }
    
    drawTouchpad(cursorX = null, cursorY = null) {
        const ctx = this.ctx;
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Draw grid
        ctx.strokeStyle = 'rgba(0, 212, 255, 0.1)';
        ctx.lineWidth = 1;
        
        // Vertical lines
        for (let x = 0; x <= width; x += 40) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
            ctx.stroke();
        }
        
        // Horizontal lines
        for (let y = 0; y <= height; y += 40) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
        
        // Draw cursor if tracking
        if (cursorX !== null && cursorY !== null) {
            // Outer circle
            ctx.beginPath();
            ctx.arc(cursorX, cursorY, 15, 0, Math.PI * 2);
            ctx.strokeStyle = '#00ff88';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // Inner dot
            ctx.beginPath();
            ctx.arc(cursorX, cursorY, 3, 0, Math.PI * 2);
            ctx.fillStyle = '#00ff88';
            ctx.fill();
            
            // Crosshair
            ctx.beginPath();
            ctx.moveTo(cursorX - 10, cursorY);
            ctx.lineTo(cursorX + 10, cursorY);
            ctx.moveTo(cursorX, cursorY - 10);
            ctx.lineTo(cursorX, cursorY + 10);
            ctx.strokeStyle = '#00ff88';
            ctx.lineWidth = 1;
            ctx.stroke();
        }
    }
}
