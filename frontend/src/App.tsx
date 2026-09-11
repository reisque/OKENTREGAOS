import { useState } from 'react'
import { Download, FileCode2, FileText, Search } from 'lucide-react'

type Result = { input: string; normalized: string; os_number?: string; status?: string; booking?: string; container?: string; contractor?: string; depot?: string; found: boolean; message?: string }

const apiUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? 'http://localhost:8000'
const splitOs = (value: string) => value.split(/[\n,;]+/).map(item => item.trim()).filter(Boolean)
const normalizedOs = (value: string) => value.replace(/\s+/g, '').toUpperCase()
const normalizedContainer = (value?: string) => value?.replace(/[^a-zA-Z0-9]/g, '').toUpperCase() || '—'

export default function App() {
  const [value, setValue] = useState('')
  const [results, setResults] = useState<Result[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function consult(event: React.FormEvent) {
    event.preventDefault()
    const osNumbers = splitOs(value)
    if (!osNumbers.length) return setError('Informe ao menos uma ordem de serviço.')
    setLoading(true); setError(''); setResults([])
    try {
      const response = await fetch(`${apiUrl}/api/consultations`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ os_numbers: osNumbers }) })
      const body = await response.json()
      if (!response.ok) throw new Error(body.detail ?? 'Não foi possível consultar as OS.')
      setResults(body)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Erro inesperado.') }
    finally { setLoading(false) }
  }

  function download(os: string, type: 'xml' | 'pdf') { window.open(`${apiUrl}/api/os/${encodeURIComponent(normalizedOs(os))}/documents/${type}`, '_blank', 'noopener,noreferrer') }

  return <main className="page">
    <section className="hero"><p className="eyebrow">OK ENTREGA</p><h1>Consulta de ordem de serviço</h1></section>
    <section className="panel"><form onSubmit={consult}><label htmlFor="os">Número da OS</label><div className="query"><textarea id="os" value={value} onChange={event => setValue(event.target.value)} placeholder="Ex.: 6SP 568396C ou 6SP568396C" rows={3} /><button disabled={loading}>{loading ? 'Consultando...' : <><Search size={18} /> Consultar</>}</button></div><small>Para várias OS, separe por vírgula, ponto e vírgula ou uma por linha.</small></form>{error && <div className="error">{error}</div>}</section>
    {results.length > 0 && <section className="results"><div className="results-head"><h2>Resultado da consulta</h2><span>{results.filter(item => item.found).length} encontrada(s)</span></div><div className="table-scroll"><table><thead><tr><th>Ordem de serviço</th><th>Status</th><th>Booking</th><th>Contêiner</th><th>Contratante</th><th>Depot</th><th>Arquivos</th></tr></thead><tbody>{results.map((item, index) => item.found
      ? <tr key={`${item.normalized}-${index}`}><td className="os-cell">{item.os_number}</td><td><span className="status">{item.status}</span></td><td>{item.booking || '—'}</td><td>{normalizedContainer(item.container)}</td><td>{item.contractor || '—'}</td><td>{item.depot || '—'}</td><td><div className="actions"><button type="button" onClick={() => download(item.os_number!, 'xml')}><FileCode2 size={16} /> XML</button><button type="button" className="pdf" onClick={() => download(item.os_number!, 'pdf')}><FileText size={16} /> PDF <Download size={14} /></button></div></td></tr>
      : <tr key={`${item.normalized}-${index}`} className="not-found"><td className="os-cell">{item.normalized}</td><td colSpan={6}>{item.message}</td></tr>
    )}</tbody></table></div></section>}
  </main>
}
