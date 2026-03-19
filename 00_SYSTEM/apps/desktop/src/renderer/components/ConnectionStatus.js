import useSocket from '../hooks/useSocket';

export default function ConnectionStatus() {
  const { isConnected, error } = useSocket();

  const isReconnecting = !isConnected && error && error.message && !error.message.includes('Failed to connect after');

  let dotColor, label;
  if (isConnected) {
    dotColor = 'bg-omega-success';
    label = 'Connected';
  } else if (isReconnecting) {
    dotColor = 'bg-amber-400 animate-pulse';
    label = 'Reconnecting\u2026';
  } else {
    dotColor = 'bg-omega-critical';
    label = 'Disconnected';
  }

  return (
    <div className="flex items-center gap-1.5 px-2 py-1 text-xs select-none">
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <span className="text-omega-muted">{label}</span>
    </div>
  );
}
