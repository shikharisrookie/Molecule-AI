export default function LoadingSpinner({ text = 'Analyzing molecule...' }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12">
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 rounded-full border-4 border-surface-200 dark:border-surface-700" />
        <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-primary-500 animate-spin" />
        <div className="absolute inset-2 rounded-full border-4 border-transparent border-t-accent-500 animate-spin-slow" style={{ animationDirection: 'reverse' }} />
      </div>
      <p className="text-sm font-medium text-surface-500 dark:text-surface-400 animate-pulse">{text}</p>
    </div>
  );
}
