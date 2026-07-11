export default function AudioPlayer({ audioUrl }) {
  if (!audioUrl) return null
  return <audio controls src={audioUrl} />
}

