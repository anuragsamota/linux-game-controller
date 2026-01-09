/**
 * GamepadUI - Manages all UI elements and interactions
 * Handles rendering and user input
 */

class GamepadUI {
    constructor() {
        this.pressedButtons = new Set();
        this.activeAxesMap = new Map();
        this.stickPositions = {
            left: { x: 0, y: 0 },
            right: { x: 0, y: 0 }
        };
        this.triggerValues = {
            l2: 0,
            r2: 0
        };

        this.initDOM();
        this.initCanvases();
    }

    /**
     * Initialize DOM references
     */
    initDOM() {
        // Connection
        this.connectBtn = document.getElementById('connectBtn');
        this.disconnectBtn = document.getElementById('disconnectBtn');
        this.serverHost = document.getElementById('serverHost');
        this.serverPort = document.getElementById('serverPort');
        this.deviceName = document.getElementById('deviceName');
        this.transportSelect = document.getElementById('transportSelect');
        this.statusDisplay = document.getElementById('statusDisplay');

        // Buttons (all 13)
        this.buttonElements = {};
        const buttonNames = ['a', 'b', 'x', 'y', 'l1', 'r1', 'l2_click', 'r2_click', 'back', 'start', 'guide', 'l3', 'r3'];
        
        buttonNames.forEach(name => {
            const elemId = name === 'l2_click' ? 'l2ClickBtn' : 
                          name === 'r2_click' ? 'r2ClickBtn' :
                          name + 'Btn';
            this.buttonElements[name] = document.getElementById(elemId);
        });

        // D-Pad
        this.dpadButtons = {
            up: document.getElementById('dpadUp'),
            down: document.getElementById('dpadDown'),
            left: document.getElementById('dpadLeft'),
            right: document.getElementById('dpadRight')
        };

        // Sticks
        this.leftStickCanvas = document.getElementById('leftStickCanvas');
        this.rightStickCanvas = document.getElementById('rightStickCanvas');
        this.stickContexts = {
            left: this.leftStickCanvas.getContext('2d'),
            right: this.rightStickCanvas.getContext('2d')
        };

        // Stick values
        this.stickValueDisplays = {
            lx: document.getElementById('lxValue'),
            ly: document.getElementById('lyValue'),
            rx: document.getElementById('rxValue'),
            ry: document.getElementById('ryValue')
        };

        // Triggers
        this.triggerSliders = {
            l2: document.getElementById('l2Slider'),
            r2: document.getElementById('r2Slider')
        };
        this.triggerValueDisplays = {
            l2: document.getElementById('l2Value'),
            r2: document.getElementById('r2Value')
        };
    }

    /**
     * Initialize canvas drawing contexts
     */
    initCanvases() {
        this.drawSticks();
    }

    /**
     * Update button visual state
     */
    updateButtonVisual(name, pressed) {
        const elem = this.buttonElements[name];
        if (!elem) return;

        if (pressed) {
            elem.classList.add('active');
            this.pressedButtons.add(name);
        } else {
            elem.classList.remove('active');
            this.pressedButtons.delete(name);
        }
    }

    /**
     * Update D-pad visual state
     */
    updateDpadVisual(direction, pressed) {
        const elem = this.dpadButtons[direction];
        if (!elem) return;

        if (pressed) {
            elem.classList.add('active');
        } else {
            elem.classList.remove('active');
        }
    }

    /**
     * Update stick position
     */
    updateStickPosition(stick, x, y) {
        this.stickPositions[stick] = { x, y };
        
        if (stick === 'left') {
            this.stickValueDisplays.lx.textContent = x.toFixed(2);
            this.stickValueDisplays.ly.textContent = y.toFixed(2);
            this.activeAxesMap.set('lx', x);
            this.activeAxesMap.set('ly', y);
        } else {
            this.stickValueDisplays.rx.textContent = x.toFixed(2);
            this.stickValueDisplays.ry.textContent = y.toFixed(2);
            this.activeAxesMap.set('rx', x);
            this.activeAxesMap.set('ry', y);
        }

        // Throttle drawing with requestAnimationFrame to optimize rendering
        if (!this._drawScheduled) {
            this._drawScheduled = true;
            requestAnimationFrame(() => {
                this.drawSticks();
                this._drawScheduled = false;
            });
        }
    }

    /**
     * Reset stick to center
     */
    resetStick(stick) {
        this.updateStickPosition(stick, 0, 0);
    }

    /**
     * Update trigger value
     */
    updateTrigger(trigger, value) {
        const percent = Math.round(value * 100);
        this.triggerValues[trigger] = value;
        this.triggerValueDisplays[trigger].textContent = percent + '%';
        this.activeAxesMap.set(trigger === 'l2' ? 'lt' : 'rt', value);
    }

    /**
     * Draw analog sticks
     */
    drawSticks() {
        this.drawStick(this.stickContexts.left, this.stickPositions.left);
        this.drawStick(this.stickContexts.right, this.stickPositions.right);
    }

    /**
     * Draw single stick on canvas
     */
    drawStick(ctx, position) {
        const w = ctx.canvas.width;
        const h = ctx.canvas.height;
        const centerX = w / 2;
        const centerY = h / 2;
        const outerRadius = 70;
        const innerRadius = 15;

        // Clear
        ctx.clearRect(0, 0, w, h);

        // Outer circle (boundary)
        ctx.strokeStyle = '#00d4ff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(centerX, centerY, outerRadius, 0, Math.PI * 2);
        ctx.stroke();

        // Grid
        ctx.strokeStyle = 'rgba(0, 212, 255, 0.2)';
        ctx.lineWidth = 1;
        
        // Horizontal line
        ctx.beginPath();
        ctx.moveTo(centerX - outerRadius, centerY);
        ctx.lineTo(centerX + outerRadius, centerY);
        ctx.stroke();
        
        // Vertical line
        ctx.beginPath();
        ctx.moveTo(centerX, centerY - outerRadius);
        ctx.lineTo(centerX, centerY + outerRadius);
        ctx.stroke();

        // Stick position
        const stickX = centerX + position.x * 60;
        const stickY = centerY + position.y * 60;

        // Inner circle (stick)
        ctx.fillStyle = 'rgba(0, 212, 255, 0.3)';
        ctx.beginPath();
        ctx.arc(stickX, stickY, innerRadius, 0, Math.PI * 2);
        ctx.fill();

        ctx.strokeStyle = '#00d4ff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(stickX, stickY, innerRadius, 0, Math.PI * 2);
        ctx.stroke();
    }

    /**
     * Update connection status display
     */
    setConnected(connected, deviceName) {
        if (connected) {
            this.statusDisplay.classList.remove('disconnected');
            this.statusDisplay.classList.add('connected');
            this.statusDisplay.innerHTML = `<span class="status-icon">●</span><span class="status-text">Connected: ${deviceName}</span>`;
            this.connectBtn.disabled = true;
            this.disconnectBtn.disabled = false;
        } else {
            this.statusDisplay.classList.remove('connected');
            this.statusDisplay.classList.add('disconnected');
            this.statusDisplay.innerHTML = `<span class="status-icon">●</span><span class="status-text">Disconnected</span>`;
            this.connectBtn.disabled = false;
            this.disconnectBtn.disabled = true;
            this.resetAllControls();
        }
    }

    /**
     * Reset all controls to neutral state
     */
    resetAllControls() {
        // Reset buttons
        Object.values(this.buttonElements).forEach((elem) => {
            if (elem) elem.classList.remove('active');
        });
        this.pressedButtons.clear();

        // Reset D-pad
        Object.values(this.dpadButtons).forEach(elem => {
            elem.classList.remove('active');
        });

        // Reset sticks
        this.updateStickPosition('left', 0, 0);
        this.updateStickPosition('right', 0, 0);

        // Reset triggers
        this.triggerSliders.l2.value = 0;
        this.triggerSliders.r2.value = 0;
        this.triggerValues.l2 = 0;
        this.triggerValues.r2 = 0;
        this.triggerValueDisplays.l2.textContent = '0%';
        this.triggerValueDisplays.r2.textContent = '0%';

        this.activeAxesMap.clear();
    }

    /**
     * Get current connection info
     */
    getConnectionInfo() {
        return {
            host: this.serverHost.value,
            port: this.serverPort.value,
            device: this.deviceName.value,
            transport: this.transportSelect.value
        };
    }
}
