import { useEffect, useMemo, useState } from 'react'
import { FileCode2, RefreshCw, Search } from 'lucide-react'

type Result = { input: string; normalized: string; os_number?: string; status?: string; booking?: string; container?: string; contractor?: string; depot?: string; integration_date?: string; cte_detected_at?: string; has_xml: boolean; found: boolean; message?: string }
type SyncResponse = { results: Result[]; consulted_at: string; year: number }
const apiUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? 'http://localhost:8000'
const normalizedOs = (value: string) => value.replace(/\s+/g, '').toUpperCase()
const normalizedContainer = (value?: string) => value?.replace(/[^a-zA-Z0-9]/g, '').toUpperCase() || '—'
const formatDate = (value: string) => {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(date)
}

export default function App() {
  const [query, setQuery] = useState('')
  const [batchQuery, setBatchQuery] = useState('')
  const [batchFilter, setBatchFilter] = useState<string[]>([])
  const [integrationStart, setIntegrationStart] = useState('')
  const [integrationEnd, setIntegrationEnd] = useState('')
  const [cteStart, setCteStart] = useState('')
  const [cteEnd, setCteEnd] = useState('')
  const [page, setPage] = useState(1)
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
      setPage(1)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Erro inesperado.') }
    finally { setLoading(false) }
  }

  async function loadLatest() {
    setLoading(true); setError('')
    try {
      const response = await fetch(`${apiUrl}/api/consultations/latest`)
      if (response.status === 404) {
        await sync()
        return
      }
      const body: SyncResponse & { detail?: string } = await response.json()
      if (!response.ok) throw new Error(body.detail ?? 'Não foi possível carregar a consulta salva.')
      setResults(body.results)
      setConsultedAt(body.consulted_at)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Erro inesperado.') }
    finally { setLoading(false) }
  }

  useEffect(() => {
    void loadLatest()
  }, [])
  useEffect(() => {
    if (!consultedAt) return
    const elapsed = Date.now() - new Date(consultedAt).getTime()
    const remaining = Math.max(0, 30 * 60 * 1000 - elapsed)
    const timer = window.setTimeout(() => void sync(), remaining)
    return () => window.clearTimeout(timer)
  }, [consultedAt])

  function download(os: string) { window.open(`${apiUrl}/api/os/${encodeURIComponent(normalizedOs(os))}/xml`, '_blank', 'noopener,noreferrer') }

  function applyBatchFilter() {
    setBatchFilter(batchQuery.split(/\r?\n/).map(line => line.trim()).filter(line => normalizedOs(line).startsWith('6SP')))
    setPage(1)
  }

  function clearBatchFilter() {
    setBatchQuery('')
    setBatchFilter([])
    setPage(1)
  }

  function clearDateFilters() {
    setIntegrationStart('')
    setIntegrationEnd('')
    setCteStart('')
    setCteEnd('')
  }

  const visibleResults = useMemo(() => {
    const requestedResults = batchFilter.length
      ? batchFilter.map(input => results.find(item => item.normalized === normalizedOs(input)) ?? {
        input,
        normalized: normalizedOs(input),
        found: false,
        has_xml: false,
        message: 'OS não encontrada na consulta anual.',
      })
      : results
    const inDateRange = (value: string | undefined, start: string, end: string) => {
      if (!start && !end) return true
      if (!value) return false
      const date = new Date(value).getTime()
      if (Number.isNaN(date)) return false
      return (!start || date >= new Date(`${start}T00:00:00`).getTime())
        && (!end || date <= new Date(`${end}T23:59:59.999`).getTime())
    }
    const term = query.trim().toLocaleLowerCase()
    return requestedResults.filter(item => inDateRange(item.integration_date, integrationStart, integrationEnd)
      && inDateRange(item.cte_detected_at, cteStart, cteEnd)
      && (!term || Object.values(item).some(value => String(value ?? '').toLocaleLowerCase().includes(term))))
  }, [batchFilter, cteEnd, cteStart, integrationEnd, integrationStart, query, results])
  const pageSize = 100
  const pageCount = Math.max(1, Math.ceil(visibleResults.length / pageSize))
  const pageResults = visibleResults.slice((page - 1) * pageSize, page * pageSize)
  const foundCount = visibleResults.filter(item => item.found).length

  return <main className="page">
    <section className="hero"><h1>Consulta de ordem de serviço</h1></section>
    <section className="panel"><div className="sync-bar"><span>{consultedAt ? `Última consulta: ${formatDate(consultedAt)}` : 'Aguardando a primeira consulta...'}</span><button type="button" onClick={() => void sync()} disabled={loading}><RefreshCw size={16} className={loading ? 'spin' : ''} />{loading ? 'Atualizando...' : 'Atualizar consulta'}</button></div><label htmlFor="batch-search">Filtrar várias OS de uma vez</label><div className="batch-query"><textarea id="batch-search" value={batchQuery} onChange={event => setBatchQuery(event.target.value)} placeholder={'Cole uma OS por linha, por exemplo:\n6SP 558788B\n6PE 413251B'} rows={4} /><div className="batch-actions"><button type="button" onClick={applyBatchFilter} disabled={!batchQuery.trim()}>Filtrar OS</button>{batchFilter.length > 0 && <button type="button" className="secondary" onClick={clearBatchFilter}>Limpar filtro</button>}</div></div><div className="date-filters"><div><label htmlFor="integration-start">Integração da OS: início</label><input id="integration-start" type="date" value={integrationStart} onChange={event => { setIntegrationStart(event.target.value); setPage(1) }} /></div><div><label htmlFor="integration-end">Integração da OS: fim</label><input id="integration-end" type="date" value={integrationEnd} onChange={event => { setIntegrationEnd(event.target.value); setPage(1) }} /></div><div><label htmlFor="cte-start">Detecção do CTE: início</label><input id="cte-start" type="date" value={cteStart} onChange={event => { setCteStart(event.target.value); setPage(1) }} /></div><div><label htmlFor="cte-end">Detecção do CTE: fim</label><input id="cte-end" type="date" value={cteEnd} onChange={event => { setCteEnd(event.target.value); setPage(1) }} /></div><button type="button" className="clear-date-filters" onClick={() => { clearDateFilters(); setPage(1) }} disabled={!integrationStart && !integrationEnd && !cteStart && !cteEnd}>Limpar datas</button></div><label htmlFor="search">Pesquisar nos resultados</label><div className="query"><div className="search-input"><Search size={18} /><input id="search" value={query} onChange={event => { setQuery(event.target.value); setPage(1) }} placeholder="Pesquise OS, status, booking, contêiner, contratante ou depot" /></div></div>{error && <div className="error">{error}</div>}</section>
    {consultedAt && <section className="results"><div className="results-head"><div><h2>Resultado da consulta</h2><span>{foundCount} encontrada(s) de {visibleResults.length} exibida(s)</span></div></div>{!results.length ? <p className="empty">Nenhuma OS foi retornada pelo portal para o ano de {new Date(consultedAt).getFullYear()}.</p> : <><div className="table-scroll"><table><thead><tr><th>Ordem de serviço</th><th>Data integração</th><th>Status</th><th>Data do CTE</th><th>Booking</th><th>Contêiner</th><th>Contratante</th><th>Depot</th><th>XML</th></tr></thead><tbody>{pageResults.map((item, index) => item.found
      ? <tr key={`${item.normalized}-${index}`}><td className="os-cell" title={item.os_number}>{item.os_number}</td><td className="date-cell">{item.integration_date ? formatDate(item.integration_date) : '—'}</td><td><span className="status" title={item.status}>{item.status}</span></td><td className="date-cell">{item.cte_detected_at ? formatDate(item.cte_detected_at) : '—'}</td><td title={item.booking}>{item.booking || '—'}</td><td>{normalizedContainer(item.container)}</td><td title={item.contractor}>{item.contractor || '—'}</td><td title={item.depot}>{item.depot || '—'}</td><td><div className="actions"><button type="button" className={item.has_xml ? '' : 'na'} disabled={!item.has_xml} onClick={() => item.has_xml && download(item.os_number!)}>{item.has_xml ? <><FileCode2 size={15} /> Baixar XML</> : 'N/A'}</button></div></td></tr>
      : <tr key={`${item.normalized}-${index}`} className="not-found"><td className="os-cell">{item.normalized}</td><td colSpan={6}>{item.message}</td></tr>
    )}</tbody></table></div><div className="pagination"><button type="button" onClick={() => setPage(current => Math.max(1, current - 1))} disabled={page === 1}>Anterior</button><span>Página {page} de {pageCount}</span><button type="button" onClick={() => setPage(current => Math.min(pageCount, current + 1))} disabled={page >= pageCount}>Próxima</button></div></>}</section>}
  </main>
}
