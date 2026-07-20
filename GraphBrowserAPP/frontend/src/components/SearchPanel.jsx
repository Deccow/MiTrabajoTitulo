import { useState, useEffect, useRef } from 'react'
import styles from './SearchPanel.module.css'

const LANGUAGES = [
  { code: 'EN', label: 'English' },
  { code: 'ES', label: 'Spanish' },
  { code: 'null', label: 'Both' },
]

const MODES = [
  { code: 'words', label: 'Words only' },
  { code: 'all', label: 'All' },
]

const SOURCES = [
  { code: 'local', label: 'Local Database' },
  { code: 'api', label: 'API Database' },
]

export default function SearchPanel({ onSearch, loading }) {
  const [word, setWord] = useState('')
  const [hops, setHops] = useState(2)
  const [language, setLanguage] = useState('EN')
  const [mode, setMode] = useState('words')
  const [source, setSource] = useState('local')
  const [suggestions, setSuggestions] = useState([])
  const [allWords, setAllWords] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    fetch(`/api/words?language=${language}&mode=${mode}&source=${source}`)
      .then(r => r.json())
      .then(setAllWords)
      .catch(() => {})
  }, [language, mode, source])

  const handleInput = (val) => {
    setWord(val)
    if (val.length >= 1) {
      const matches = allWords
        .filter(w => w.toLowerCase().startsWith(val.toLowerCase()))
        .slice(0, 8)
      setSuggestions(matches)
      setShowSuggestions(matches.length > 0)
    } else {
      setShowSuggestions(false)
    }
  }

  const submit = (w) => {
    const target = w ?? word
    setShowSuggestions(false)
    if (target.trim()) onSearch(target.trim(), hops, language, mode, source)
  }

  const pickSuggestion = (w) => {
    setWord(w)
    setShowSuggestions(false)
    onSearch(w, hops, language, mode, source)
  }

  return (
    <div className={styles.panel}>
      <div className={styles.inputWrap}>
        <input
          ref={inputRef}
          className={styles.input}
          type="text"
          placeholder="Type a word…"
          value={word}
          onChange={e => handleInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter') submit()
            if (e.key === 'Escape') setShowSuggestions(false)
          }}
          onFocus={() => suggestions.length && setShowSuggestions(true)}
          disabled={loading}
          autoComplete="off"
          spellCheck="false"
        />
        {showSuggestions && (
          <ul className={styles.suggestions}>
            {suggestions.map(s => (
              <li
                key={s}
                className={styles.suggestion}
                onMouseDown={() => pickSuggestion(s)}
              >
                {s}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className={styles.hopsRow}>
        <label className={styles.hopsLabel}>Source:</label>
        <select
          className={styles.select}
          value={source}
          onChange={e => setSource(e.target.value)}
          disabled={loading}
        >
          {SOURCES.map(s => (
            <option key={s.code} value={s.code}>{s.label}</option>
          ))}
        </select>
      </div>

      <div className={styles.hopsRow}>
        <label className={styles.hopsLabel}>Language:</label>
        <select
          className={styles.select}
          value={language}
          onChange={e => setLanguage(e.target.value)}
          disabled={loading}
        >
          {LANGUAGES.map(l => (
            <option key={l.code} value={l.code}>{l.label}</option>
          ))}
        </select>
      </div>

      <div className={styles.hopsRow}>
        <label className={styles.hopsLabel}>Mode:</label>
        <select
          className={styles.select}
          value={mode}
          onChange={e => setMode(e.target.value)}
          disabled={loading}
        >
          {MODES.map(m => (
            <option key={m.code} value={m.code}>{m.label}</option>
          ))}
        </select>
      </div>

      <div className={styles.hopsRow}>
        <label className={styles.hopsLabel}>
          Hops: <span className={styles.hopsVal}>{hops}</span>
        </label>
        <input
          type="range"
          min={1}
          max={5}
          value={hops}
          onChange={e => setHops(Number(e.target.value))}
          className={styles.slider}
          disabled={loading}
        />
        <div className={styles.hopsTicks}>
          {[1,2,3,4,5].map(n => (
            <span key={n} className={n === hops ? styles.tickActive : styles.tick}>{n}</span>
          ))}
        </div>
      </div>

      <button
        className={styles.btn}
        onClick={() => submit()}
        disabled={loading || !word.trim()}
      >
        {loading ? 'Searching…' : 'Explore'}
      </button>
    </div>
  )
}