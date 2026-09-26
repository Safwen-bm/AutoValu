import Link from 'next/link';
import Logomark from './Logomark';

export default function Footer() {
  return (
    <footer className="bg-steel text-surface-alt">
      <div className="mx-auto grid max-w-6xl gap-10 px-6 py-14 sm:grid-cols-[1.5fr_1fr]">
        <div className="max-w-sm">
          <div className="flex items-center gap-2 font-display text-lg font-bold uppercase tracking-tight text-paper">
            <Logomark className="h-6 w-6 text-amber" />
            <span>Auto<span className="text-amber">Valu</span></span>
          </div>
          <p className="mt-3 text-sm leading-relaxed">
            Used-car price estimates for Tunisia, built from real local listings not global averages.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-8">
          <div>
            <div className="text-sm font-medium text-paper">Product</div>
            <div className="mt-3 flex flex-col gap-2">
              <Link href="/check" className="text-sm transition-colors hover:text-paper">Check a price</Link>
              <Link href="/check" className="text-sm transition-colors hover:text-paper">Seller mode</Link>
            </div>
          </div>
          <div>
            <div className="text-sm font-medium text-paper">Developer</div>
            <div className="mt-3 flex flex-col gap-2">
              <a href="https://www.linkedin.com/in/safwen-ben-mabrouk-494721362/" target="_blank" rel="noopener noreferrer" className="text-sm transition-colors hover:text-paper">LinkedIn</a>
              <a href="https://github.com/Safwen-bm" target="_blank" rel="noopener noreferrer" className="text-sm transition-colors hover:text-paper">GitHub</a>
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-6 py-5 text-xs sm:flex-row sm:items-center sm:justify-between">
          <span>Built by <a href="https://www.linkedin.com/in/safwen-ben-mabrouk-494721362/" target="_blank" rel="noopener noreferrer" className="text-paper hover:text-amber">Safwen Ben Mabrouk</a></span>
          <span>Tunisia, 2026</span>
          <span>Estimates are modeled, not guaranteed</span>
        </div>
      </div>
    </footer>
  );
}