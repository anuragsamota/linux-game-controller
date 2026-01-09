const STORAGE_KEY = 'gamepad_configs';
const ACTIVE_CONFIG_KEY = 'active_config';

export const storage = {
  getConfigs() {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Failed to load configs:', error);
      return [];
    }
  },

  saveConfigs(configs) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(configs));
    } catch (error) {
      console.error('Failed to save configs:', error);
    }
  },

  getActiveConfigId() {
    return localStorage.getItem(ACTIVE_CONFIG_KEY);
  },

  setActiveConfigId(id) {
    localStorage.setItem(ACTIVE_CONFIG_KEY, id);
  },

  clear() {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(ACTIVE_CONFIG_KEY);
  }
};
