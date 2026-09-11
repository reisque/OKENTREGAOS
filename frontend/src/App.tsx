import { useEffect, useMemo, useState } from 'react'
import { FileCode2, RefreshCw, Search } from 'lucide-react'

type Result = { input: string; normalized: string; os_number?: string; status?: string; booking?: string; container?: string; contractor?: string; depot?: string; has_xml: boolean; found: boolean; message?: string }
type SyncResponse = { results: Result[]; consulted_at: string; year: number }
const apiUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? 'http://localhost:8000'
const normalizedOs = (value: string) => value.replace(/\s+/g, '').toUpperCase()
const normalizedContainer = (value?: string) => value?.replace(/[^a-zA-Z0-9]/g, '').toUpperCase() || '—'
const formatDate = (value: string) => new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))

export default function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Result[]>([])
  const [loading, setLoading] = useState(false)
  const [consultedAt, setConsultedAt] = useState('')
  const [error, setError] = useState('')

  async function sync() {
    setLoading(true); setError('')
    try {
      const response = await fetch(`${apiUrl}/api/consultations/sync`, { method: 'POST' })
      const body: SyncResponse & { detail?: string } = await response.json()
      if (!response.ok) throw new Error(body.detail ?? 'Não foi possível consultar as OS.')
      setResults((body as SyncResponse).results)
      setConsultedAt((body as SyncResponse).consulted_at)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Erro inesperado.') }
    finally { setLoading(false) }
  }

  useEffect(() => {
    void sync()
  }, [])
  useEffect(() => {
    if (!consultedAt) return
    const timer = window.setTimeout(() => void sync(), 60 * 60 * 1000)
    return () => window.clearTimeout(timer)
  }, [consultedAt])

  function download(os: string) { window.open(`${apiUrl}/api/os/${encodeURIComponent(normalizedOs(os))}/xml`, '_blank', 'noopener,noreferrer') }

  const visibleResults = useMemo(() => {
    const term = query.trim().toLocaleLowerCase()
    if (!term) return results
    return results.filter(item => Object.values(item).some(value => String(value ?? '').toLocaleLowerCase().includes(term)))
  }, [query, results])
  const foundCount = visibleResults.filter(item => item.found).length

  return <main className="page">
    <section className="hero"><h1>Consulta de ordem de serviço</h1><p>Sincronização anual automática e gratuita</p></section>
    <section className="panel"><div className="sync-bar"><span>{consultedAt ? `Última consulta: ${formatDate(consultedAt)}` : 'Aguardando a primeira consulta...'}</span><button type="button" onClick={() => void sync()} disabled={loading}><RefreshCw size={16} className={loading ? 'spin' : ''} />{loading ? 'Atualizando...' : 'Atualizar consulta'}</button></div><label htmlFor="search">Pesquisar nos resultados</label><div className="query"><div className="search-input"><Search size={18} /><input id="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Pesquise OS, status, booking, contêiner, contratante ou depot" /></div></div>{error && <div className="error">{error}</div>}</section>
    {consultedAt && <section className="results"><div className="results-head"><div><h2>Resultado da consulta</h2><span>{foundCount} encontrada(s) de {visibleResults.length} exibida(s)</span></div></div>{!results.length ? <p className="empty">Nenhuma OS foi retornada pelo portal para o ano de {new Date(consultedAt).getFullYear()}.</p> : <div className="table-scroll"><table><thead><tr><th>Ordem de serviço</th><th>Status</th><th>Booking</th><th>Contêiner</th><th>Contratante</th><th>Depot</th><th>XML</th></tr></thead><tbody>{visibleResults.map((item, index) => item.found
      ? <tr key={`${item.normalized}-${index}`}><td className="os-cell" title={item.os_number}>{item.os_number}</td><td><span className="status" title={item.status}>{item.status}</span></td><td title={item.booking}>{item.booking || '—'}</td><td>{normalizedContainer(item.container)}</td><td title={item.contractor}>{item.contractor || '—'}</td><td title={item.depot}>{item.depot || '—'}</td><td><div className="actions"><button type="button" className={item.has_xml ? '' : 'na'} disabled={!item.has_xml} onClick={() => item.has_xml && download(item.os_number!)}>{item.has_xml ? <><FileCode2 size={15} /> Baixar XML</> : 'N/A'}</button></div></td></tr>
      : <tr key={`${item.normalized}-${index}`} className="not-found"><td className="os-cell">{item.normalized}</td><td colSpan={6}>{item.message}</td></tr>
    )}</tbody></table></div>}</section>}
  </main>
}
