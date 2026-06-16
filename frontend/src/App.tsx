import {
  Activity,
  AlertTriangle,
  BarChart3,
  Boxes,
  Cloud,
  Cpu,
  Download,
  GitBranch,
  HardDrive,
  Layers3,
  LogOut,
  MemoryStick,
  Play,
  Plus,
  ShieldCheck,
  Trash2
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { api, clearToken, getToken, setToken } from "./api";
import type { Algorithm, Cluster, Dashboard, Forecast, Node, Priority, Simulation, TrafficPattern, Workload } from "./types";

const algorithms: Algorithm[] = ["Weighted Resource Scoring", "Best Fit", "Least Loaded"];
const trafficPatterns: TrafficPattern[] = ["Low", "Medium", "High", "Spike"];
const priorities: Priority[] = ["Low", "Medium", "High", "Critical"];

export function App() {
  const [tokenReady, setTokenReady] = useState(Boolean(getToken()));
  const [activeView, setActiveView] = useState("Dashboard");
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [workloads, setWorkloads] = useState<Workload[]>([]);
  const [simulations, setSimulations] = useState<Simulation[]>([]);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [failoverResult, setFailoverResult] = useState<Record<string, unknown> | null>(null);
  const [selectedClusterId, setSelectedClusterId] = useState<number | null>(null);
  const [algorithm, setAlgorithm] = useState<Algorithm>("Weighted Resource Scoring");
  const [traffic, setTraffic] = useState<TrafficPattern>("Medium");
  const [duration, setDuration] = useState(24);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get("token");
    if (token) {
      setToken(token);
      window.history.replaceState({}, "", "/");
      setTokenReady(true);
    }
  }, []);

  useEffect(() => {
    if (!tokenReady) return;
    void refresh();
  }, [tokenReady]);

  useEffect(() => {
    if (!selectedClusterId && clusters[0]) setSelectedClusterId(clusters[0].id);
  }, [clusters, selectedClusterId]);

  async function refresh() {
    try {
      setError("");
      const [dashboardData, clusterData, nodeData, workloadData, simulationData] = await Promise.all([
        api.dashboard(),
        api.clusters(),
        api.nodes(),
        api.workloads(),
        api.simulations()
      ]);
      setDashboard(dashboardData);
      setClusters(clusterData);
      setNodes(nodeData);
      setWorkloads(workloadData);
      setSimulations(simulationData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load data");
    }
  }

  async function loginDemo() {
    const response = await api.demoLogin();
    setToken(response.access_token);
    setTokenReady(true);
  }

  function logout() {
    clearToken();
    setTokenReady(false);
  }

  async function submit<T>(action: () => Promise<T>) {
    setBusy(true);
    setError("");
    try {
      await action();
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  const selectedCluster = clusters.find((cluster) => cluster.id === selectedClusterId) ?? clusters[0];
  const clusterNodes = selectedCluster ? nodes.filter((node) => node.cluster_id === selectedCluster.id) : [];
  const clusterWorkloads = selectedCluster ? workloads.filter((workload) => workload.cluster_id === selectedCluster.id) : [];
  const latestSimulation = simulations[0];

  if (!tokenReady) {
    return <Login onDemo={loginDemo} />;
  }

  return (
    <div className="min-h-screen bg-panel text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-line bg-white px-4 py-5 lg:block">
        <div className="flex items-center gap-3 px-2">
          <div className="grid h-10 w-10 place-items-center rounded bg-teal text-white">
            <Boxes size={21} />
          </div>
          <div>
            <div className="text-sm font-semibold">Capacity Management</div>
            <div className="text-xs text-slate-500">Simulator</div>
          </div>
        </div>
        <nav className="mt-8 space-y-1">
          {["Dashboard", "Clusters", "Nodes", "Workloads", "Simulations", "Forecasting", "Reports"].map((item) => (
            <button
              key={item}
              className={`nav-item ${activeView === item ? "nav-item-active" : ""}`}
              onClick={() => setActiveView(item)}
            >
              {navIcon(item)}
              <span>{item}</span>
            </button>
          ))}
        </nav>
      </aside>

      <main className="lg:pl-64">
        <header className="sticky top-0 z-10 flex min-h-16 items-center justify-between border-b border-line bg-white/95 px-4 backdrop-blur lg:px-8">
          <div>
            <h1 className="text-lg font-semibold">{activeView}</h1>
            <p className="text-xs text-slate-500">Model placement, failure recovery, and future resource pressure.</p>
          </div>
          <div className="flex items-center gap-2">
            <select className="control" value={selectedClusterId ?? ""} onChange={(event) => setSelectedClusterId(Number(event.target.value))}>
              {clusters.map((cluster) => (
                <option key={cluster.id} value={cluster.id}>
                  {cluster.name}
                </option>
              ))}
            </select>
            <button className="icon-button" onClick={logout} title="Log out">
              <LogOut size={18} />
            </button>
          </div>
        </header>

        <section className="space-y-5 p-4 lg:p-8">
          {error && <div className="border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
          {activeView === "Dashboard" && dashboard && (
            <DashboardView dashboard={dashboard} latestSimulation={latestSimulation} clusters={clusters} nodes={nodes} workloads={workloads} />
          )}
          {activeView === "Clusters" && <ClustersView clusters={clusters} busy={busy} onCreate={(payload) => submit(() => api.createCluster(payload))} onDelete={(id) => submit(() => api.deleteCluster(id))} />}
          {activeView === "Nodes" && selectedCluster && (
            <NodesView cluster={selectedCluster} nodes={clusterNodes} busy={busy} onCreate={(payload) => submit(() => api.createNode(payload))} onDelete={(id) => submit(() => api.deleteNode(id))} />
          )}
          {activeView === "Workloads" && selectedCluster && (
            <WorkloadsView
              cluster={selectedCluster}
              workloads={clusterWorkloads}
              busy={busy}
              onCreate={(payload) => submit(() => api.createWorkload(payload))}
              onDelete={(id) => submit(() => api.deleteWorkload(id))}
            />
          )}
          {activeView === "Simulations" && selectedCluster && (
            <SimulationsView
              simulations={simulations.filter((simulation) => simulation.cluster_id === selectedCluster.id)}
              algorithm={algorithm}
              traffic={traffic}
              duration={duration}
              setAlgorithm={setAlgorithm}
              setTraffic={setTraffic}
              setDuration={setDuration}
              busy={busy}
              onRun={() => submit(() => api.runSimulation({ cluster_id: selectedCluster.id, algorithm, traffic_pattern: traffic, duration_hours: duration }))}
              nodes={clusterNodes}
              failoverResult={failoverResult}
              onFailover={(failed_node_ids) => submit(async () => setFailoverResult(await api.failover({ cluster_id: selectedCluster.id, failed_node_ids, algorithm })))}
            />
          )}
          {activeView === "Forecasting" && selectedCluster && (
            <ForecastingView
              forecast={forecast}
              onLoad={() =>
                submit(async () => {
                  setForecast(await api.forecast(selectedCluster.id));
                })
              }
            />
          )}
          {activeView === "Reports" && <ReportsView simulations={simulations} />}
        </section>
      </main>
    </div>
  );
}

function Login({ onDemo }: { onDemo: () => void }) {
  return (
    <main className="grid min-h-screen grid-cols-1 bg-slate-950 text-white lg:grid-cols-[1.05fr_0.95fr]">
      <section className="flex flex-col justify-between p-8 lg:p-12">
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded bg-teal">
            <Boxes />
          </div>
          <div className="font-semibold">Capacity Management Simulator</div>
        </div>
        <div className="max-w-2xl py-16">
          <h1 className="text-4xl font-semibold leading-tight lg:text-6xl">Operate cluster capacity before production teaches the lesson.</h1>
          <p className="mt-5 max-w-xl text-slate-300">
            Place workloads, run traffic spikes, test node failures, and forecast capacity exhaustion from one SRE-focused control plane.
          </p>
        </div>
        <div className="text-xs text-slate-400">FastAPI + React + PostgreSQL + Redis</div>
      </section>
      <section className="flex items-center border-t border-slate-800 bg-white p-8 text-ink lg:border-l lg:border-t-0">
        <div className="w-full max-w-md">
          <h2 className="text-2xl font-semibold">Sign in</h2>
          <p className="mt-2 text-sm text-slate-500">Use OAuth in deployed environments or jump into the seeded demo workspace.</p>
          <div className="mt-8 space-y-3">
            <a className="login-button" href={api.authUrl("google")}>
              <Cloud size={18} /> Google Login
            </a>
            <a className="login-button" href={api.authUrl("github")}>
              <GitBranch size={18} /> GitHub Login
            </a>
            <button className="primary-button w-full" onClick={onDemo}>
              <ShieldCheck size={18} /> Demo Login
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}

function DashboardView({ dashboard, latestSimulation, clusters, nodes, workloads }: { dashboard: Dashboard; latestSimulation?: Simulation; clusters: Cluster[]; nodes: Node[]; workloads: Workload[] }) {
  const barData = [
    { name: "CPU", value: dashboard.utilization.cpu },
    { name: "Memory", value: dashboard.utilization.memory },
    { name: "Storage", value: dashboard.utilization.storage }
  ];
  return (
    <>
      <div className="grid gap-4 md:grid-cols-4">
        <Metric label="Clusters" value={dashboard.total_clusters} icon={<Layers3 />} />
        <Metric label="Active Nodes" value={dashboard.active_nodes} icon={<Cpu />} />
        <Metric label="Workloads" value={dashboard.active_workloads} icon={<Activity />} />
        <Metric label="Health" value={dashboard.health} icon={<ShieldCheck />} />
      </div>
      <div className="grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
        <Panel title="Resource Utilization">
          <ChartBox>
            <ResponsiveContainer>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="value" fill="#0f766e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartBox>
        </Panel>
        <Panel title="Inventory">
          <div className="compact-list">
            <span>{clusters.length} clusters across {new Set(clusters.map((cluster) => cluster.region)).size} regions</span>
            <span>{nodes.filter((node) => node.status === "Failed").length} failed nodes</span>
            <span>{workloads.filter((workload) => workload.priority === "Critical").length} critical workloads</span>
          </div>
        </Panel>
      </div>
      {latestSimulation && <SimulationChart simulation={latestSimulation} />}
    </>
  );
}

function ClustersView({ clusters, busy, onCreate, onDelete }: { clusters: Cluster[]; busy: boolean; onCreate: (payload: Omit<Cluster, "id">) => void; onDelete: (id: number) => void }) {
  const [form, setForm] = useState({ name: "", region: "us-east-1", description: "" });
  return (
    <CrudPanel
      title="Clusters"
      form={
        <>
          <Input label="Name" value={form.name} onChange={(name) => setForm({ ...form, name })} />
          <Input label="Region" value={form.region} onChange={(region) => setForm({ ...form, region })} />
          <Input label="Description" value={form.description} onChange={(description) => setForm({ ...form, description })} />
          <button className="primary-button" disabled={busy} onClick={() => onCreate(form)}>
            <Plus size={17} /> Create
          </button>
        </>
      }
    >
      <DataTable
        rows={clusters}
        columns={["name", "region", "description"]}
        onDelete={onDelete}
      />
    </CrudPanel>
  );
}

function NodesView({ cluster, nodes, busy, onCreate, onDelete }: { cluster: Cluster; nodes: Node[]; busy: boolean; onCreate: (payload: Omit<Node, "id">) => void; onDelete: (id: number) => void }) {
  const [form, setForm] = useState({ name: "", cpu_cores: 16, memory_gb: 64, storage_gb: 500, status: "Active" as const });
  return (
    <CrudPanel
      title={`Nodes in ${cluster.name}`}
      form={
        <>
          <Input label="Name" value={form.name} onChange={(name) => setForm({ ...form, name })} />
          <NumberInput label="CPU" value={form.cpu_cores} onChange={(cpu_cores) => setForm({ ...form, cpu_cores })} />
          <NumberInput label="Memory GB" value={form.memory_gb} onChange={(memory_gb) => setForm({ ...form, memory_gb })} />
          <NumberInput label="Storage GB" value={form.storage_gb} onChange={(storage_gb) => setForm({ ...form, storage_gb })} />
          <select className="control" value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value as "Active" })}>
            <option>Active</option>
            <option>Failed</option>
          </select>
          <button className="primary-button" disabled={busy} onClick={() => onCreate({ ...form, cluster_id: cluster.id })}>
            <Plus size={17} /> Add
          </button>
        </>
      }
    >
      <DataTable rows={nodes} columns={["name", "cpu_cores", "memory_gb", "storage_gb", "status"]} onDelete={onDelete} />
    </CrudPanel>
  );
}

function WorkloadsView({ cluster, workloads, busy, onCreate, onDelete }: { cluster: Cluster; workloads: Workload[]; busy: boolean; onCreate: (payload: Omit<Workload, "id">) => void; onDelete: (id: number) => void }) {
  const [form, setForm] = useState({ name: "", cpu_required: 4, memory_required: 8, storage_required: 50, priority: "Medium" as Priority });
  return (
    <CrudPanel
      title={`Workloads in ${cluster.name}`}
      form={
        <>
          <Input label="Name" value={form.name} onChange={(name) => setForm({ ...form, name })} />
          <NumberInput label="CPU" value={form.cpu_required} onChange={(cpu_required) => setForm({ ...form, cpu_required })} />
          <NumberInput label="Memory GB" value={form.memory_required} onChange={(memory_required) => setForm({ ...form, memory_required })} />
          <NumberInput label="Storage GB" value={form.storage_required} onChange={(storage_required) => setForm({ ...form, storage_required })} />
          <select className="control" value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value as Priority })}>
            {priorities.map((priority) => <option key={priority}>{priority}</option>)}
          </select>
          <button className="primary-button" disabled={busy} onClick={() => onCreate({ ...form, cluster_id: cluster.id })}>
            <Plus size={17} /> Add
          </button>
        </>
      }
    >
      <DataTable rows={workloads} columns={["name", "cpu_required", "memory_required", "storage_required", "priority"]} onDelete={onDelete} />
    </CrudPanel>
  );
}

function SimulationsView(props: {
  simulations: Simulation[];
  algorithm: Algorithm;
  traffic: TrafficPattern;
  duration: number;
  setAlgorithm: (value: Algorithm) => void;
  setTraffic: (value: TrafficPattern) => void;
  setDuration: (value: number) => void;
  busy: boolean;
  onRun: () => void;
  nodes: Node[];
  failoverResult: Record<string, unknown> | null;
  onFailover: (failedNodeIds: number[]) => void;
}) {
  const [failedNodeIds, setFailedNodeIds] = useState<number[]>([]);
  return (
    <>
      <Panel title="Run Simulation">
        <div className="form-grid">
          <select className="control" value={props.algorithm} onChange={(event) => props.setAlgorithm(event.target.value as Algorithm)}>
            {algorithms.map((item) => <option key={item}>{item}</option>)}
          </select>
          <select className="control" value={props.traffic} onChange={(event) => props.setTraffic(event.target.value as TrafficPattern)}>
            {trafficPatterns.map((item) => <option key={item}>{item}</option>)}
          </select>
          <NumberInput label="Duration Hours" value={props.duration} onChange={props.setDuration} />
          <button className="primary-button" disabled={props.busy} onClick={props.onRun}>
            <Play size={17} /> Run
          </button>
        </div>
      </Panel>
      {props.simulations[0] && <SimulationChart simulation={props.simulations[0]} />}
      <Panel title="Failover Simulation">
        <div className="grid gap-3 md:grid-cols-[1fr_auto]">
          <div className="flex flex-wrap gap-2">
            {props.nodes.map((node) => (
              <label key={node.id} className="check-pill">
                <input
                  type="checkbox"
                  checked={failedNodeIds.includes(node.id)}
                  onChange={(event) =>
                    setFailedNodeIds(event.target.checked ? [...failedNodeIds, node.id] : failedNodeIds.filter((id) => id !== node.id))
                  }
                />
                {node.name}
              </label>
            ))}
          </div>
          <button className="primary-button" onClick={() => props.onFailover(failedNodeIds)}>
            <AlertTriangle size={17} /> Test
          </button>
        </div>
        {props.failoverResult && <pre className="result-box">{JSON.stringify(props.failoverResult, null, 2)}</pre>}
      </Panel>
    </>
  );
}

function ForecastingView({ forecast, onLoad }: { forecast: Forecast | null; onLoad: () => void }) {
  return (
    <Panel title="Capacity Forecast">
      <button className="primary-button mb-4" onClick={onLoad}>
        <BarChart3 size={17} /> Generate Forecast
      </button>
      {forecast && (
        <div className="grid gap-4 md:grid-cols-3">
          {Object.entries(forecast.exhaustion_dates).map(([resource, date]) => (
            <div className="mini-card" key={resource}>
              <div className="text-xs uppercase text-slate-500">{resource}</div>
              <div className="mt-2 text-lg font-semibold">{date}</div>
              <div className="text-sm text-slate-500">30-day extra need: {forecast.future_needs[resource]}%</div>
            </div>
          ))}
          <div className="md:col-span-3">
            <div className="compact-list">{forecast.recommendations.map((item) => <span key={item}>{item}</span>)}</div>
          </div>
        </div>
      )}
    </Panel>
  );
}

function ReportsView({ simulations }: { simulations: Simulation[] }) {
  return (
    <Panel title="Reports">
      <DataTable
        rows={simulations}
        columns={["id", "algorithm", "traffic_pattern", "duration_hours", "created_at"]}
        actions={(row) => (
          <div className="flex gap-1">
            {(["pdf", "csv", "json"] as const).map((format) => (
              <button className="icon-button" title={`Download ${format}`} key={format} onClick={() => void api.downloadReport(row.id, format)}>
                <Download size={15} />
              </button>
            ))}
          </div>
        )}
      />
    </Panel>
  );
}

function SimulationChart({ simulation }: { simulation: Simulation }) {
  const data = useMemo(
    () =>
      simulation.results.timeline.map((point) => ({
        ...point,
        timestamp: new Date(point.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      })),
    [simulation]
  );
  return (
    <Panel title={`Simulation ${simulation.id}: ${simulation.algorithm}`}>
      <ChartBox>
        <ResponsiveContainer>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" minTickGap={24} />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="cpu" stackId="1" stroke="#0f766e" fill="#99f6e4" />
            <Area type="monotone" dataKey="memory" stackId="2" stroke="#7c3aed" fill="#ddd6fe" />
            <Area type="monotone" dataKey="storage" stackId="3" stroke="#b45309" fill="#fde68a" />
          </AreaChart>
        </ResponsiveContainer>
      </ChartBox>
      <div className="compact-list mt-4">
        {simulation.results.bottlenecks.map((item) => <span key={item}>{item}</span>)}
      </div>
    </Panel>
  );
}

function CrudPanel({ title, form, children }: { title: string; form: React.ReactNode; children: React.ReactNode }) {
  return (
    <Panel title={title}>
      <div className="form-grid">{form}</div>
      <div className="mt-5">{children}</div>
    </Panel>
  );
}

function DataTable<T extends { id: number }>({ rows, columns, onDelete, actions }: { rows: T[]; columns: Array<keyof T & string>; onDelete?: (id: number) => void; actions?: (row: T) => React.ReactNode }) {
  return (
    <div className="overflow-x-auto border border-line">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="bg-slate-100 text-xs uppercase text-slate-500">
          <tr>
            {columns.map((column) => <th className="px-3 py-2" key={column}>{column.replaceAll("_", " ")}</th>)}
            {(onDelete || actions) && <th className="px-3 py-2">Actions</th>}
          </tr>
        </thead>
        <tbody className="divide-y divide-line bg-white">
          {rows.map((row) => (
            <tr key={row.id}>
              {columns.map((column) => <td className="px-3 py-2" key={column}>{String(row[column] ?? "")}</td>)}
              {(onDelete || actions) && (
                <td className="px-3 py-2">
                  {actions?.(row)}
                  {onDelete && (
                    <button className="icon-button" title="Delete" onClick={() => onDelete(row.id)}>
                      <Trash2 size={15} />
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Metric({ label, value, icon }: { label: string; value: number | string; icon: React.ReactNode }) {
  return (
    <div className="mini-card">
      <div className="flex items-center justify-between text-slate-500">
        <span className="text-xs uppercase">{label}</span>
        {icon}
      </div>
      <div className="mt-3 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="border border-line bg-white p-4 shadow-sm">
      <h2 className="mb-4 text-sm font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function ChartBox({ children }: { children: React.ReactNode }) {
  return <div className="h-72 w-full">{children}</div>;
}

function Input({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return <input className="control" placeholder={label} value={value} onChange={(event) => onChange(event.target.value)} />;
}

function NumberInput({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return <input className="control" type="number" min="1" placeholder={label} value={value} onChange={(event) => onChange(Number(event.target.value))} />;
}

function navIcon(item: string) {
  const props = { size: 17 };
  if (item === "Dashboard") return <BarChart3 {...props} />;
  if (item === "Clusters") return <Layers3 {...props} />;
  if (item === "Nodes") return <Cpu {...props} />;
  if (item === "Workloads") return <Activity {...props} />;
  if (item === "Simulations") return <Play {...props} />;
  if (item === "Forecasting") return <MemoryStick {...props} />;
  return <HardDrive {...props} />;
}
