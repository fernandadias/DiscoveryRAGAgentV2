import axios from 'axios';

// API base URL - será substituído pelo URL real em produção
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Cliente Axios configurado
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Serviço de consulta
export const queryService = {
  // Enviar consulta ao backend
  async sendQuery(query, objective = 'informative') {
    try {
      const response = await apiClient.post('/query', {
        query,
        objective,
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao enviar consulta:', error);
      throw error;
    }
  },

  // Iniciar simulação de fluxo
  async startFlowSimulation(query, objective = 'informative') {
    try {
      const response = await apiClient.post('/flow/start', {
        query,
        objective,
      });
      return response.data;
    } catch (error) {
      console.error('Erro ao iniciar simulação de fluxo:', error);
      throw error;
    }
  },

  // Obter status da simulação de fluxo
  async getFlowStatus(simulationId) {
    try {
      const response = await apiClient.get(`/flow/${simulationId}`);
      return response.data;
    } catch (error) {
      console.error('Erro ao obter status do fluxo:', error);
      throw error;
    }
  },
};

// Serviço de saúde da API
export const healthService = {
  // Verificar status da API
  async checkHealth() {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('Erro ao verificar saúde da API:', error);
      throw error;
    }
  },
};

export default {
  query: queryService,
  health: healthService,
};
