const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const MOCK_AUDIO_DATA_URI =
  'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA='

export function resolveAudioUrl(audioUrl) {
  if (!audioUrl) return null
  if (audioUrl.startsWith('http') || audioUrl.startsWith('data:') || audioUrl.startsWith('blob:')) {
    return audioUrl
  }
  return `${API_BASE}${audioUrl}`
}
