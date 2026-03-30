import styles from './Footer.module.css';

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.brand}>
          <div className={styles.brandName}><span>Auto</span>Valu</div>
          <p className={styles.brandDesc}>
            AI-powered used car price intelligence for the Tunisian market.
            Trained on thousands of real local listings.
          </p>
        </div>

        <div className={styles.links}>
          <div className={styles.linkGroup}>
            <div className={styles.linkGroupTitle}>Product</div>
            <a href="/check" className={styles.link}>Check a price</a>
            <a href="/check" className={styles.link}>Seller mode</a>
          </div>
          <div className={styles.linkGroup}>
            <div className={styles.linkGroupTitle}>Developer</div>
            <a href="https://www.linkedin.com/in/safwen-ben-mabrouk-494721362/"
              target="_blank" rel="noopener noreferrer" className={styles.link}>LinkedIn</a>
            <a href="https://github.com/Safwen-bm"
              target="_blank" rel="noopener noreferrer" className={styles.link}>GitHub</a>
          </div>
        </div>
      </div>

      <div className={styles.bottom}>
        <span>Built by <a href="https://www.linkedin.com/in/safwen-ben-mabrouk-494721362/"
          target="_blank" rel="noopener noreferrer">Safwen Ben Mabrouk</a></span>
        <span>AutoValu Tunisia · 2026</span>
        <span>Prices are AI estimates based on market data</span>
      </div>
    </footer>
  );
}