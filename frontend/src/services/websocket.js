class WebSocketService {
    constructor() {
        this.socket = null;
        this.listeners = new Set();
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect() {
        // Prevent multiple connections
        if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host; // e.g. localhost:4202
        const wsUrl = `${protocol}//${host}/api/v1/sync/ws/sync-status`;

        console.log(`Connecting to WebSocket: ${wsUrl}`);
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.notifyListeners(data);
            } catch (e) {
                console.error('Error parsing WS message', e);
            }
        };

        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            this.attemptReconnect();
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error', error);
        };
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const timeout = Math.min(1000 * (2 ** this.reconnectAttempts), 30000);
            console.log(`Reconnecting in ${timeout}ms...`);
            setTimeout(() => this.connect(), timeout);
        }
    }

    subscribe(callback) {
        this.listeners.add(callback);
        if (!this.isConnected && (!this.socket || this.socket.readyState === WebSocket.CLOSED)) {
            this.connect();
        }
        return () => this.listeners.delete(callback);
    }

    notifyListeners(data) {
        this.listeners.forEach(callback => callback(data));
    }
}

export const webSocketService = new WebSocketService();
