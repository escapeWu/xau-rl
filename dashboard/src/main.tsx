import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock,
  Database,
  ExternalLink,
  FileText,
  Image as ImageIcon,
  RefreshCw,
  Shield,
  Table2,
} from 'lucide-react'
import './index.css'

type ArtifactKind = 'csv' | 'json' | 'html' | 'image' | 'text' | 'other'

type Artifact = {
  path: string
  name: string
  kind: ArtifactKind
  extension: string
  sizeBytes: number
  sizeLabel: string
  modifiedAt: string
  url: string
}

type MetricBlock = {
  path?: string
  rows?: Record<string, string>[]
  updatedAt?: string
  error?: string
} | null

type StatusPayload = {
  projectRoot: string
  generatedAt: string
  hasOutputs: boolean
  hasModels: boolean
  gate: { status: string; noDeployPath?: string | null; message?: string | null }
  runInfo?: Record<string, unknown> | null
  latestModel?: Artifact | null
  summary?: {
    slidingWalkForward?: {
      status: string
      path?: string
      foldCount?: number
      positiveReturnFolds?: number
      profitFactorGtOneFolds?: number
      testStart?: string
      testEnd?: string
      worstReturnPct?: number | null
      worstProfitFactor?: number | null
      worstMaxDrawdownPct?: number | null
      meanSharpe?: number | null
      totalTrades?: number | null
      stitchedOos?: {
        path?: string | null
        rows?: number
        firstTime?: string | null
        lastTime?: string | null
        totalReturnPct?: number | null
        maxDrawdownPct?: number | null
      }
      gatePassed?: boolean | null
      promotedFromFold?: number | null
    } | null
    sealedHoldout?: { status: string; reportPath?: string | null }
  }
  artifactCount: number
  artifacts: Artifact[]
  metrics: {
    performanceReport: MetricBlock
    selectedPolicy: MetricBlock
    walkForwardBaseline: MetricBlock
    slidingWalkForwardSummary: MetricBlock
  }
}

type PreviewPayload = {
  meta: Artifact
  csv?: { columns: string[]; rows: Record<string, string>[]; totalRows: number; previewRows: number }
  json?: unknown
  text?: string
}

const API_STATUS = '/api/status'
const fmtDate = (iso?: string) => (iso ? new Date(iso).toLocaleString() : '—')
const pct = (value: unknown, digits = 2) => {
  const n = Number(value)
  return Number.isFinite(n) ? `${n.toFixed(digits)}%` : '—'
}
const num = (value: unknown, digits = 2) => {
  const n = Number(value)
  return Number.isFinite(n) ? n.toFixed(digits) : '—'
}

function metricRows(block: MetricBlock) {
  return Array.isArray(block?.rows) ? block!.rows! : []
}

function scenarioMetrics(block: MetricBlock, scenario: string) {
  const out: Record<string, string> = {}
  for (const row of metricRows(block)) {
    if (row.scenario === scenario && row.metric) out[row.metric] = row.value
  }
  return out
}

function selectedPolicy(block: MetricBlock) {
  const out: Record<string, string> = {}
  for (const row of metricRows(block)) {
    const key = row[''] || row.metric || row.name || row.key
    if (key) out[key] = row.value
  }
  return out
}

function StatCard({ title, value, sub, tone = 'slate' }: { title: string; value: string; sub?: string; tone?: 'slate' | 'green' | 'red' | 'amber' | 'cyan' }) {
  const toneMap = {
    slate: 'from-slate-800/70 to-slate-900/80 border-slate-700/70',
    green: 'from-emerald-500/15 to-slate-900/80 border-emerald-400/30',
    red: 'from-rose-500/15 to-slate-900/80 border-rose-400/30',
    amber: 'from-amber-500/15 to-slate-900/80 border-amber-400/30',
    cyan: 'from-cyan-500/15 to-slate-900/80 border-cyan-400/30',
  }[tone]
  return (
    <div className={`rounded-2xl border bg-gradient-to-br p-4 shadow-xl shadow-black/20 ${toneMap}`}>
      <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{title}</div>
      <div className="mt-2 text-2xl font-semibold text-white">{value}</div>
      {sub && <div className="mt-1 text-sm text-slate-400">{sub}</div>}
    </div>
  )
}

function Section({ title, icon, children, right }: { title: string; icon: React.ReactNode; children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <section className="rounded-3xl border border-slate-800/80 bg-slate-950/70 p-5 shadow-2xl shadow-black/30 backdrop-blur">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="rounded-2xl border border-slate-700/70 bg-slate-900 p-2 text-cyan-300">{icon}</div>
          <h2 className="text-lg font-semibold text-white">{title}</h2>
        </div>
        {right}
      </div>
      {children}
    </section>
  )
}

function ArtifactIcon({ kind }: { kind: ArtifactKind }) {
  if (kind === 'image') return <ImageIcon className="h-4 w-4" />
  if (kind === 'html') return <BarChart3 className="h-4 w-4" />
  if (kind === 'csv') return <Table2 className="h-4 w-4" />
  return <FileText className="h-4 w-4" />
}

function CsvTable({ rows, limit = 12 }: { rows: Record<string, string>[]; limit?: number }) {
  const columns = Object.keys(rows[0] || {})
  if (!rows.length) return <div className="text-sm text-slate-500">暂无数据</div>
  return (
    <div className="overflow-auto rounded-2xl border border-slate-800">
      <table className="min-w-full divide-y divide-slate-800 text-sm">
        <thead className="bg-slate-900/80 text-slate-300">
          <tr>{columns.map((c) => <th key={c} className="whitespace-nowrap px-3 py-2 text-left font-medium">{c || 'key'}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-slate-800/70">
          {rows.slice(0, limit).map((row, i) => (
            <tr key={i} className="odd:bg-slate-900/30">
              {columns.map((c) => <td key={c} className="whitespace-nowrap px-3 py-2 text-slate-300">{row[c]}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ArtifactViewer({ artifact }: { artifact: Artifact | null }) {
  const [preview, setPreview] = useState<PreviewPayload | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!artifact) return
    setPreview(null)
    if (artifact.kind === 'csv' || artifact.kind === 'json' || artifact.kind === 'text') {
      setLoading(true)
      fetch(`/api/preview?path=${encodeURIComponent(artifact.path)}`)
        .then((r) => r.json())
        .then(setPreview)
        .finally(() => setLoading(false))
    }
  }, [artifact])

  if (!artifact) {
    return <div className="flex min-h-[24rem] items-center justify-center rounded-2xl border border-dashed border-slate-800 text-slate-500">选择左侧产物查看</div>
  }
  if (artifact.kind === 'html') {
    return <iframe className="h-[34rem] w-full rounded-2xl border border-slate-700" src={artifact.url} title={artifact.name} />
  }
  if (artifact.kind === 'image') {
    return <img src={artifact.url} alt={artifact.name} className="max-h-[34rem] w-full rounded-2xl border border-slate-700 object-contain" />
  }
  if (loading) return <div className="text-slate-400">读取中…</div>
  if (preview?.csv) return <CsvTable rows={preview.csv.rows} limit={30} />
  if (preview?.json) return <pre className="max-h-[34rem] overflow-auto rounded-2xl border border-slate-800 bg-slate-950 p-4 text-xs text-slate-300">{JSON.stringify(preview.json, null, 2)}</pre>
  if (preview?.text) return <pre className="max-h-[34rem] overflow-auto rounded-2xl border border-slate-800 bg-slate-950 p-4 text-xs text-slate-300">{preview.text}</pre>
  return <div className="text-slate-400">该文件可通过新窗口打开。</div>
}

function App() {
  const [status, setStatus] = useState<StatusPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Artifact | null>(null)
  const [kindFilter, setKindFilter] = useState<string>('all')
  const [query, setQuery] = useState('')

  const load = () => {
    fetch(API_STATUS)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then((data) => {
        setStatus(data)
        setError(null)
        if (!selected && data.artifacts?.length) {
          const firstHtml = data.artifacts.find((a: Artifact) => a.kind === 'html')
          setSelected(firstHtml || data.artifacts[0])
        }
      })
      .catch((e) => setError(String(e)))
  }

  useEffect(() => {
    load()
    const timer = window.setInterval(load, 15000)
    return () => window.clearInterval(timer)
  }, [])

  const selectedVal = scenarioMetrics(status?.metrics.performanceReport || null, 'selected_val')
  const baselineVal = scenarioMetrics(status?.metrics.performanceReport || null, 'baseline_val')
  const policy = selectedPolicy(status?.metrics.selectedPolicy || null)
  const wf = status?.summary?.slidingWalkForward
  const holdout = status?.summary?.sealedHoldout
  const artifacts = useMemo(() => {
    const list = status?.artifacts || []
    return list.filter((a) => {
      const okKind = kindFilter === 'all' || a.kind === kindFilter
      const okText = !query || `${a.path} ${a.name}`.toLowerCase().includes(query.toLowerCase())
      return okKind && okText
    })
  }, [status, kindFilter, query])

  const gateTone = status?.gate.status === 'blocked' || status?.gate.status === 'failed' ? 'red' : status?.gate.status === 'passed' ? 'green' : 'amber'

  return (
    <main className="mx-auto max-w-7xl px-4 py-6 text-slate-100 sm:px-6 lg:px-8">
      <header className="mb-6 flex flex-col gap-4 rounded-3xl border border-slate-800/70 bg-slate-950/60 p-6 shadow-2xl shadow-black/30 backdrop-blur md:flex-row md:items-end md:justify-between">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-medium text-cyan-200">
            <Activity className="h-3.5 w-3.5" /> XAUUSD RL Research Dashboard
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white md:text-4xl">训练结果看板</h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-400">读取本地 outputs/、models/、notebooks/ 下的运行结果、图表、CSV 和模型门控状态。自动每 15 秒刷新。</p>
          <p className="mt-1 text-xs text-slate-500">项目：{status?.projectRoot || '加载中…'}</p>
        </div>
        <button onClick={load} className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-medium text-slate-100 hover:bg-slate-800">
          <RefreshCw className="h-4 w-4" /> 刷新
        </button>
      </header>

      {error && <div className="mb-6 rounded-2xl border border-rose-400/40 bg-rose-500/10 p-4 text-rose-200">API 错误：{error}</div>}

      <div className="mb-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="PPO Walk-forward" value={wf?.stitchedOos?.totalReturnPct != null ? pct(wf.stitchedOos.totalReturnPct) : 'pending'} sub={wf ? `${wf.positiveReturnFolds}/${wf.foldCount} folds positive · PF>1 ${wf.profitFactorGtOneFolds}/${wf.foldCount}` : '等待 sliding summary'} tone={wf?.gatePassed ? 'green' : 'amber'} />
        <StatCard title="Walk-forward Max DD" value={wf?.stitchedOos?.maxDrawdownPct != null ? pct(wf.stitchedOos.maxDrawdownPct) : '—'} sub={wf ? `Worst fold PF ${num(wf.worstProfitFactor, 3)} · Trades ${num(wf.totalTrades, 0)}` : '训练完成后显示'} tone="amber" />
        <StatCard title="Gate / Model" value={status?.gate.status || 'pending'} sub={wf?.promotedFromFold ? `promoted from fold ${wf.promotedFromFold}` : status?.latestModel?.name || '等待 PPO 产物'} tone={gateTone} />
        <StatCard title="Sealed Holdout" value={holdout?.status === 'revealed' ? 'revealed' : 'not revealed'} sub={holdout?.status === 'revealed' ? holdout.reportPath || 'holdout report exists' : '最终保留集仍未揭盲'} tone={holdout?.status === 'revealed' ? 'red' : 'cyan'} />
      </div>

      <div className="mb-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Selected Val Return" value={pct(selectedVal.total_return_pct)} sub={`PF ${num(selectedVal.profit_factor)} / Trades ${num(selectedVal.n_trades, 0)}`} tone={Number(selectedVal.total_return_pct) >= 0 ? 'green' : 'red'} />
        <StatCard title="Selected Max DD" value={pct(selectedVal.max_drawdown_pct)} sub={`Sharpe ${num(selectedVal.sharpe_like)}`} tone="amber" />
        <StatCard title="Baseline Val Return" value={pct(baselineVal.total_return_pct)} sub={`PF ${num(baselineVal.profit_factor)} / Trades ${num(baselineVal.n_trades, 0)}`} tone={Number(baselineVal.total_return_pct) >= 0 ? 'green' : 'red'} />
        <StatCard title="Artifacts" value={String(status?.artifactCount ?? 0)} sub={`刷新 ${fmtDate(status?.generatedAt)}`} tone="slate" />
      </div>

      <div className="mb-6 rounded-3xl border border-cyan-400/20 bg-cyan-400/10 p-4 text-sm text-cyan-100">
        当前 PPO 指标来自 sliding walk-forward OOS。它是滚动样本外证据，不是 sealed holdout；如果后续按这些结果继续调参，会污染验证口径。
      </div>

      <div className="mb-6 grid gap-6 lg:grid-cols-3">
        <Section title="当前策略参数" icon={<Shield className="h-5 w-5" />}>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {Object.entries(policy).map(([k, v]) => (
              <div key={k} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-3">
                <div className="text-xs text-slate-500">{k}</div>
                <div className="mt-1 font-semibold text-white">{v}</div>
              </div>
            ))}
            {!Object.keys(policy).length && <div className="text-slate-500">暂无 selected_policy.csv</div>}
          </div>
        </Section>
        <Section title="运行状态" icon={status?.gate.status === 'blocked' ? <AlertTriangle className="h-5 w-5" /> : <CheckCircle2 className="h-5 w-5" />}>
          <div className="space-y-3 text-sm text-slate-300">
            <div className="flex justify-between gap-3"><span className="text-slate-500">outputs</span><span>{status?.hasOutputs ? '存在' : '缺失'}</span></div>
            <div className="flex justify-between gap-3"><span className="text-slate-500">models</span><span>{status?.hasModels ? '存在' : '缺失/训练中'}</span></div>
            <div className="flex justify-between gap-3"><span className="text-slate-500">产物数量</span><span>{status?.artifactCount ?? 0}</span></div>
            <div className="flex justify-between gap-3"><span className="text-slate-500">刷新时间</span><span>{fmtDate(status?.generatedAt)}</span></div>
            {status?.gate.message && <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 p-3 text-rose-200">{status.gate.message}</div>}
          </div>
        </Section>
        <Section title="Walk-forward 概览" icon={<Database className="h-5 w-5" />}>
          {wf && (
            <div className="mb-3 grid grid-cols-2 gap-2 text-xs text-slate-300">
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-3"><span className="text-slate-500">test window</span><br />{wf.testStart} → {wf.testEnd}</div>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-3"><span className="text-slate-500">stitched rows</span><br />{wf.stitchedOos?.rows ?? '—'}</div>
            </div>
          )}
          {status?.metrics.slidingWalkForwardSummary?.rows?.length ? (
            <CsvTable rows={status.metrics.slidingWalkForwardSummary.rows} limit={5} />
          ) : (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-400">PPO sliding walk-forward 还没完成。训练结束后这里会显示 models/sliding_walk_forward_summary.csv。</div>
          )}
        </Section>
      </div>

      <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
        <Section
          title="本地产物"
          icon={<FileText className="h-5 w-5" />}
          right={<span className="text-xs text-slate-500">{artifacts.length} 项</span>}
        >
          <div className="mb-3 grid gap-2">
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="搜索文件名…" className="rounded-2xl border border-slate-800 bg-slate-900 px-3 py-2 text-sm outline-none ring-cyan-400/40 focus:ring-2" />
            <select value={kindFilter} onChange={(e) => setKindFilter(e.target.value)} className="rounded-2xl border border-slate-800 bg-slate-900 px-3 py-2 text-sm outline-none ring-cyan-400/40 focus:ring-2">
              <option value="all">全部类型</option>
              <option value="html">HTML 图表</option>
              <option value="image">图片</option>
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
              <option value="text">文本/日志</option>
            </select>
          </div>
          <div className="max-h-[42rem] space-y-2 overflow-auto pr-1">
            {artifacts.map((a) => (
              <button key={a.path} onClick={() => setSelected(a)} className={`w-full rounded-2xl border p-3 text-left transition hover:border-cyan-400/50 hover:bg-slate-900 ${selected?.path === a.path ? 'border-cyan-400/60 bg-cyan-400/10' : 'border-slate-800 bg-slate-900/40'}`}>
                <div className="flex items-start gap-2">
                  <span className="mt-0.5 text-cyan-300"><ArtifactIcon kind={a.kind} /></span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-slate-100">{a.name}</span>
                    <span className="mt-1 block truncate text-xs text-slate-500">{a.path}</span>
                    <span className="mt-1 flex items-center gap-2 text-xs text-slate-500"><Clock className="h-3 w-3" /> {fmtDate(a.modifiedAt)} · {a.sizeLabel}</span>
                  </span>
                </div>
              </button>
            ))}
          </div>
        </Section>

        <Section
          title={selected?.name || '产物预览'}
          icon={<ArtifactIcon kind={selected?.kind || 'other'} />}
          right={selected && <a href={selected.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm text-cyan-300 hover:text-cyan-200">新窗口 <ExternalLink className="h-3.5 w-3.5" /></a>}
        >
          {selected && <div className="mb-3 text-xs text-slate-500">{selected.path} · {selected.sizeLabel} · {fmtDate(selected.modifiedAt)}</div>}
          <ArtifactViewer artifact={selected} />
        </Section>
      </div>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
