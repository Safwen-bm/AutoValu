'use client';

import Link from 'next/link';
import Logomark from './Logomark';

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-steel">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2 font-display text-xl font-bold uppercase tracking-tight text-paper">
          <Logomark className="h-6 w-6 text-amber" />
          <span>Auto<span className="text-amber">Valu</span></span>
        </Link>

        <nav className="hidden sm:flex items-center gap-8">
          <Link href="/#how-it-works" className="text-sm text-surface-alt transition-colors hover:text-paper">
            How it works
          </Link>
          <Link href="/#under-the-hood" className="text-sm text-surface-alt transition-colors hover:text-paper">
            The model
          </Link>
        </nav>

        <Link
          href="/check"
          className="rounded bg-amber px-4 py-2 text-sm font-medium text-steel transition-colors hover:bg-amber-hover hover:text-paper"
        >
          Check a price
        </Link>
      </div>
    </header>
  );
}