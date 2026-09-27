const BADGE_STYLES: Record<string, string> = {
  pending: 'bg-amber text-steel',
  approved: 'bg-verdict-great text-paper',
  rejected: 'bg-verdict-bad text-paper',
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold capitalize ${BADGE_STYLES[status] ?? 'bg-ink-400 text-paper'}`}>
      {status}
    </span>
  );
}
