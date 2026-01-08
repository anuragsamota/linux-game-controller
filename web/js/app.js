/**
 * Virtual Game Controller - Main Application
 * Integrates GamepadController and GamepadUI
 */

class VirtualGamepadApp {
    constructor() {
        this.controller = new GamepadController();
        this.ui = new GamepadUI();
        this.touchpad = null; // Initialize after DOM ready
        
        this.isStickActive = {
            left: false,
            right: false
        };
        this.dpadState = {
            x: 0,
            y: 0
        };

        // Screen management
        this.connectionScreen = document.getElementById('connectionScreen');
        this.gamepadScreen = document.getElementById('gamepadScreen');
        this.fullscreenCheck = document.getElementById('fullscreenCheck');

        this.setupUICallbacks();
        this.setupInputHandlers();
    }

    /**
     * Switch between connection and gamepad screens
     */
    showConnectionScreen() {
        this.connectionScreen.classList.add('active');
        this.gamepadScreen.classList.remove('active');
        
        // Exit fullscreen if active
        if (document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement) {
            this.exitFullscreen();
        }
    }

    showGamepadScreen() {
        this.connectionScreen.classList.remove('active');
        this.gamepadScreen.classList.add('active');
        
        // Enter fullscreen if checkbox is checked
        if (this.fullscreenCheck.checked) {
            this.enterFullscreen();
        }
    }

    enterFullscreen() {
        const elem = document.documentElement;
        if (elem.requestFullscreen) {
            elem.requestFullscreen().catch(err => {
                console.log('Fullscreen request failed:', err);
            });
        } else if (elem.webkitRequestFullscreen) {
            elem.webkitRequestFullscreen();
        } else if (elem.mozRequestFullScreen) {
            elem.mozRequestFullScreen();
        }
    }

    exitFullscreen() {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        }
    }

    /**
     * Setup UI event callbacks
     */
    setupUICallbacks() {
        // Connection buttons
        this.ui.connectBtn.addEventListener('click', () => this.connect());
        
        // Disconnect button in gamepad screen
        const disconnectGamepadBtn = document.getElementById('disconnectGamepadBtn');
        if (disconnectGamepadBtn) {
            disconnectGamepadBtn.addEventListener('click', () => this.disconnect());
        }
        
        // Toggle touchpad button in gamepad header
        const toggleTouchpadBtn = document.getElementById('toggleTouchpadBtn');
        if (toggleTouchpadBtn) {
            toggleTouchpadBtn.addEventListener('click', () => {
                const touchpadSection = document.getElementById('touchpadSection');
                if (touchpadSection.style.display === 'none') {
                    touchpadSection.style.display = 'block';
                    toggleTouchpadBtn.textContent = 'Hide Touchpad';
                } else {
                    touchpadSection.style.display = 'none';
                    toggleTouchpadBtn.textContent = 'Show Touchpad';
                }
            });
        }
        
        // Transport selector auto-port switching
        this.ui.transportSelect.addEventListener('change', () => {
            const portField = this.ui.serverPort;
            const value = this.ui.transportSelect.value;
            if (value === 'webrtc' && portField.value === '8765') {
                portField.value = '8787';
            } else if (value === 'websocket' && portField.value === '8787') {
                portField.value = '8765';
            }
        });

        // Override controller callbacks
        this.controller.onConnected = () => {
            this.showGamepadScreen();
        };

        this.controller.onDisconnected = () => {
            this.showConnectionScreen();
        };

        this.controller.onError = (msg) => {
            console.error(`Connection Error: ${msg}`);
            alert(`Connection Error: ${msg}`);
        };
    }

    /**
     * Setup input event handlers
     */
    setupInputHandlers() {
        this.setupButtonHandlers();
        this.setupDpadHandlers();
        this.setupStickHandlers();
        this.setupTriggerHandlers();
    }

    /**
     * Setup button handlers (A, B, X, Y, L1, R1, L2_click, R2_click, Back, Start, Guide, L3, R3)
     */
    setupButtonHandlers() {
        const buttonNames = ['a', 'b', 'x', 'y', 'l1', 'r1', 'l2_click', 'r2_click', 'back', 'start', 'guide', 'l3', 'r3'];
        
        buttonNames.forEach(name => {
            const elem = this.ui.buttonElements[name];
            if (!elem) return;

            // Mouse events
            elem.addEventListener('mousedown', () => this.buttonDown(name));
            elem.addEventListener('mouseup', () => this.buttonUp(name));
            elem.addEventListener('mouseleave', () => this.buttonUp(name));

            // Touch events
            elem.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.buttonDown(name);
            }, { passive: false });  // Need false for preventDefault
            elem.addEventListener('touchend', (e) => {
                e.preventDefault();
                this.buttonUp(name);
            }, { passive: false });
        });
    }

    /**
     * Handle button press down
     */
    buttonDown(name) {
        this.controller.sendButton(name, true);
        this.ui.updateButtonVisual(name, true);
    }

    /**
     * Handle button press up
     */
    buttonUp(name) {
        this.controller.sendButton(name, false);
        this.ui.updateButtonVisual(name, false);
    }

    /**
     * Setup D-pad handlers
     */
    setupDpadHandlers() {
        Object.entries(this.ui.dpadButtons).forEach(([direction, elem]) => {
            // Mouse events
            elem.addEventListener('mousedown', () => this.dpadPress(direction, true));
            elem.addEventListener('mouseup', () => this.dpadPress(direction, false));
            elem.addEventListener('mouseleave', () => this.dpadPress(direction, false));

            // Touch events
            elem.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.dpadPress(direction, true);
            }, { passive: false });
            elem.addEventListener('touchend', (e) => {
                e.preventDefault();
                this.dpadPress(direction, false);
            }, { passive: false });
        });
    }

    /**
     * Handle D-pad press
     */
    dpadPress(direction, pressed) {
        const directionMap = {
            up: { axis: 'dpad_y', value: pressed ? -1 : 0 },
            down: { axis: 'dpad_y', value: pressed ? 1 : 0 },
            left: { axis: 'dpad_x', value: pressed ? -1 : 0 },
            right: { axis: 'dpad_x', value: pressed ? 1 : 0 }
        };

        const mapping = directionMap[direction];
        this.controller.sendAxis(mapping.axis, mapping.value);
        this.ui.updateDpadVisual(direction, pressed);
    }

    /**
     * Setup analog stick handlers
     */
    setupStickHandlers() {
        const sticks = [
            { canvas: this.ui.leftStickCanvas, type: 'left', clickBtn: this.ui.buttonElements['l3'] },
            { canvas: this.ui.rightStickCanvas, type: 'right', clickBtn: this.ui.buttonElements['r3'] }
        ];

        sticks.forEach(({ canvas, type, clickBtn }) => {
            // Mouse events
            canvas.addEventListener('mousedown', (e) => this.stickStart(e, type));
            canvas.addEventListener('mousemove', (e) => this.stickMove(e, type));
            canvas.addEventListener('mouseup', () => this.stickEnd(type));
            canvas.addEventListener('mouseleave', () => this.stickEnd(type));

            // Touch events
            canvas.addEventListener('touchstart', (e) => this.stickStart(e, type));
            canvas.addEventListener('touchmove', (e) => this.stickMove(e, type));
            canvas.addEventListener('touchend', () => this.stickEnd(type));
            canvas.addEventListener('touchcancel', () => this.stickEnd(type));

            // Click button handler
            if (clickBtn) {
                const buttonName = type === 'left' ? 'l3' : 'r3';
                clickBtn.addEventListener('mousedown', () => this.buttonDown(buttonName));
                clickBtn.addEventListener('mouseup', () => this.buttonUp(buttonName));
                clickBtn.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    this.buttonDown(buttonName);
                });
                clickBtn.addEventListener('touchend', (e) => {
                    e.preventDefault();
                    this.buttonUp(buttonName);
                });
            }
        });
    }

    /**
     * Handle stick start
     */
    stickStart(e, type) {
        this.isStickActive[type] = true;
        this.stickMove(e, type);
    }

    /**
     * Handle stick move
     */
    stickMove(e, type) {
        if (!this.isStickActive[type]) return;

        const canvas = type === 'left' ? this.ui.leftStickCanvas : this.ui.rightStickCanvas;
        const rect = canvas.getBoundingClientRect();
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = 60;

        let clientX, clientY;
        if (e.touches) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }

        const x = clientX - rect.left - centerX;
        const y = clientY - rect.top - centerY;
        const distance = Math.sqrt(x * x + y * y);
        const angle = Math.atan2(y, x);

        const maxDistance = Math.min(distance, radius);
        const normalizedX = (Math.cos(angle) * maxDistance) / radius;
        const normalizedY = (Math.sin(angle) * maxDistance) / radius;

        // Send axis values
        const xAxis = type === 'left' ? 'lx' : 'rx';
        const yAxis = type === 'left' ? 'ly' : 'ry';

        this.controller.sendAxis(xAxis, normalizedX);
        this.controller.sendAxis(yAxis, normalizedY);

        // Update UI
        this.ui.updateStickPosition(type, normalizedX, normalizedY);
    }

    /**
     * Handle stick end
     */
    stickEnd(type) {
        this.isStickActive[type] = false;

        const xAxis = type === 'left' ? 'lx' : 'rx';
        const yAxis = type === 'left' ? 'ly' : 'ry';

        this.controller.sendAxis(xAxis, 0);
        this.controller.sendAxis(yAxis, 0);

        this.ui.resetStick(type);
    }

    /**
     * Setup trigger handlers
     */
    setupTriggerHandlers() {
        this.ui.triggerSliders.l2.addEventListener('input', (e) => {
            const value = parseInt(e.target.value) / 100;
            this.controller.sendAxis('lt', value);
            this.ui.updateTrigger('l2', value);
        });

        this.ui.triggerSliders.r2.addEventListener('input', (e) => {
            const value = parseInt(e.target.value) / 100;
            this.controller.sendAxis('rt', value);
            this.ui.updateTrigger('r2', value);
        });
    }

    /**
     * Connect to server
     */
    connect() {
        const info = this.ui.getConnectionInfo();
        this.controller.connect(info.host, parseInt(info.port), info.device, info.transport);
    }

    /**
     * Disconnect from server
     */
    disconnect() {
        this.controller.disconnect();
        this.showConnectionScreen();
    }
}

/**
 * Initialize app when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VirtualGamepadApp();
    
    // Initialize touchpad controller
    window.app.touchpad = new TouchpadController(window.app);
    
    // Auto-fill server host with current URL's hostname
    const serverHostInput = document.getElementById('serverHost');
    if (serverHostInput && window.location.hostname) {
        serverHostInput.value = window.location.hostname;
        serverHostInput.placeholder = window.location.hostname;
    }
});
