export default function Logomark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <path d="M5.6 22a12 12 0 1 1 20.8 0" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" opacity="0.3" />
      <path d="M8.3 24.6a12 12 0 0 0 15.4 0" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="16" y1="6" x2="16" y2="8.6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
      <line x1="6.4" y1="12" x2="8.5" y2="13.4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
      <line x1="25.6" y1="12" x2="23.5" y2="13.4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
      <line x1="16" y1="16" x2="21.4" y2="9.6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="16" cy="16" r="2.2" fill="currentColor" />
    </svg>
  );
}