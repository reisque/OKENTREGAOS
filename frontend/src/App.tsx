import { useState } from 'react'
import { Download, FileCode2, FileText, Search } from 'lucide-react'

type Result = { input: string; normalized: string; os_number?: string; status?: string; booking?: string; container?: string; contractor?: string; depot?: string; found: boolean; message?: string }
const apiUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? 'http://localhost:8000'
const splitOs = (value: string) => value.split(/[\n,;]+/).map(item => item.trim()).filter(Boolean)
const normalizedOs = (value: string) => value.replace(/\s+/g, '').toUpperCase()

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

  return <main className="page"><section className="hero"><p className="eyebrow">OK ENTREGA</p><h1>Consulta de ordem de serviço</h1><p>Consulte uma ou mais OS e baixe os arquivos XML e PDF.</p></section><section className="panel"><form onSubmit={consult}><label htmlFor="os">Número da OS</label><div className="query"><textarea id="os" value={value} onChange={event => setValue(event.target.value)} placeholder="Ex.: 6SP 568396C ou 6SP568396C" rows={3} /><button disabled={loading}>{loading ? 'Consultando...' : <><Search size={18}/> Consultar</>}</button></div><small>Para várias OS, separe por vírgula, ponto e vírgula ou uma por linha.</small></form>{error && <div className="error">{error}</div>}</section>{results.length > 0 && <section className="results"><div className="results-head"><h2>Resultado da consulta</h2><span>{results.filter(item => item.found).length} encontrada(s)</span></div><div className="cards">{results.map((item, index) => <article className="card" key={`${item.normalized}-${index}`}><div className="card-top"><div><p className="label">ORDEM DE SERVIÇO</p><h3>{item.os_number ?? item.normalized}</h3></div><span className={item.found ? 'badge success' : 'badge'}>{item.found ? item.status : 'Não encontrada'}</span></div>{item.found ? <><dl><div><dt>Booking</dt><dd>{item.booking || '—'}</dd></div><div><dt>Contêiner</dt><dd>{item.container || '—'}</dd></div><div><dt>Contratante</dt><dd>{item.contractor || '—'}</dd></div><div><dt>Depot</dt><dd>{item.depot || '—'}</dd></div></dl><div className="actions"><button onClick={() => download(item.os_number!, 'xml')}><FileCode2 size={17}/> Baixar XML</button><button className="pdf" onClick={() => download(item.os_number!, 'pdf')}><FileText size={17}/> Baixar PDF <Download size={15}/></button></div></> : <p className="not-found">{item.message}</p>}</article>)}</div></section>}</main>
}
