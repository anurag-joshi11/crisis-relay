import { resolveAudioUrl } from '../audioUrl'

export default function AudioPlayer({ audioUrl }) {
  const resolvedAudioUrl = resolveAudioUrl(audioUrl)
  if (!resolvedAudioUrl) return null
  return <audio controls src={resolvedAudioUrl} />
}

