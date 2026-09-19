import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

const API_BASE = "http://localhost:8000";

type Summary = {
  total_articles: number;
  total_categories: number;
  total_sources: number;
  fulltext_articles: number;
  rss_fallback_articles: number;
  latest_crawled_at: string | null;
};

type Category = {
  category: string;
  total: number;
  percentage: number;
};

type Trend = {
  day: string;
  categories: Record<string, number>;
  total: number;
};

type NewsItem = {
  id: number;
  title: string;
  category: string;
  source: string;
  content_source: string;
  decision_score: number;
  published_at: string | null;
  crawled_at: string | null;
  url: string;
};

type CrawlerStatus = {
  status: string;
  last_run_status: string;
  last_run_source: string | null;
  last_started_at: string | null;
  last_finished_at: string | null;
  last_error: string | null;
  last_stats: Record<string, number> | null;
};

const chartColors = [
  "#9B5C45",
  "#66785A",
  "#547181",
  "#C18B3E",
  "#886B54",
  "#737884",
  "#9A5260",
  "#5E7C72",
  "#98754E",
  "#69636C",
  "#B36F54",
  "#71818B",
];

function App() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [trend, setTrend] = useState<Trend[]>([]);
  const [recent, setRecent] = useState<NewsItem[]>([]);

  const [category, setCategory] = useState("");
  const [contentSource, setContentSource] = useState("");
  const [datePreset, setDatePreset] = useState("all");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [crawlerStatus, setCrawlerStatus] =
    useState<CrawlerStatus | null>(null);
  const [crawlerMessage, setCrawlerMessage] =
    useState("");

  const query = useMemo(() => {
    const params = new URLSearchParams();

    let from = fromDate;
    let to = toDate;

    if (datePreset === "today") {
      const d = new Date().toISOString().slice(0, 10);
      from = d;
      to = d;
    }

    if (datePreset === "7d") {
      const now = new Date();
      const fromD = new Date(now);
      fromD.setDate(now.getDate() - 6);
      from = fromD.toISOString().slice(0, 10);
      to = now.toISOString().slice(0, 10);
    }

    if (datePreset === "30d") {
      const now = new Date();
      const fromD = new Date(now);
      fromD.setDate(now.getDate() - 29);
      from = fromD.toISOString().slice(0, 10);
      to = now.toISOString().slice(0, 10);
    }

    if (from) params.set("from_date", from);
    if (to) params.set("to_date", to);
    if (category) params.set("category", category);
    if (contentSource) params.set("content_source", contentSource);

    return params.toString();
  }, [datePreset, fromDate, toDate, category, contentSource]);

  const loadCrawlerStatus = async () => {
    try {
      const response = await fetch(
        `${API_BASE}/crawler/status`,
      );

      if (!response.ok) {
        return;
      }

      const data: CrawlerStatus = await response.json();
      setCrawlerStatus(data);
    } catch {
      setCrawlerStatus(null);
    }
  };

  const runCrawlerNow = async () => {
    try {
      setCrawlerMessage("Đang khởi chạy crawler...");

      const response = await fetch(
        `${API_BASE}/crawler/run-now`,
        {
          method: "POST",
        },
      );

      if (response.status === 409) {
        setCrawlerMessage(
          "Crawler đang chạy, không thể chạy song song.",
        );
        await loadCrawlerStatus();
        return;
      }

      if (!response.ok) {
        throw new Error(
          `Crawler request failed: ${response.status}`,
        );
      }

      setCrawlerMessage(
        "Crawler đã khởi chạy. Đang theo dõi...",
      );

      for (let i = 0; i < 30; i++) {
        await new Promise((resolve) =>
          setTimeout(resolve, 1000),
        );

        const statusResponse = await fetch(
          `${API_BASE}/crawler/status`,
        );

        if (!statusResponse.ok) {
          continue;
        }

        const status: CrawlerStatus =
          await statusResponse.json();

        setCrawlerStatus(status);

        if (status.status === "idle") {
          if (status.last_run_status === "success") {
            const stats = status.last_stats;

            if (stats) {
              setCrawlerMessage(
                `Crawler hoàn tất · ${stats.articles_parsed ?? 0} parsed · ` +
                `${stats.articles_created ?? 0} new · ` +
                `${stats.articles_duplicate ?? 0} duplicate`,
              );
            } else {
              setCrawlerMessage(
                "Crawler hoàn tất thành công.",
              );
            }
          } else if (
            status.last_run_status === "error"
          ) {
            setCrawlerMessage(
              status.last_error ||
                "Crawler hoàn tất nhưng có lỗi.",
            );
          }

          await loadDashboard();
          return;
        }
      }

      setCrawlerMessage(
        "Crawler vẫn đang chạy. Hãy làm mới dữ liệu sau.",
      );
    } catch (err) {
      setCrawlerMessage(
        err instanceof Error
          ? err.message
          : "Không thể khởi chạy crawler.",
      );
    } finally {
      await loadCrawlerStatus();
    }
  };

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      const suffix = query ? `?${query}` : "";
      const recentSuffix = query
        ? `?${query}&limit=20`
        : "?limit=20";

      const [summaryRes, categoryRes, trendRes, recentRes] =
        await Promise.all([
          fetch(`${API_BASE}/analytics/summary${suffix}`),
          fetch(`${API_BASE}/analytics/categories${suffix}`),
          fetch(`${API_BASE}/analytics/trend-by-category${suffix}`),
          fetch(`${API_BASE}/analytics/recent${recentSuffix}`),
        ]);

      if (
        !summaryRes.ok ||
        !categoryRes.ok ||
        !trendRes.ok ||
        !recentRes.ok
      ) {
        throw new Error("Analytics API request failed.");
      }

      const summaryData = await summaryRes.json();
      const categoryData = await categoryRes.json();
      const trendData = await trendRes.json();
      const recentData = await recentRes.json();

      setSummary(summaryData);
      setCategories(categoryData.items);
      setTrend(trendData.items);
      setRecent(recentData.items);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Cannot load dashboard data.",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
    loadCrawlerStatus();
  }, [query]);

  const trendCategories = useMemo(() => {
    const validCategories = new Set(
      categories.map((item) => item.category),
    );

    const names = new Set<string>();

    trend.forEach((day) => {
      Object.keys(day.categories).forEach((name) => {
        if (validCategories.has(name)) {
          names.add(name);
        }
      });
    });

    return Array.from(names);
  }, [trend, categories]);

  const trendData = useMemo(
    () =>
      trend.map((item) => ({
        day: item.day.slice(5),
        ...item.categories,
      })),
    [trend],
  );

  const qualityData = summary
    ? [
        {
          name: "Fulltext",
          value: summary.fulltext_articles,
        },
        {
          name: "RSS Fallback",
          value: summary.rss_fallback_articles,
        },
      ]
    : [];

  const fulltextRate =
    summary && summary.total_articles
      ? (
          (summary.fulltext_articles / summary.total_articles) *
          100
        ).toFixed(1)
      : "0.0";

  const fallbackRate =
    summary && summary.total_articles
      ? (
          (summary.rss_fallback_articles / summary.total_articles) *
          100
        ).toFixed(1)
      : "0.0";

  const lastCrawl = summary?.latest_crawled_at
    ? new Date(summary.latest_crawled_at).toLocaleString("vi-VN")
    : "—";

  const resetFilters = () => {
    setCategory("");
    setContentSource("");
    setDatePreset("all");
    setFromDate("");
    setToDate("");
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <div className="eyebrow">P2 · ML / NLP MONITORING</div>
          <h1 style={{ color: "#211c18", WebkitTextFillColor: "#211c18" }}>Vietnamese News Intelligence</h1>
          <p>
            News classification, data quality and trend analytics
          </p>
        </div>

        <div className="header-actions">
          <div className="header-actions">
  <button
    className="refresh-btn"
    onClick={loadDashboard}
    disabled={loading}
  >
    {loading ? "Đang tải..." : "↻ Làm mới dữ liệu"}
  </button>
</div>

          <button
            className="run-btn"
            onClick={runCrawlerNow}
            disabled={crawlerStatus?.status === "running"}
          >
            {crawlerStatus?.status === "running"
              ? "● Crawler Running..."
              : "▶ Run Crawler Now"}
          </button>
        </div>
      </header>

      <section className="filters">
        <div>
          <label>Date Range</label>
          <select
            value={datePreset}
            onChange={(e) => setDatePreset(e.target.value)}
          >
            <option value="all">All</option>
            <option value="today">Today</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="custom">Custom Range</option>
          </select>
        </div>

        {datePreset === "custom" && (
          <>
            <div>
              <label>From</label>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
              />
            </div>

            <div>
              <label>To</label>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
              />
            </div>
          </>
        )}

        <div>
          <label>Category</label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="">All categories</option>
            {categories.map((item) => (
              <option key={item.category} value={item.category}>
                {item.category}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label>Content Source</label>
          <select
            value={contentSource}
            onChange={(e) => setContentSource(e.target.value)}
          >
            <option value="">All sources</option>
            <option value="fulltext">Fulltext</option>
            <option value="rss_fallback">RSS Fallback</option>
          </select>
        </div>

        <button className="reset-btn" onClick={resetFilters}>
          Reset
        </button>
      </section>

      {error && (
        <div className="error">
          {error}
        </div>
      )}

      {crawlerMessage && (
        <div className="crawler-message">
          <span>●</span>
          {crawlerMessage}
        </div>
      )}

      <main className="dashboard">
        <section className="kpis">
          <div className="card">
            <span>Articles</span>
            <strong>{summary?.total_articles ?? "—"}</strong>
            <small>Filtered dataset</small>
          </div>

          <div className="card">
            <span>Categories</span>
            <strong>{summary?.total_categories ?? "—"}</strong>
            <small>ML labels</small>
          </div>

          <div className="card">
            <span>Fulltext</span>
            <strong>{summary?.fulltext_articles ?? "—"}</strong>
            <small>{fulltextRate}% of data</small>
          </div>

          <div className="card">
            <span>RSS Fallback</span>
            <strong>{summary?.rss_fallback_articles ?? "—"}</strong>
            <small>{fallbackRate}% of data</small>
          </div>

          <div className="card">
            <span>Last Crawl</span>
            <strong className="date-value">{lastCrawl}</strong>
            <small>Latest crawl timestamp</small>
          </div>
        </section>

        <section className="panel">
          <div className="panel-title">
            <div>
              <div className="eyebrow">TIME SERIES</div>
              <h2>News Trend by Category</h2>
            </div>
            <span>
              {trend.reduce((sum, item) => sum + item.total, 0)} articles
            </span>
          </div>

          <div className="chart">
            {trendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={360}>
                <BarChart data={trendData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                  />
                  <XAxis dataKey="day" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Legend />
                  {trendCategories.map((name, index) => (
                    <Bar
                      key={name}
                      dataKey={name}
                      stackId="a"
                      fill={
                        chartColors[index % chartColors.length]
                      }
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty">No data for this filter.</div>
            )}
          </div>
        </section>

        <section className="three-columns">
          <div className="panel">
            <div className="panel-title">
              <div>
                <div className="eyebrow">ML OUTCOME</div>
                <h2>Category Distribution</h2>
              </div>
            </div>

            <div className="chart compact">
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={categories}
                    dataKey="total"
                    nameKey="category"
                    innerRadius={55}
                    outerRadius={90}
                  >
                    {categories.map((item, index) => (
                      <Cell
                        key={item.category}
                        fill={
                          chartColors[
                            index % chartColors.length
                          ]
                        }
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="list">
              {categories.slice(0, 7).map((item) => (
                <div key={item.category} className="list-row">
                  <span>{item.category}</span>
                  <strong>
                    {item.total} ({item.percentage}%)
                  </strong>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="panel-title">
              <div>
                <div className="eyebrow">DATA QUALITY</div>
                <h2>Content Quality</h2>
              </div>
            </div>

            <div className="chart compact">
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={qualityData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={58}
                    outerRadius={90}
                  >
                    <Cell fill="#66785A" />
                    <Cell fill="#9B5C45" />
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="quality">
              <div>
                <strong>{summary?.fulltext_articles ?? 0}</strong>
                <span>Fulltext</span>
              </div>
              <div>
                <strong>
                  {summary?.rss_fallback_articles ?? 0}
                </strong>
                <span>Fallback</span>
              </div>
            </div>
          </div>

          <div className="panel">
            <div className="panel-title">
              <div>
                <div className="eyebrow">OPERATIONS</div>
                <h2>Pipeline Snapshot</h2>
              </div>
            </div>

                        <div className="ops">
              <div>
                <span>API</span>
                <strong className="ok">? Connected</strong>
              </div>
              <div>
                <span>Database</span>
                <strong className="ok">
                  {summary ? "? Connected" : "? Checking..."}
                </strong>
              </div>
              <div>
                <span>Crawler</span>
                <strong
                  className={
                    crawlerStatus?.status === "running"
                      ? "running"
                      : crawlerStatus?.last_run_status === "error"
                        ? "error"
                        : "ok"
                  }
                >
                  {crawlerStatus?.status === "running"
                    ? "? Running"
                    : crawlerStatus?.last_run_status === "error"
                      ? "? Error"
                      : "? Idle"}
                </strong>
              </div>
              <div>
                <span>ML Model</span>
                <strong className="ok">? Loaded</strong>
              </div>
              <div>
                <span>Source</span>
                <strong>
                  {summary?.total_sources ?? 0} source
                </strong>
              </div>
              <div>
                <span>Classifier</span>
                <strong>LinearSVC</strong>
              </div>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-title">
            <div>
              <div className="eyebrow">RAW DATA</div>
              <h2>Recent Classified News</h2>
            </div>
            <span>{recent.length} rows</span>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Category</th>
                  <th>Content</th>
                  <th>Score</th>
                  <th>Published</th>
                  <th></th>
                </tr>
              </thead>

              <tbody>
                {recent.map((item) => (
                  <tr key={item.id}>
                    <td className="title">
                      {item.title}
                    </td>

                    <td>
                      <span className="tag">
                        {item.category}
                      </span>
                    </td>

                    <td>
                      <span className="tag">
                        {item.content_source === "fulltext"
                          ? "Fulltext"
                          : "RSS fallback"}
                      </span>
                    </td>

                    <td className="score">
                      {item.decision_score.toFixed(3)}
                    </td>

                    <td>
                      {item.published_at
                        ? new Date(
                            item.published_at,
                          ).toLocaleDateString("vi-VN")
                        : "—"}
                    </td>

                    <td>
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Open ↗
                      </a>
                    </td>
                  </tr>
                ))}

                {!recent.length && (
                  <tr>
                    <td colSpan={6}>
                      <div className="empty">
                        No articles found.
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;








