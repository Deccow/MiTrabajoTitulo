import { useEffect, useRef, useCallback } from 'react'
import * as d3 from 'd3'
import styles from './GraphCanvas.module.css'

const COLORS = {
  ES:   '#4CAF50',
  EN:   '#E84040',
  hub:  '#7c6af7',
  seed: '#f0c040',
}

function nodeColor(node, seeds) {
  if (seeds && seeds.includes(node.id)) return COLORS.seed
  if (node.type === 'hub') return COLORS.hub
  return COLORS[node.lang] || '#888'
}

function nodeRadius(node, seeds) {
  if (seeds && seeds.includes(node.id)) return 14
  if (node.type === 'hub') return 11
  return 8
}

export default function GraphCanvas({ data, onNodeClick, selectedNode }) {
  const svgRef = useRef(null)
  const simRef = useRef(null)

  const render = useCallback(() => {
    if (!data || !svgRef.current) return
    const { nodes: rawNodes, edges: rawEdges, seeds } = data

    const container = svgRef.current.parentElement
    const W = container.clientWidth
    const H = container.clientHeight

    // Clear previous
    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
      .attr('width', W)
      .attr('height', H)

    // Zoom
    const g = svg.append('g')
    svg.call(
      d3.zoom()
        .scaleExtent([0.05, 4])
        .on('zoom', e => g.attr('transform', e.transform))
    )

    // Arrow markers
    const defs = svg.append('defs')
    const markerColors = { default: '#3a4155', translation: '#888888', hub: '#3a4155' }
    Object.entries(markerColors).forEach(([key, color]) => {
      defs.append('marker')
        .attr('id', `arrow-${key}`)
        .attr('viewBox', '0 -4 8 8')
        .attr('refX', 18)
        .attr('refY', 0)
        .attr('markerWidth', 5)
        .attr('markerHeight', 5)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-4L8,0L0,4')
        .attr('fill', color)
    })

    // Copy data for simulation
    const nodes = rawNodes.map(n => ({ ...n }))
    const nodeById = Object.fromEntries(nodes.map(n => [n.id, n]))
    const edges = rawEdges
      .filter(e => nodeById[e.source] && nodeById[e.target])
      .map(e => ({ ...e, source: e.source, target: e.target }))

    // Simulation
    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges)
        .id(d => d.id)
        .distance(d => d.relation === 'hub' ? 55 : 100)
        .strength(d => d.relation === 'hub' ? 0.8 : 0.3)
      )
      .force('charge', d3.forceManyBody().strength(d => d.type === 'hub' ? -300 : -180))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide().radius(d => nodeRadius(d, seeds) + 6))

    simRef.current = sim

    // Edges
    const link = g.append('g').selectAll('line')
      .data(edges)
      .join('line')
      .attr('class', styles.edge)
      .attr('stroke', d => d.relation === 'translation' ? '#666' : '#2a3044')
      .attr('stroke-width', d => d.relation === 'translation' ? 1.5 : 1)
      .attr('stroke-dasharray', d => d.relation === 'hub' ? '3,3' : null)
      .attr('marker-end', d => {
        if (d.relation === 'hub') return null
        const key = d.relation === 'translation' ? 'translation' : 'default'
        return `url(#arrow-${key})`
      })
      .attr('opacity', d => d.relation === 'hub' ? 0.35 : 0.7)

    // Edge labels (only for translation)
    const edgeLabel = g.append('g').selectAll('text')
      .data(edges.filter(e => e.relation === 'translation'))
      .join('text')
      .attr('class', styles.edgeLabel)
      .attr('text-anchor', 'middle')
      .attr('dy', -4)
      .text(d => d.relation)

    // Node groups
    const node = g.append('g').selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', styles.nodeGroup)
      .attr('cursor', 'pointer')
      .call(
        d3.drag()
          .on('start', (event, d) => {
            if (!event.active) sim.alphaTarget(0.3).restart()
            d.fx = d.x; d.fy = d.y
          })
          .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
          .on('end', (event, d) => {
            if (!event.active) sim.alphaTarget(0)
            d.fx = null; d.fy = null
          })
      )
      .on('click', (event, d) => {
        event.stopPropagation()
        onNodeClick(d)
      })

    node.append('circle')
      .attr('r', d => nodeRadius(d, seeds))
      .attr('fill', d => nodeColor(d, seeds))
      .attr('stroke', d => seeds && seeds.includes(d.id) ? '#fff' : 'transparent')
      .attr('stroke-width', 2)
      .attr('opacity', 0.92)

    node.append('text')
      .attr('class', styles.nodeLabel)
      .attr('dy', d => nodeRadius(d, seeds) + 12)
      .attr('text-anchor', 'middle')
      .text(d => {
        const label = d.label || d.id
        return label.length > 20 ? label.slice(0, 18) + '…' : label
      })

    // Tick
    sim.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)

      edgeLabel
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2)

      node.attr('transform', d => `translate(${d.x},${d.y})`)
    })

    // Click on background deselects
    svg.on('click', () => onNodeClick(null))

    // Cleanup on next render
    return () => sim.stop()
  }, [data, onNodeClick])

  useEffect(() => {
    const cleanup = render()
    const observer = new ResizeObserver(render)
    if (svgRef.current?.parentElement) {
      observer.observe(svgRef.current.parentElement)
    }
    return () => {
      cleanup?.()
      observer.disconnect()
    }
  }, [render])

  // Highlight selected node
  useEffect(() => {
    if (!svgRef.current) return
    d3.select(svgRef.current).selectAll('circle')
      .attr('stroke', d => {
        if (selectedNode && d.id === selectedNode.id) return '#fff'
        return 'transparent'
      })
      .attr('stroke-width', d => selectedNode && d.id === selectedNode.id ? 3 : 2)
  }, [selectedNode])

  return <svg ref={svgRef} className={styles.svg} />
}
