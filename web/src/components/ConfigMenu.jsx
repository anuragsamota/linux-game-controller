import  { useState } from 'react';
import { DEFAULT_CONFIGS, createNewConfig } from '../utils/defaultConfigs';

const ConfigMenu = ({ 
  configs, 
  activeConfigId, 
  onSelectConfig, 
  onCreateConfig,
  onDuplicateConfig,
  onDeleteConfig,
  onRenameConfig,
  onClose,
  onImportConfig
}) => {
  const [isCreating, setIsCreating] = useState(false);
  const [newConfigName, setNewConfigName] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editingName, setEditingName] = useState('');

  const handleCreate = () => {
    if (newConfigName.trim()) {
      const newConfig = createNewConfig(newConfigName.trim());
      onCreateConfig(newConfig);
      setNewConfigName('');
      setIsCreating(false);
    }
  };

  const handleRename = (configId) => {
    if (editingName.trim()) {
      onRenameConfig(configId, editingName.trim());
      setEditingId(null);
      setEditingName('');
    }
  };

  const handleLoadDefault = (defaultConfig) => {
    const newConfig = {
      ...defaultConfig,
      id: `config-${Date.now()}`,
    };
    onCreateConfig(newConfig);
  };

  const handleExport = (config) => {
    const dataStr = JSON.stringify(config, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${config.name.replace(/\s+/g, '-')}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          try {
            const config = JSON.parse(event.target.result);
            config.id = `config-${Date.now()}`;
            onImportConfig(config);
          } catch (err) {
            alert('Failed to import config: Invalid JSON');
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-hidden">
      <div className="bg-gray-900 border border-cyan-500/30 rounded-2xl max-w-2xl w-full max-h-[90vh] flex flex-col shadow-2xl shadow-cyan-500/20">
        <div className="flex items-center justify-between p-6 border-b border-cyan-500/30 bg-linear-to-r from-gray-900 to-slate-900">
          <h2 className="text-2xl font-bold text-cyan-300">Controller Configurations</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl transition-colors"
          >
            ×
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-cyan-300 mb-3">My Controllers</h3>
            <div className="space-y-2">
              {configs.map((config) => (
                <div
                  key={config.id}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    activeConfigId === config.id
                      ? 'border-cyan-500 bg-cyan-500/10'
                      : 'border-cyan-500/20 bg-slate-800/30 hover:border-cyan-500/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    {editingId === config.id ? (
                      <input
                        type="text"
                        value={editingName}
                        onChange={(e) => setEditingName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleRename(config.id);
                          if (e.key === 'Escape') setEditingId(null);
                        }}
                        className="flex-1 px-2 py-1 bg-slate-800 border border-cyan-500/50 rounded text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        autoFocus
                      />
                    ) : (
                      <div className="flex-1">
                        <h4 className="font-medium text-white">{config.name}</h4>
                        <p className="text-sm text-gray-400">{config.buttons.length} buttons</p>
                      </div>
                    )}
                    
                    <div className="flex gap-2">
                      {activeConfigId !== config.id && (
                        <button
                          onClick={() => onSelectConfig(config.id)}
                          className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-sm transition-all font-medium"
                        >
                          Load
                        </button>
                      )}
                      
                      <button
                        onClick={() => {
                          setEditingId(config.id);
                          setEditingName(config.name);
                        }}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm transition-all font-medium"
                      >
                        Rename
                      </button>
                      
                      <button
                        onClick={() => onDuplicateConfig(config.id)}
                        className="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white rounded text-sm transition-all font-medium"
                      >
                        Duplicate
                      </button>
                      
                      <button
                        onClick={() => handleExport(config)}
                        className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-all font-medium"
                      >
                        Export
                      </button>
                      
                      <button
                        onClick={() => {
                          if (confirm(`Delete "${config.name}"?`)) {
                            onDeleteConfig(config.id);
                          }
                        }}
                        className="px-3 py-1 bg-red-600 hover:bg-red-500 text-white rounded text-sm transition-all font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
              
              {configs.length === 0 && (
                <p className="text-gray-400 text-center py-8 text-sm">
                  No custom controllers yet. Create one or load a default!
                </p>
              )}
            </div>
          </div>
          
          <div className="border-t border-cyan-500/30 pt-6">
            {isCreating ? (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newConfigName}
                  onChange={(e) => setNewConfigName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleCreate();
                    if (e.key === 'Escape') setIsCreating(false);
                  }}
                  placeholder="Controller name..."
                  className="flex-1 px-4 py-2 bg-gamepad-background border border-gamepad-border rounded text-white"
                  autoFocus
                />
                <button
                  onClick={handleCreate}
                  className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                >
                  Create
                </button>
                <button
                  onClick={() => setIsCreating(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={() => setIsCreating(true)}
                  className="flex-1 px-4 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 font-medium"
                >
                  + Create New Controller
                </button>
                <button
                  onClick={handleImport}
                  className="px-4 py-3 bg-gamepad-secondary text-white rounded-lg hover:opacity-80 font-medium"
                >
                  Import JSON
                </button>
              </div>
            )}
          </div>
          
          <div className="border-t border-gamepad-border pt-6">
            <h3 className="text-lg font-semibold mb-3">Default Templates</h3>
            <div className="space-y-2">
              {DEFAULT_CONFIGS.map((config) => (
                <div
                  key={config.id}
                  className="p-4 rounded-lg border border-gamepad-border bg-gamepad-background"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">{config.name}</h4>
                      <p className="text-sm text-gray-400">{config.buttons.length} buttons</p>
                    </div>
                    <button
                      onClick={() => handleLoadDefault(config)}
                      className="px-4 py-2 bg-(--color-gamepad-primary) text-white rounded hover:opacity-80"
                    >
                      Load Template
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfigMenu;
