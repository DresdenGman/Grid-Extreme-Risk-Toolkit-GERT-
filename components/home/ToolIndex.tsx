import Link from 'next/link';
import { toolIndex } from '@/lib/homepage/tools';
import styles from './home.module.css';

export function ToolIndex() {
  return (
    <section id="tools" className={styles.index} aria-labelledby="tools-heading">
      <h2 id="tools-heading" className={styles.indexTitle}>Contents</h2>
      <p className={styles.indexDek}>The other pages. Each line is a route that already exists.</p>
      {toolIndex.map((group) => (
        <div key={group.id} className={styles.group}>
          <h3 className={styles.groupLabel}>{group.label}</h3>
          <ul className={styles.entryList}>
            {group.entries.map((entry) => (
              <li key={entry.href}>
                <Link href={entry.href} className={styles.entry}>
                  <span className={styles.entryName}>{entry.name}</span>
                  <span className={styles.entryDesc}>{entry.description}</span>
                  <span className={styles.entryPath}>{entry.href}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}
