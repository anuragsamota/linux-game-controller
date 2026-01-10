import React, { useState } from 'react';

const ConnectionScreen = ({ onConnect, isConnecting }) => {
  const [host, setHost] = useState(window.location.hostname || 'localhost');
  const [port, setPort] = useState('8765');
  const [deviceName, setDeviceName] = useState('LibrePad Gamepad');

  const handleConnect = (e) => {
    e.preventDefault();
    onConnect(host, port, deviceName);
  };

  return (
    <div className="min-h-screen w-screen overflow-y-auto bg-linear-to-br from-slate-900 via-slate-800 to-slate-900 py-8 px-4">
      <div className="flex items-center justify-center min-h-[calc(100vh-2rem)]">
        <div className="bg-gray-900 border border-cyan-500/30 rounded-2xl p-8 max-w-md w-full shadow-2xl shadow-cyan-500/20">
          <h1 className="text-3xl font-bold text-center mb-2 bg-linear-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
            LibrePad Controller
          </h1>
          <p className="text-center text-gray-400 mb-8 text-sm">Connect to your LibrePad server</p>
          
          <form onSubmit={handleConnect} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-cyan-300 mb-2">Server Host</label>
              <input
                type="text"
                value={host}
                onChange={(e) => setHost(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800 border border-cyan-500/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 placeholder-gray-500"
                placeholder="localhost or IP address"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-cyan-300 mb-2">WebSocket Port</label>
              <input
                type="text"
                value={port}
                onChange={(e) => setPort(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800 border border-cyan-500/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 placeholder-gray-500"
                placeholder="8765"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-cyan-300 mb-2">Device Name</label>
              <input
                type="text"
                value={deviceName}
                onChange={(e) => setDeviceName(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800 border border-cyan-500/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 placeholder-gray-500"
                placeholder="LibrePad Gamepad"
                required
              />
            </div>
            
            <button
              type="submit"
              disabled={isConnecting}
              className="w-full py-3 bg-linear-to-r from-cyan-600 to-cyan-500 text-white font-semibold rounded-lg hover:from-cyan-500 hover:to-cyan-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/30"
            >
              {isConnecting ? 'Connecting...' : 'Connect'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ConnectionScreen;
