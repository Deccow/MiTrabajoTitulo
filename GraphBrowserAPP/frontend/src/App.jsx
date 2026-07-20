import { useState, useCallback } from 'react'
import SearchPanel from './components/SearchPanel'
import GraphCanvas from './components/GraphCanvas'
import InfoPanel from './components/InfoPanel'
import styles from './App.module.css'

export default function App() {
  const [data, setData] = useState(null)       // { nodes, edges, seeds, total_nodes, total_edges }
  const [selectedNode, setSelectedNode] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastQuery, setLastQuery] = useState(null)

  const handleSearch = useCallback(async (word, hops, language, mode, source) => {
    setLoading(true)
    setError(null)
    setSelectedNode(null)
    setLastQuery({ word, hops, language, mode, source })

    try {
      const params = new URLSearchParams({ word, hops: String(hops), language, mode, source })
      const res = await fetch(`/api/search?${params.toString()}`)
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.error || `Search failed (${res.status})`)
      }
      const json = await res.json()
      setData(json)
      if (json.nodes.length === 0) {
        setError(json.message || `No results for "${word}"`)
      }
    } catch (err) {
      setError(err.message || 'Something went wrong')
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node)
  }, [])

  // Connections for the currently selected node, derived from the loaded subgraph
  const connections = selectedNode && data
    ? data.edges
        .filter(e => e.source === selectedNode.id || e.target === selectedNode.id)
        .map(e => {
          const otherId = e.source === selectedNode.id ? e.target : e.source
          const otherNode = data.nodes.find(n => n.id === otherId)
          return { edge: e, node: otherNode }
        })
        .filter(c => c.node)
    : []

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <h1 className={styles.title}>WordGraph Explorer</h1>
        <p className={styles.subtitle}>Interactive lexical network visualizer</p>
      </header>

      <div className={styles.body}>
        <aside className={styles.sidebar}>
          <SearchPanel onSearch={handleSearch} loading={loading} />

          {error && <div className={styles.error}>{error}</div>}

          {data && !error && (
            <div className={styles.summary}>
              {data.total_nodes} nodes · {data.total_edges} edges
            </div>
          )}

          <InfoPanel
            node={selectedNode}
            connections={connections}
            onSelectNode={(id) => {
              const n = data?.nodes.find(n => n.id === id)
              if (n) setSelectedNode(n)
            }}
          />
        </aside>

        <main className={styles.canvasArea}>
          {data ? (
            <GraphCanvas
              data={data}
              onNodeClick={handleNodeClick}
              selectedNode={selectedNode}
            />
          ) : (
            <div className={styles.placeholder}>
              {loading ? 'Loading graph…' : 'Search a word to explore its network'}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
