import axios, { AxiosInstance } from 'axios'

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      headers: {
        'Content-Type': 'application/json',
      },
    })
  }

  async crossMatch(materialName: string, topN: number = 10) {
    const response = await this.client.post('/chat/cross-match', {
      material_name: materialName,
      top_n: topN,
      include_details: true,
    })
    return response.data
  }

  async chatQuery(message: string, queryType: string = 'cross_match') {
    const response = await this.client.post('/chat/query', {
      message,
      query_type: queryType,
    })
    return response.data
  }

  async getConfig() {
    const response = await this.client.get('/config')
    return response.data
  }

  async getHealth() {
    const response = await this.client.get('/health')
    return response.data
  }
}

export const apiClient = new APIClient()