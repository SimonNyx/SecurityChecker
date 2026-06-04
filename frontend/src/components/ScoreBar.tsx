const colour = (score: number) =>
  score >= 7.5 ? 'bg-green-500' : score >= 5 ? 'bg-amber-400' : 'bg-red-500'

export default function ScoreBar({ score }: { score: number | null | undefined }) {
  if (score == null) return <span className="text-sm text-gray-400">—</span>
  const pct = Math.min(100, Math.max(0, (score / 10) * 100))
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-2 rounded-full ${colour(score)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm font-semibold text-gray-700 w-10 text-right">
        {score.toFixed(1)}
      </span>
    </div>
  )
}
