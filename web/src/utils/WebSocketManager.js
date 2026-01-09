class WebSocketManager {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 3;
    this.messageQueue = [];
    this.listeners = { open: [], close: [], error: [], message: [] };
  }

  connect(host, port, deviceName = 'Virtual Gamepad') {
    return new Promise((resolve, reject) => {
      try {
        const url = `ws://${host}:${port}`;
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.send({ event: 'connect', device: 'standard', name: deviceName });
          while (this.messageQueue.length > 0) this.send(this.messageQueue.shift());
          this.emit('open');
          resolve();
        };

        this.ws.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data);
            this.emit('message', data);
          } catch (err) {
            console.error('Failed to parse message:', err);
          }
        };

        this.ws.onerror = (error) => {
          this.emit('error', error);
          reject(error);
        };

        this.ws.onclose = () => {
          this.isConnected = false;
          this.emit('close');
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect() {
    if (this.ws) {
      this.send({ event: 'disconnect' });
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
    }
  }

  send(message) {
    if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      this.messageQueue.push(message);
    }
  }

  sendButton(buttonName, pressed) {
    this.send({ event: 'button', device: 'standard', name: buttonName, pressed });
  }

  sendAxis(axisName, value) {
    this.send({ event: 'axis', device: 'standard', name: axisName, value });
  }

  on(event, callback) {
    if (this.listeners[event]) this.listeners[event].push(callback);
  }

  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  emit(event, ...args) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(...args));
    }
  }
}

export default WebSocketManager;
