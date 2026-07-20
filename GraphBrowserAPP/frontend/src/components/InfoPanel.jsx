import styles from './InfoPanel.module.css'

const LANG_NAMES = { EN: 'English', ES: 'Spanish' }

function relationLabel(rel) {
  if (rel === 'hub') return 'shares a headword with'
  if (rel === 'translation') return 'translates to'
  return rel.replace(/_/g, ' ')
}

export default function InfoPanel({ node, connections, onSelectNode }) {
  if (!node) {
    return (
      <div className={styles.panel}>
        <p className={styles.empty}>Click a node in the graph to see its details.</p>
      </div>
    )
  }

  return (
    <div className={styles.panel}>
      <div className={styles.headerRow}>
        <span className={`${styles.badge} ${styles[node.type] || ''}`}>
          {node.type === 'hub' ? 'headword' : 'concept'}
        </span>
        {node.lang && (
          <span className={styles.lang}>{LANG_NAMES[node.lang] || node.lang}</span>
        )}
      </div>

      <h2 className={styles.label}>{node.label}</h2>

      <div className={styles.connections}>
        <h3 className={styles.connTitle}>
          Connections {connections.length ? `(${connections.length})` : ''}
        </h3>
        {connections.length === 0 && (
          <p className={styles.empty}>No connections in the current view.</p>
        )}
        <ul className={styles.connList}>
          {connections.map(({ edge, node: other }, i) => (
            <li
              key={`${other.id}-${i}`}
              className={styles.connItem}
              onClick={() => onSelectNode(other.id)}
            >
              <span className={styles.connRelation}>{relationLabel(edge.relation)}</span>
              <span className={styles.connTarget}>{other.label}</span>
              {other.lang && <span className={styles.connLang}>{other.lang}</span>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
