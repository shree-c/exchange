import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL
})

function newAbortSignal(timeoutMs: number) {
  const abortController = new AbortController()
  setTimeout(() => abortController.abort(), timeoutMs || 0)
  return abortController.signal
}

client.interceptors.request.use(async (config): Promise<any> => {
  config.headers.set('ngrok-skip-browser-warning', 'true')
  config.signal = newAbortSignal(60000)
  return config
})

export { client }