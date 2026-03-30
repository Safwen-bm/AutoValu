'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import styles from './Header.module.css';

export default function Header() {
  const path = usePathname();

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <Link href="/" className={styles.logo}>
          <div className={styles.logoIcon}>🚗</div>
          <span><span className={styles.logoAccent}>Auto</span>Valu</span>
        </Link>

        <nav className={styles.nav}>
          <Link href="/"       className={`${styles.navLink} ${path==='/'?styles.active:''}`}>Home</Link>
          <Link href="/check"  className={`${styles.navLink} ${path==='/check'?styles.active:''}`}>Check a price</Link>
        </nav>

        <Link href="/check" className={styles.ctaBtn}>
          Check a price →
        </Link>
      </div>
    </header>
  );
}