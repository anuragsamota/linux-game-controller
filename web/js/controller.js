/**
 * GamepadController - transport-agnostic client for virtual gamepad control.
 * Supports WebSocket and WebRTC (UDP via STUN/TURN).
 */

class GamepadController {
    constructor() {
        this.transport = 'websocket';
        this.ws = null;
        this.signalingSocket = null;
        this.rtcPeer = null;
        this.dataChannel = null;
        this.isConnected = false;
        this.serverHost = '';
        this.serverPort = '';
        this.deviceName = '';
        this.messageQueue = [];
        this.connectionAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.iceServers = [
            {
                urls: [
                    'stun:stun.l.google.com:19302',
                    'stun:stun1.l.google.com:19302',
                    'stun:stun2.l.google.com:19302',
                    'stun:stun3.l.google.com:19302',
                    'stun:stun4.l.google.com:19302'
                ]
            },
            {
                // Public TURN relay to aid NAT traversal (Google publishes STUN only)
                urls: [
                    'turn:global.relay.metered.ca:80',
                    'turn:global.relay.metered.ca:443',
                    'turn:global.relay.metered.ca:443?transport=tcp'
                ],
                username: 'openrelayproject',
                credential: 'openrelayproject'
            }
        ];
    }

    /**
     * Connect to chosen transport
     */
    connect(host, port, deviceName, transport = 'websocket') {
        if (this.isConnected) {
            console.warn('Already connected');
            return;
        }

        this.transport = transport || 'websocket';
        this.serverHost = host || '127.0.0.1';
        this.serverPort = port || '8765';
        this.deviceName = deviceName || 'Virtual Gamepad';

        if (this.transport === 'webrtc') {
            this.connectWebRTC().catch((err) => this.handleError(err));
        } else {
            this.connectWebSocket();
        }
    }

    /**
     * WebSocket connection setup
     */
    connectWebSocket() {
        try {
            const url = `ws://${this.serverHost}:${this.serverPort}`;
            this.ws = new WebSocket(url);

            this.ws.onopen = () => this.handleWebSocketOpen();
            this.ws.onmessage = (e) => this.handleWebSocketMessage(e.data);
            this.ws.onerror = (e) => this.handleError(e);
            this.ws.onclose = () => this.handleTransportClosed();
        } catch (error) {
            this.handleError(error);
        }
    }

    /**
     * WebRTC connection setup with WebSocket signaling
     */
    async connectWebRTC() {
        try {
            this.rtcPeer = new RTCPeerConnection({ iceServers: this.iceServers });
            
            // Track connection state
            this.rtcPeer.onicegatheringstatechange = () => {
                // ICE gathering in progress
            };
            
            this.rtcPeer.onicecandidateerror = (e) => {
                console.warn('ICE candidate error:', e);
            };
            
            // Create data channel BEFORE signaling
            this.dataChannel = this.rtcPeer.createDataChannel('gamepad', {
                ordered: false  // Low-latency over order
            });

            this.dataChannel.onopen = () => {
                this.connectionAttempts = 0;
                this.processMessageQueue();
            };
            this.dataChannel.onmessage = (e) => this.handleRtcMessage(e.data);
            this.dataChannel.onerror = (e) => {
                console.error('Data channel error:', e);
                this.handleError(e);
            };
            this.dataChannel.onclose = () => {
                this.handleTransportClosed();
            };

            this.rtcPeer.onconnectionstatechange = () => {
                const state = this.rtcPeer.connectionState;
                if (['disconnected', 'failed', 'closed'].includes(state)) {
                    this.handleTransportClosed();
                }
            };

            this.rtcPeer.onicecandidate = (event) => {
                if (event.candidate) {
                    if (this.signalingSocket && this.signalingSocket.readyState === WebSocket.OPEN) {
                        this.signalingSocket.send(JSON.stringify({
                            type: 'candidate',
                            candidate: {
                                candidate: event.candidate.candidate,
                                sdpMid: event.candidate.sdpMid,
                                sdpMLineIndex: event.candidate.sdpMLineIndex
                            }
                        }));
                    }
                }
            };

            // Open signaling connection
            const signalingUrl = `ws://${this.serverHost}:${this.serverPort}`;
            this.signalingSocket = new WebSocket(signalingUrl);
            this.signalingSocket.onmessage = (e) => this.handleSignalingMessage(e.data);
            this.signalingSocket.onerror = (e) => {
                console.error('Signaling error:', e);
                this.handleError(e);
            };
            this.signalingSocket.onclose = () => {
                this.handleTransportClosed();
            };

            await new Promise((resolve, reject) => {
                const handleOpen = () => {
                    this.signalingSocket.removeEventListener('error', handleErr);
                    resolve();
                };
                const handleErr = (err) => {
                    console.error('Signaling open error:', err);
                    this.signalingSocket.removeEventListener('open', handleOpen);
                    reject(err);
                };
                this.signalingSocket.addEventListener('open', handleOpen, { once: true });
                this.signalingSocket.addEventListener('error', handleErr, { once: true });
            });

            const offer = await this.rtcPeer.createOffer();
            await this.rtcPeer.setLocalDescription(offer);

            this.signalingSocket.send(JSON.stringify({
                type: 'offer',
                sdp: this.rtcPeer.localDescription.sdp,
                sdpType: this.rtcPeer.localDescription.type
            }));
        } catch (error) {
            console.error('WebRTC connection error:', error);
            this.handleError(error);
        }
    }

    /**
     * Handle WebSocket open
     */
    handleWebSocketOpen() {
        this.connectionAttempts = 0;
        this.processMessageQueue();
    }

    /**
     * Handle WebSocket server message
     */
    handleWebSocketMessage(raw) {
        this.handleServerPayload(raw);
    }

    /**
     * Handle signaling channel messages (SDP/ICE)
     */
    async handleSignalingMessage(raw) {
        try {
            const msg = JSON.parse(raw);
            
            if (msg.type === 'answer' && this.rtcPeer) {
                const desc = new RTCSessionDescription({ type: msg.sdpType, sdp: msg.sdp });
                await this.rtcPeer.setRemoteDescription(desc);
            } else if (msg.type === 'candidate' && this.rtcPeer) {
                const candidateObj = msg.candidate;
                if (candidateObj && candidateObj.candidate) {
                    try {
                        const candidate = new RTCIceCandidate({
                            candidate: candidateObj.candidate,
                            sdpMid: candidateObj.sdpMid,
                            sdpMLineIndex: candidateObj.sdpMLineIndex
                        });
                        await this.rtcPeer.addIceCandidate(candidate);
                    } catch (e) {
                        console.warn('Failed to add ICE candidate:', e.message);
                    }
                }
            }
        } catch (error) {
            console.error('Signaling message parse error:', error);
            this.handleError(error);
        }
    }

    /**
     * Handle data-channel messages
     */
    handleRtcMessage(raw) {
        this.handleServerPayload(raw);
    }

    /**
     * Common server payload handler
     */
    handleServerPayload(raw) {
        try {
            const data = typeof raw === 'string' ? JSON.parse(raw) : JSON.parse(raw.data || '{}');

            if (data.type === 'welcome') {
                this.sendConnect(this.deviceName);
            } else if (data.type === 'ok') {
                if (data.connected) {
                    this.isConnected = true;
                    this.onConnected();
                }
            } else if (data.type === 'error') {
                this.onError(data.message || 'Server error');
            } else if (data.type === 'pong') {
                // ignore
            }
        } catch (error) {
            console.error('Failed to parse server message:', error);
        }
    }

    /**
     * Handle errors
     */
    handleError(error) {
        const message = (error && error.message) ? error.message : 'Connection failed';
        console.error('Controller error:', message);
        this.onError(message);
    }

    /**
     * Handle transport close for both WebSocket and WebRTC
     */
    handleTransportClosed() {
        if (this.isConnected) {
            this.isConnected = false;
            this.onDisconnected();
        }
    }

    /**
     * Send connect message to server
     */
    sendConnect(deviceName) {
        const msg = {
            event: 'connect',
            device: 'standard',
            name: deviceName
        };
        this.send(msg);
    }

    /**
     * Send button press event
     */
    sendButton(name, pressed) {
        if (!this.isConnected) return;
        // Reuse message object to reduce GC pressure
        if (!this._buttonMsg) {
            this._buttonMsg = { event: 'button', device: 'standard', name: '', pressed: false };
        }
        this._buttonMsg.name = name;
        this._buttonMsg.pressed = pressed;
        this.send(this._buttonMsg);
    }

    /**
     * Send axis value
     */
    sendAxis(name, value) {
        if (!this.isConnected) return;
        // Reuse message object to reduce GC pressure
        if (!this._axisMsg) {
            this._axisMsg = { event: 'axis', device: 'standard', name: '', value: 0 };
        }
        this._axisMsg.name = name;
        this._axisMsg.value = value;
        this.send(this._axisMsg);
    }

    /**
     * Send disconnect message
     */
    sendDisconnect() {
        const msg = { event: 'disconnect' };
        this.send(msg);
    }

    /**
     * Send message to server using active transport
     */
    send(message) {
        if (this.transport === 'webrtc') {
            this.sendViaDataChannel(message);
            return;
        }

        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.messageQueue.push(message);
            return;
        }

        try {
            this.ws.send(JSON.stringify(message));
        } catch (error) {
            console.error('Failed to send message:', error);
            this.messageQueue.push(message);
        }
    }

    /**
     * Send via WebRTC data channel
     */
    sendViaDataChannel(message) {
        if (!this.dataChannel || this.dataChannel.readyState !== 'open') {
            this.messageQueue.push(message);
            return;
        }

        try {
            this.dataChannel.send(JSON.stringify(message));
        } catch (error) {
            console.error('Failed to send via data channel:', error);
            this.messageQueue.push(message);
        }
    }

    /**
     * Process queued messages
     */
    processMessageQueue() {
        if (!this.messageQueue.length) return;
        const pending = [...this.messageQueue];
        this.messageQueue = [];
        pending.forEach((msg) => this.send(msg));
    }

    /**
     * Disconnect from server
     */
    disconnect() {
        if (this.isConnected) {
            this.sendDisconnect();
        }

        if (this.transport === 'webrtc') {
            if (this.signalingSocket && this.signalingSocket.readyState === WebSocket.OPEN) {
                this.signalingSocket.send(JSON.stringify({ type: 'bye' }));
            }
            if (this.dataChannel && this.dataChannel.readyState !== 'closed') {
                this.dataChannel.close();
            }
            if (this.rtcPeer) {
                this.rtcPeer.close();
            }
            if (this.signalingSocket) {
                this.signalingSocket.close();
            }
            this.dataChannel = null;
            this.rtcPeer = null;
            this.signalingSocket = null;
        } else if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        const wasConnected = this.isConnected;
        this.isConnected = false;
        if (wasConnected) {
            this.onDisconnected();
        }
    }

    /**
     * Callback when connected (override in subclass)
     */
    onConnected() {
        // Override in subclass
    }

    /**
     * Callback when disconnected (override in subclass)
     */
    onDisconnected() {
        // Override in subclass
    }

    /**
     * Callback on error (override in subclass)
     */
    onError(message) {
        console.error('Controller error:', message);
    }

    /**
     * Get connection status
     */
    getStatus() {
        return {
            isConnected: this.isConnected,
            host: this.serverHost,
            port: this.serverPort,
            device: this.deviceName,
            transport: this.transport
        };
    }
}
