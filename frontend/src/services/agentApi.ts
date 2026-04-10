import axios from 'axios'

const API_URL = import.meta.env.VITE_AGENT_URL || 'https://agent-production-065e.up.railway.app'

export interface Source {
  url: string
  title: string
  category: string
  relevance_score: number
}

export interface ChatResponse {
  conversation_id: string
  response: string
  sources: Source[]
}

export interface ChatRequest {
  query: string
  conversation_id?: string
}

export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await axios.post<ChatResponse>(`${API_URL}/chat`, request)
  return response.data
}
