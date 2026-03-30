import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AutoValu — اعرف قيمة سيارتك',
  description: 'تحقق من سعر السيارة في السوق التونسي قبل ما تشري أو تبيع. مدعوم بالذكاء الاصطناعي.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" dir="ltr">
      <body style={{ margin: 0, padding: 0 }}>{children}</body>
    </html>
  );
}