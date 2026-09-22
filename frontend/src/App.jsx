import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  getCategories,
  getCrawlerSources,
  getCrawlerStatus,
  getDaily,
  getHotTopics,
  getIntelligenceTrends,
  getKeywords,
  getRecent,
  getSummary,
  getTrendByCategory,
  runCrawler,
} from "./services/api";

import "./App.css";

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("vi-VN");
}

function formatDateTime(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("vi-VN");
}

function formatNumber(value) {
  if (typeof value !== "number") return "—";

  return value.toLocaleString("vi-VN");
}

function formatScore(value) {
  if (typeof value !== "number") return "—";

  return value.toFixed(3);
}

function getTopicKeywords(topic) {
  if (!Array.isArray(topic?.keywords)) {
    return "—";
  }

  return topic.keywords
    .map((item) => {
      if (typeof item === "string") {
        return item;
      }

      return item?.display_keyword || item?.keyword || "";
    })
    .filter(Boolean)
    .join(", ");
}

function App() {
  const [summary, setSummary] = useState(null);
  const [categories, setCategories] = useState([]);
  const [daily, setDaily] = useState([]);
  const [trend, setTrend] = useState([]);
  const [recent, setRecent] = useState([]);

  const [keywords, setKeywords] = useState([]);
  const [intelligenceTrends, setIntelligenceTrends] = useState([]);
  const [hotTopics, setHotTopics] = useState([]);

  // =========================
  // Data Scope
  // =========================

  const [appliedScope, setAppliedScope] = useState({
    source: "",
    category: "",
    from_date: "",
    to_date: "",
  });

  const [scopeDraft, setScopeDraft] = useState({
    source: "",
    category: "",
    from_date: "",
    to_date: "",
  });

  const [availableCategories, setAvailableCategories] = useState([]);

  // =========================
  // Data Collection
  // =========================

  const [crawlerSources, setCrawlerSources] = useState([]);
  const [selectedCollectionSources, setSelectedCollectionSources] =
    useState([]);

  const [collectionFromDate, setCollectionFromDate] = useState("");
  const [collectionToDate, setCollectionToDate] = useState("");

  const [crawlerStatus, setCrawlerStatus] = useState(null);
  const [collectionBusy, setCollectionBusy] = useState(false);
  const [collectionError, setCollectionError] = useState("");
  const [dataControlOpen, setDataControlOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("overview");

  const [newsSearch, setNewsSearch] = useState("");
  const [newsSourceFilter, setNewsSourceFilter] = useState("");
  const [newsCategoryFilter, setNewsCategoryFilter] = useState("");
  const [newsContentFilter, setNewsContentFilter] = useState("");
  const [newsPage, setNewsPage] = useState(1);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const NEWS_PAGE_SIZE = 10;

  const [trendMeta, setTrendMeta] = useState({
    recent_days: 0,
    previous_days: 0,
    anchor_date: null,
  });

  const [hotTopicMeta, setHotTopicMeta] = useState({
    recent_days: 0,
    anchor_date: null,
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard(params = appliedScope) {
    try {
      setLoading(true);
      setError("");

      const [
        summaryData,
        categoriesData,
        dailyData,
        trendData,
        recentData,
        keywordsData,
        intelligenceTrendData,
        hotTopicsData,
      ] = await Promise.all([
        getSummary(params),
        getCategories(params),
        getDaily(params),
        getTrendByCategory(params),
        getRecent(30, params),
        getKeywords(params),
        getIntelligenceTrends(params),
        getHotTopics(params),
      ]);

      setSummary(summaryData);
      setCategories(categoriesData.items || []);
      setDaily(dailyData.items || []);
      setTrend(trendData.items || []);
      setRecent(recentData.items || []);

      setKeywords(keywordsData.items || []);
      setIntelligenceTrends(intelligenceTrendData.items || []);
      setHotTopics(hotTopicsData.items || []);

      setTrendMeta({
        recent_days: intelligenceTrendData.recent_days || 0,
        previous_days: intelligenceTrendData.previous_days || 0,
        anchor_date: intelligenceTrendData.anchor_date || null,
      });

      setHotTopicMeta({
        recent_days: hotTopicsData.recent_days || 0,
        anchor_date: hotTopicsData.anchor_date || null,
      });
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Không thể tải dữ liệu từ máy chủ."
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadControlData() {
    try {
      const [
        crawlerSourcesData,
        categoriesData,
        crawlerStatusData,
      ] = await Promise.all([
        getCrawlerSources(),
        getCategories(),
        getCrawlerStatus(),
      ]);

      const sources = crawlerSourcesData.items || [];

      setCrawlerSources(sources);

      setAvailableCategories(
        categoriesData.items || []
      );

      setCrawlerStatus(crawlerStatusData);

      setSelectedCollectionSources(
        sources
          .filter((item) => item.enabled)
          .map((item) => item.name)
      );
    } catch (err) {
      setCollectionError(
        err instanceof Error
          ? err.message
          : "Không thể tải cấu hình crawler."
      );
    }
  }

  function validateDateRange(
    fromDate,
    toDate
  ) {
    if (
      fromDate &&
      toDate &&
      fromDate > toDate
    ) {
      return "Ngày bắt đầu không được lớn hơn ngày kết thúc.";
    }

    return "";
  }

  async function handleApplyScope() {
    const validationError =
      validateDateRange(
        scopeDraft.from_date,
        scopeDraft.to_date
      );

    if (validationError) {
      setError(validationError);
      return;
    }

    setError("");

    const nextScope = {
      source: scopeDraft.source,
      category: scopeDraft.category,
      from_date: scopeDraft.from_date,
      to_date: scopeDraft.to_date,
    };

    setAppliedScope(nextScope);
    resetNewsExplorer();

    await loadDashboard(nextScope);
  }

  async function handleResetScope() {
    const emptyScope = {
      source: "",
      category: "",
      from_date: "",
      to_date: "",
    };

    setScopeDraft(emptyScope);
    setAppliedScope(emptyScope);
    setError("");
    resetNewsExplorer();

    await loadDashboard(emptyScope);
  }

  function toggleCollectionSource(
    sourceName
  ) {
    setSelectedCollectionSources(
      (current) => {
        if (current.includes(sourceName)) {
          return current.filter(
            (item) => item !== sourceName
          );
        }

        return [
          ...current,
          sourceName,
        ];
      }
    );
  }

  async function handleCollectData() {
    const validationError =
      validateDateRange(
        collectionFromDate,
        collectionToDate
      );

    if (validationError) {
      setCollectionError(validationError);
      return;
    }

    if (
      selectedCollectionSources.length === 0
    ) {
      setCollectionError(
        "Vui lòng chọn ít nhất một nguồn dữ liệu."
      );
      return;
    }

    try {
      setCollectionBusy(true);
      setCollectionError("");

      const result = await runCrawler({
        sources: selectedCollectionSources,
        fromDate: collectionFromDate,
        toDate: collectionToDate,
      });

      setCrawlerStatus(
        (current) => ({
          ...(current || {}),
          status: "running",
          last_run_status: "running",
          last_run_source: "manual",
          last_options: result?.options || {
            sources:
              selectedCollectionSources,
            from_date:
              collectionFromDate || null,
            to_date:
              collectionToDate || null,
          },
        })
      );

      let currentStatus =
        await getCrawlerStatus();

      setCrawlerStatus(currentStatus);

      for (
        let i = 0;
        i < 120;
        i += 1
      ) {
        if (
          currentStatus?.status !== "running"
        ) {
          break;
        }

        await new Promise(
          (resolve) =>
            setTimeout(resolve, 1000)
        );

        currentStatus =
          await getCrawlerStatus();

        setCrawlerStatus(
          currentStatus
        );
      }

      if (
        currentStatus?.last_run_status ===
        "error"
      ) {
        setCollectionError(
          currentStatus.last_error ||
            "Crawler hoàn tất với lỗi."
        );
      }

      await loadDashboard(
        appliedScope
      );
    } catch (err) {
      setCollectionError(
        err instanceof Error
          ? err.message
          : "Không thể kích hoạt crawler."
      );
    } finally {
      setCollectionBusy(false);
    }
  }

  useEffect(() => {
    loadDashboard();
    loadControlData();
  }, []);

  useEffect(() => {
    const sectionIds = [
      "overview",
      "news",
      "intelligence",
      "analytics",
      "data",
    ];

    function updateActiveSection() {
      const offset = 180;
      let current = "overview";

      for (const sectionId of sectionIds) {
        const element = document.getElementById(sectionId);
        if (element && element.getBoundingClientRect().top <= offset) {
          current = sectionId;
        }
      }

      setActiveSection(current);
    }

    window.addEventListener("scroll", updateActiveSection, { passive: true });
    updateActiveSection();

    return () => {
      window.removeEventListener("scroll", updateActiveSection);
    };
  }, []);

  function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (!element) return;

    element.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  function exploreNews(query) {
    const value = String(query || "").trim();
    if (!value) return;

    setNewsSearch(value);
    setNewsSourceFilter("");
    setNewsCategoryFilter("");
    setNewsContentFilter("");
    setNewsPage(1);
    scrollToSection("news");
  }

  function exploreCategory(category) {
    if (!category) return;

    setNewsSearch("");
    setNewsSourceFilter("");
    setNewsCategoryFilter(category);
    setNewsContentFilter("");
    setNewsPage(1);
    scrollToSection("news");
  }

  const trendData = trend.map((item) => ({
    day: item.day,
    ...item.categories,
  }));

  const trendCategories = [
    ...new Set(
      trend.flatMap((item) => Object.keys(item.categories || {}))
    ),
  ];

  const filteredRecent = recent.filter((article) => {
    const query = newsSearch.trim().toLocaleLowerCase("vi-VN");
    const matchesSearch =
      !query ||
      [article.title, article.category, article.source]
        .filter(Boolean)
        .some((value) =>
          String(value).toLocaleLowerCase("vi-VN").includes(query)
        );

    const matchesSource =
      !newsSourceFilter || article.source === newsSourceFilter;
    const matchesCategory =
      !newsCategoryFilter || article.category === newsCategoryFilter;
    const matchesContent =
      !newsContentFilter || article.content_source === newsContentFilter;

    return matchesSearch && matchesSource && matchesCategory && matchesContent;
  });

  useEffect(() => {
    setNewsPage(1);
  }, [newsSearch, newsSourceFilter, newsCategoryFilter, newsContentFilter]);

  const newsPageCount = Math.max(
    1,
    Math.ceil(filteredRecent.length / NEWS_PAGE_SIZE)
  );
  const safeNewsPage = Math.min(newsPage, newsPageCount);
  const paginatedRecent = filteredRecent.slice(
    (safeNewsPage - 1) * NEWS_PAGE_SIZE,
    safeNewsPage * NEWS_PAGE_SIZE
  );
  const newsStart = filteredRecent.length === 0
    ? 0
    : (safeNewsPage - 1) * NEWS_PAGE_SIZE + 1;
  const newsEnd = Math.min(
    safeNewsPage * NEWS_PAGE_SIZE,
    filteredRecent.length
  );

  function resetNewsExplorer() {
    setNewsSearch("");
    setNewsSourceFilter("");
    setNewsCategoryFilter("");
    setNewsContentFilter("");
    setNewsPage(1);
  }

  function openArticle(article) {
    setSelectedArticle(article);
  }

  function closeArticle() {
    setSelectedArticle(null);
  }

  return (
    <div className="app">
      <header className="site-header">
        <div className="header-inner">
          <div>
            <h1>Vietnamese News Classification</h1>
            <p>News Classification & Trend Analytics Platform</p>
          </div>

          <div className="header-status">
            Hệ thống phân tích tin tức
          </div>
        </div>
      </header>

      <div className="dashboard-shell">
        <aside className="catalog">
          <div className="catalog-title">CATALOG</div>

          <nav className="catalog-nav" aria-label="Điều hướng dashboard">
            <button type="button" className={`catalog-link ${activeSection === "overview" ? "is-active" : ""}`} onClick={() => scrollToSection("overview")}>
              <span className="catalog-index">01</span>
              <span>Tổng quan</span>
            </button>
            <button type="button" className={`catalog-link ${activeSection === "news" ? "is-active" : ""}`} onClick={() => scrollToSection("news")}>
              <span className="catalog-index">02</span>
              <span>Tin tức</span>
            </button>
            <button type="button" className={`catalog-link ${activeSection === "intelligence" ? "is-active" : ""}`} onClick={() => scrollToSection("intelligence")}>
              <span className="catalog-index">03</span>
              <span>Intelligence</span>
            </button>
            <button type="button" className={`catalog-link ${activeSection === "analytics" ? "is-active" : ""}`} onClick={() => scrollToSection("analytics")}>
              <span className="catalog-index">04</span>
              <span>Analytics</span>
            </button>
            <div className="catalog-divider" />
            <div className="catalog-group-label">DATA CONTROL</div>
            <button type="button" className={`catalog-link ${activeSection === "data" ? "is-active" : ""}`} onClick={() => scrollToSection("data")}>
              <span className="catalog-index">05</span>
              <span>Dữ liệu</span>
            </button>
          </nav>

          <button type="button" className="catalog-top" onClick={() => scrollToSection("overview")}>
            ↑ Về đầu trang
          </button>
        </aside>

        <main className="main-content">
        <section id="overview" className="page-heading dashboard-anchor">
          <h2>Tổng quan</h2>
          <p>
            Thống kê và phân tích dữ liệu tin tức được thu thập từ hệ thống.
          </p>
        </section>

        <div className="overview-toolbar">
          <div className="scope-readout">
            <span>PHẠM VI HIỆN TẠI</span>
            <strong>
              {appliedScope.source || "Tất cả nguồn"}
              {" · "}
              {appliedScope.category || "Tất cả danh mục"}
              {" · "}
              {appliedScope.from_date || "Không giới hạn"}
              {" → "}
              {appliedScope.to_date || "Không giới hạn"}
            </strong>
          </div>
          <div className="overview-toolbar-actions">
            <button type="button" className="toolbar-button" onClick={() => scrollToSection("news")}>
              News Explorer
            </button>
            <button type="button" className="toolbar-button" onClick={() => scrollToSection("intelligence")}>
              Intelligence
            </button>
            <button type="button" className="toolbar-button secondary" onClick={() => {
              setDataControlOpen(true);
              scrollToSection("data");
            }}>
              Data Control
            </button>
          </div>
        </div>

        {error && (
          <section className="error-box">
            <strong>Lỗi kết nối:</strong> {error}
            <button type="button" onClick={loadDashboard}>
              Thử lại
            </button>
          </section>
        )}

        {loading ? (
          <section className="loading-box">
            Đang tải dữ liệu...
          </section>
        ) : (
          <>
            <section className="summary-grid">
              <div className="summary-card">
                <span className="summary-label">Tổng số bài viết</span>
                <strong>{summary?.total_articles ?? 0}</strong>
              </div>

              <div className="summary-card">
                <span className="summary-label">Số danh mục</span>
                <strong>{summary?.total_categories ?? 0}</strong>
              </div>

              <div className="summary-card">
                <span className="summary-label">Số nguồn</span>
                <strong>{summary?.total_sources ?? 0}</strong>
              </div>

              <div className="summary-card">
                <span className="summary-label">Bài có nội dung đầy đủ</span>
                <strong>{summary?.fulltext_articles ?? 0}</strong>
              </div>
            </section>

            <section className="content-section">
              <div className="section-header">
                <h3>Số lượng bài viết theo ngày</h3>
              </div>

              <div className="chart-container">
                <ResponsiveContainer width="100%" height={330}>
                  <LineChart
                    data={daily}
                    margin={{
                      top: 15,
                      right: 25,
                      left: 5,
                      bottom: 10,
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />

                    <XAxis
                      dataKey="day"
                      tickFormatter={formatDate}
                    />

                    <YAxis allowDecimals={false} />

                    <Tooltip
                      labelFormatter={(value) =>
                        `Ngày: ${formatDate(value)}`
                      }
                    />

                    <Line
                      type="monotone"
                      dataKey="total"
                      name="Số bài viết"
                      stroke="#17365d"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section id="news" className="content-section dashboard-anchor">
              <div className="section-header news-explorer-header">
                <div>
                  <h3>News Explorer</h3>
                  <p className="section-note">
                    Tra cứu nhanh trong tập bài viết gần nhất của phạm vi dữ liệu hiện tại.
                  </p>
                </div>
                <span className="explorer-count">
                  {newsStart}–{newsEnd} / {filteredRecent.length} bài
                </span>
              </div>

              <div className="news-explorer-controls">
                <div className="explorer-field explorer-search">
                  <label htmlFor="news-search">Tìm kiếm</label>
                  <input
                    id="news-search"
                    type="search"
                    placeholder="Tìm theo tiêu đề, nguồn hoặc danh mục..."
                    value={newsSearch}
                    onChange={(event) => setNewsSearch(event.target.value)}
                  />
                </div>

                <div className="explorer-field">
                  <label htmlFor="news-source-filter">Nguồn</label>
                  <select
                    id="news-source-filter"
                    value={newsSourceFilter}
                    onChange={(event) => setNewsSourceFilter(event.target.value)}
                  >
                    <option value="">Tất cả nguồn</option>
                    {crawlerSources
                      .filter((item) => item.enabled)
                      .map((item) => (
                        <option key={item.source} value={item.source}>
                          {item.source}
                        </option>
                      ))}
                  </select>
                </div>

                <div className="explorer-field">
                  <label htmlFor="news-category-filter">Danh mục</label>
                  <select
                    id="news-category-filter"
                    value={newsCategoryFilter}
                    onChange={(event) => setNewsCategoryFilter(event.target.value)}
                  >
                    <option value="">Tất cả danh mục</option>
                    {availableCategories.map((item) => (
                      <option key={item.category} value={item.category}>
                        {item.category}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="explorer-field">
                  <label htmlFor="news-content-filter">Loại nội dung</label>
                  <select
                    id="news-content-filter"
                    value={newsContentFilter}
                    onChange={(event) => setNewsContentFilter(event.target.value)}
                  >
                    <option value="">Tất cả</option>
                    <option value="fulltext">Fulltext</option>
                    <option value="rss_fallback">RSS fallback</option>
                  </select>
                </div>

                <button
                  type="button"
                  className="control-button secondary explorer-reset"
                  onClick={resetNewsExplorer}
                >
                  Xóa lọc
                </button>
              </div>

              <div className="table-scroll recent-table-scroll">
                <table className="data-table recent-table">
                  <thead>
                    <tr>
                      <th>Tiêu đề</th>
                      <th>Danh mục</th>
                      <th>Nguồn</th>
                      <th>Loại nội dung</th>
                      <th>Decision Score</th>
                      <th>Thời gian</th>
                    </tr>
                  </thead>

                  <tbody>
                    {paginatedRecent.map((article) => (
                      <tr
                        key={article.id}
                        className="interactive-row"
                        onClick={() => openArticle(article)}
                      >
                        <td>
                          <button
                            type="button"
                            className="article-title-button"
                            onClick={(event) => {
                              event.stopPropagation();
                              openArticle(article);
                            }}
                          >
                            {article.title || "—"}
                          </button>
                        </td>
                        <td>{article.category || "—"}</td>
                        <td>{article.source || "—"}</td>
                        <td>{article.content_source || "—"}</td>
                        <td>
                          {typeof article.decision_score === "number"
                            ? article.decision_score.toFixed(4)
                            : "—"}
                        </td>
                        <td>
                          {formatDateTime(
                            article.published_at || article.crawled_at
                          )}
                        </td>
                      </tr>
                    ))}

                    {filteredRecent.length === 0 && (
                      <tr>
                        <td colSpan={6}>Không tìm thấy bài viết phù hợp.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="section-footer-row explorer-footer">
                <div className="section-footer-note">
                  Bộ lọc phạm vi dữ liệu được áp dụng trước; Explorer hiển thị danh sách bài viết gần nhất trong phạm vi đó. Bấm vào tiêu đề để xem chi tiết.
                </div>
                <div className="explorer-pagination" aria-label="Phân trang News Explorer">
                  <button
                    type="button"
                    className="pagination-button"
                    onClick={() => setNewsPage((page) => Math.max(1, page - 1))}
                    disabled={safeNewsPage <= 1}
                  >
                    ←
                  </button>
                  <span>Trang {safeNewsPage} / {newsPageCount}</span>
                  <button
                    type="button"
                    className="pagination-button"
                    onClick={() => setNewsPage((page) => Math.min(newsPageCount, page + 1))}
                    disabled={safeNewsPage >= newsPageCount}
                  >
                    →
                  </button>
                </div>
              </div>
              <div className="explorer-bottom-actions">
                <button type="button" className="section-jump" onClick={() => scrollToSection("overview")}>↑ Tổng quan</button>
              </div>
            </section>
            <section id="intelligence" className="content-section intelligence-section dashboard-anchor">
              <div className="section-header">
                <div>
                  <h3>News Intelligence</h3>
                  <p className="section-note">
                    Phân tích từ khóa, động lượng xu hướng và các cụm chủ đề
                    được hình thành từ dữ liệu tin tức.
                  </p>
                </div>
              </div>

              <div className="two-column">
                <div className="content-section nested-section">
                  <div className="section-header">
                    <h3>Top Keywords</h3>
                  </div>

                  <div className="table-scroll">
                    <table className="data-table intelligence-table">
                      <thead>
                        <tr>
                          <th>Từ khóa</th>
                          <th>Bài viết</th>
                          <th>Tần suất</th>
                          <th>Strength</th>
                        </tr>
                      </thead>

                      <tbody>
                        {keywords.slice(0, 10).map((item) => (
                          <tr key={item.keyword} onClick={() => exploreNews(item.display_keyword || item.keyword)} className="interactive-row">
                            <td>
                              <button type="button" className="table-link" onClick={() => exploreNews(item.display_keyword || item.keyword)}>
                                {item.display_keyword || item.keyword}
                              </button>
                            </td>
                            <td>{formatNumber(item.article_count)}</td>
                            <td>{formatNumber(item.total_frequency)}</td>
                            <td>{formatScore(item.strength)}</td>
                          </tr>
                        ))}

                        {keywords.length === 0 && (
                          <tr>
                            <td colSpan={4}>Chưa có dữ liệu từ khóa.</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="content-section nested-section">
                  <div className="section-header">
                    <div>
                      <h3>Trending Keywords</h3>
                      <p className="section-note">
                        {trendMeta.recent_days} ngày gần nhất so với{" "}
                        {trendMeta.previous_days} ngày trước đó
                        {trendMeta.anchor_date
                          ? ` · cập nhật ${formatDate(
                              trendMeta.anchor_date
                            )}`
                          : ""}
                      </p>
                    </div>
                  </div>

                  <div className="table-scroll">
                    <table className="data-table intelligence-table">
                      <thead>
                        <tr>
                          <th>Từ khóa</th>
                          <th>Bài viết</th>
                          <th>Tần suất</th>
                          <th>Strength</th>
                          <th>Trend</th>
                        </tr>
                      </thead>

                      <tbody>
                        {intelligenceTrends.slice(0, 10).map((item) => (
                          <tr key={item.keyword} onClick={() => exploreNews(item.display_keyword || item.keyword)} className="interactive-row">
                            <td>
                              <button type="button" className="table-link" onClick={() => exploreNews(item.display_keyword || item.keyword)}>
                                {item.display_keyword || item.keyword}
                              </button>
                            </td>

                            <td>
                              {formatNumber(item.total_articles)}
                            </td>

                            <td>
                              {formatNumber(item.total_frequency)}
                            </td>

                            <td>
                              {formatScore(item.keyword_strength)}
                            </td>

                            <td>
                              <span
                                className={
                                  item.growth_label === "NEW"
                                    ? "trend-badge trend-new"
                                    : "trend-badge"
                                }
                              >
                                {item.growth_label || "—"}
                              </span>
                              <span className="trend-score">
                                {formatScore(item.trend_score)}
                              </span>
                            </td>
                          </tr>
                        ))}

                        {intelligenceTrends.length === 0 && (
                          <tr>
                            <td colSpan={5}>
                              Chưa có dữ liệu xu hướng.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              <div className="content-section nested-section">
                <div className="section-header">
                  <div>
                    <h3>Hot Topic Candidates</h3>
                    <p className="section-note">
                      Các cụm từ khóa có liên hệ trong cùng tập dữ liệu;
                      đây là topic candidates, không phải chủ đề được sinh
                      bởi mô hình ngôn ngữ.
                      {hotTopicMeta.anchor_date
                        ? ` · cập nhật ${formatDate(
                            hotTopicMeta.anchor_date
                          )}`
                        : ""}
                    </p>
                  </div>
                </div>

                <div className="hot-topic-grid">
                  {hotTopics.map((topic, index) => (
                    <article
                      className="hot-topic-card interactive-card"
                      key={`${topic.label}-${index}`}
                      onClick={() => exploreNews(topic.label)}
                      tabIndex={0}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          exploreNews(topic.label);
                        }
                      }}
                    >
                      <div className="hot-topic-header">
                        <span className="topic-index">
                          {String(index + 1).padStart(2, "0")}
                        </span>

                        <h4>{topic.label || "Chưa xác định"}</h4>
                      </div>

                      <p className="topic-keywords">
                        {getTopicKeywords(topic)}
                      </p>

                      <div className="topic-action">Xem các bài liên quan →</div>

                      <div className="topic-meta">
                        <span>
                          Bài viết:{" "}
                          <strong>
                            {formatNumber(
                              topic.article_volume ??
                                topic.total_articles ??
                                0
                            )}
                          </strong>
                        </span>

                        <span>
                          Keywords:{" "}
                          <strong>
                            {formatNumber(topic.keyword_count)}
                          </strong>
                        </span>

                        <span>
                          Trend:{" "}
                          <strong>
                            {formatScore(topic.max_trend_score)}
                          </strong>
                        </span>
                      </div>
                    </article>
                  ))}

                  {hotTopics.length === 0 && (
                    <div className="empty-state">
                      Chưa hình thành topic candidate từ dữ liệu hiện tại.
                    </div>
                  )}
                </div>
              </div>
            </section>

            <section id="analytics" className="two-column dashboard-anchor">
              <div className="content-section">
                <div className="section-header">
                  <h3>Phân bố theo danh mục</h3>
                </div>

                <div className="category-table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Danh mục</th>
                        <th>Số bài</th>
                        <th>Tỷ lệ</th>
                      </tr>
                    </thead>

                    <tbody>
                      {categories.map((item) => (
                        <tr key={item.category} onClick={() => exploreCategory(item.category)} className="interactive-row">
                          <td>
                            <button type="button" className="table-link" onClick={() => exploreCategory(item.category)}>
                              {item.category}
                            </button>
                          </td>
                          <td>{formatNumber(item.total)}</td>
                          <td>
                            {typeof item.percentage === "number"
                              ? `${item.percentage.toFixed(2)}%`
                              : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="content-section">
                <div className="section-header">
                  <h3>Nguồn nội dung</h3>
                </div>

                <div className="source-summary">
                  <div>
                    <span>Fulltext</span>
                    <strong>
                      {summary?.fulltext_articles ?? 0}
                    </strong>
                  </div>

                  <div>
                    <span>RSS fallback</span>
                    <strong>
                      {summary?.rss_fallback_articles ?? 0}
                    </strong>
                  </div>
                </div>

                <div className="latest-info">
                  <span>Cập nhật dữ liệu gần nhất</span>
                  <strong>
                    {formatDateTime(summary?.latest_crawled_at)}
                  </strong>
                </div>
              </div>
            </section>

            <section id="analytics-trend" className="content-section dashboard-anchor">
              <div className="section-header">
                <h3>Xu hướng theo danh mục</h3>
              </div>

              <div className="chart-container">
                <ResponsiveContainer width="100%" height={380}>
                  <LineChart
                    data={trendData}
                    margin={{
                      top: 15,
                      right: 25,
                      left: 5,
                      bottom: 10,
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />

                    <XAxis
                      dataKey="day"
                      tickFormatter={formatDate}
                    />

                    <YAxis allowDecimals={false} />

                    <Tooltip
                      labelFormatter={(value) =>
                        `Ngày: ${formatDate(value)}`
                      }
                    />

                    <Legend />

                    {trendCategories.map((category, index) => (
                      <Line
                        key={category}
                        type="monotone"
                        dataKey={category}
                        name={category}
                        stroke={
                          [
                            "#17365d",
                            "#7f6000",
                            "#38761d",
                            "#741b47",
                            "#134f5c",
                            "#5b0f00",
                            "#351c75",
                            "#783f04",
                            "#274e13",
                            "#0b5394",
                            "#660000",
                            "#20124d",
                            "#444444",
                          ][index % 13]
                        }
                        strokeWidth={1.8}
                        dot={{ r: 2 }}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>

          </>
        )}

        <section id="data" className="data-control-section dashboard-anchor">
          <button
            type="button"
            className="data-control-toggle"
            onClick={() => setDataControlOpen((current) => !current)}
            aria-expanded={dataControlOpen}
            aria-controls="data-control-body"
          >
            <span>
              <strong>Data Control</strong>
              <small>Phạm vi dữ liệu và thu thập dữ liệu RSS</small>
            </span>
            <span className="toggle-mark" aria-hidden="true">
              {dataControlOpen ? "−" : "+"}
            </span>
          </button>

          {dataControlOpen && (
            <div id="data-control-body" className="data-control-body">
              <div className="data-control-grid">

            {/* =========================
                DATA SCOPE
                ========================= */}

            <div className="control-panel">
              <div className="control-panel-header">
                <h3>Data Scope</h3>
                <p>
                  Phạm vi dữ liệu dùng cho
                  Dashboard và News Intelligence.
                </p>
              </div>

              <div className="control-form">

                <div className="control-field">
                  <label htmlFor="scope-source">
                    Source
                  </label>

                  <select
                    id="scope-source"
                    value={scopeDraft.source}
                    onChange={(event) =>
                      setScopeDraft(
                        (current) => ({
                          ...current,
                          source:
                            event.target.value,
                        })
                      )
                    }
                  >
                    <option value="">
                      Tất cả nguồn
                    </option>

                    {crawlerSources
                      .filter(
                        (item) =>
                          item.enabled
                      )
                      .map((item) => (
                        <option
                          key={item.name}
                          value={item.source}
                        >
                          {item.source}
                        </option>
                      ))}
                  </select>
                </div>

                <div className="control-field">
                  <label htmlFor="scope-category">
                    Category
                  </label>

                  <select
                    id="scope-category"
                    value={scopeDraft.category}
                    onChange={(event) =>
                      setScopeDraft(
                        (current) => ({
                          ...current,
                          category:
                            event.target.value,
                        })
                      )
                    }
                  >
                    <option value="">
                      Tất cả danh mục
                    </option>

                    {availableCategories.map(
                      (item) => (
                        <option
                          key={
                            item.category
                          }
                          value={
                            item.category
                          }
                        >
                          {item.category}
                        </option>
                      )
                    )}
                  </select>
                </div>

                <div className="control-field">
                  <label htmlFor="scope-from-date">
                    From date
                  </label>

                  <input
                    id="scope-from-date"
                    type="date"
                    value={
                      scopeDraft.from_date
                    }
                    onChange={(event) =>
                      setScopeDraft(
                        (current) => ({
                          ...current,
                          from_date:
                            event.target.value,
                        })
                      )
                    }
                  />
                </div>

                <div className="control-field">
                  <label htmlFor="scope-to-date">
                    To date
                  </label>

                  <input
                    id="scope-to-date"
                    type="date"
                    value={
                      scopeDraft.to_date
                    }
                    onChange={(event) =>
                      setScopeDraft(
                        (current) => ({
                          ...current,
                          to_date:
                            event.target.value,
                        })
                      )
                    }
                  />
                </div>

                <div className="control-actions">
                  <button
                    type="button"
                    className="control-button"
                    onClick={
                      handleApplyScope
                    }
                  >
                    Áp dụng bộ lọc
                  </button>

                  <button
                    type="button"
                    className="control-button secondary"
                    onClick={
                      handleResetScope
                    }
                  >
                    Đặt lại
                  </button>
                </div>

                <div className="scope-summary">
                  <div className="scope-summary-title">
                    Applied Scope
                  </div>

                  <div className="scope-summary-text">
                    Nguồn:{" "}
                    {appliedScope.source ||
                      "Tất cả nguồn"}
                    {" · "}
                    Danh mục:{" "}
                    {appliedScope.category ||
                      "Tất cả danh mục"}
                    {" · "}
                    Thời gian:{" "}
                    {appliedScope.from_date ||
                      "Không giới hạn"}
                    {" → "}
                    {appliedScope.to_date ||
                      "Không giới hạn"}
                  </div>
                </div>

              </div>
            </div>

            {/* =========================
                DATA COLLECTION
                ========================= */}

            <div className="control-panel">
              <div className="control-panel-header">
                <h3>Data Collection</h3>
                <p>
                  Thu thập dữ liệu mới từ các
                  RSS source đã cấu hình.
                </p>
              </div>

              <div className="control-form">

                <div className="control-field">
                  <label>
                    Sources
                  </label>

                  <div className="source-check-list">
                    {crawlerSources
                      .filter(
                        (item) =>
                          item.enabled
                      )
                      .map((item) => (
                        <label
                          className="source-check-item"
                          key={item.name}
                        >
                          <input
                            type="checkbox"
                            checked={selectedCollectionSources.includes(
                              item.name
                            )}
                            onChange={() =>
                              toggleCollectionSource(
                                item.name
                              )
                            }
                          />

                          <span>
                            {item.source}
                          </span>
                        </label>
                      ))}
                  </div>
                </div>

                <div className="control-field">
                  <label htmlFor="collection-from-date">
                    From date
                  </label>

                  <input
                    id="collection-from-date"
                    type="date"
                    value={
                      collectionFromDate
                    }
                    onChange={(event) =>
                      setCollectionFromDate(
                        event.target.value
                      )
                    }
                  />
                </div>

                <div className="control-field">
                  <label htmlFor="collection-to-date">
                    To date
                  </label>

                  <input
                    id="collection-to-date"
                    type="date"
                    value={
                      collectionToDate
                    }
                    onChange={(event) =>
                      setCollectionToDate(
                        event.target.value
                      )
                    }
                  />
                </div>

                {collectionError && (
                  <div className="validation-message">
                    {collectionError}
                  </div>
                )}

                <div className="control-actions">
                  <button
                    type="button"
                    className="control-button"
                    onClick={
                      handleCollectData
                    }
                    disabled={
                      collectionBusy ||
                      selectedCollectionSources.length ===
                        0
                    }
                  >
                    {collectionBusy
                      ? "Đang thu thập..."
                      : "Thu thập dữ liệu"}
                  </button>
                </div>

                <div className="collection-status">
                  <div className="collection-status-grid">

                    <div className="status-item">
                      <span>Status</span>
                      <strong
                        className={
                          crawlerStatus?.status ===
                          "running"
                            ? "status-running"
                            : crawlerStatus?.last_run_status ===
                                "error"
                              ? "status-error"
                              : crawlerStatus?.last_run_status ===
                                  "success"
                                ? "status-success"
                                : "status-idle"
                        }
                      >
                        {crawlerStatus?.status ===
                        "running"
                          ? "Running"
                          : crawlerStatus?.last_run_status ===
                              "success"
                            ? "Success"
                            : crawlerStatus?.last_run_status ===
                                "error"
                              ? "Error"
                              : "Idle"}
                      </strong>
                    </div>

                    <div className="status-item">
                      <span>Last run</span>
                      <strong>
                        {crawlerStatus?.last_run_source ||
                          "—"}
                      </strong>
                    </div>

                    <div className="status-item">
                      <span>Created</span>
                      <strong>
                        {crawlerStatus?.last_stats
                          ?.articles_created ??
                          "—"}
                      </strong>
                    </div>

                    <div className="status-item">
                      <span>Duplicate</span>
                      <strong>
                        {crawlerStatus?.last_stats
                          ?.articles_duplicate ??
                          "—"}
                      </strong>
                    </div>

                    <div className="status-item">
                      <span>Date filtered</span>
                      <strong>
                        {crawlerStatus?.last_stats
                          ?.articles_date_filtered ??
                          "—"}
                      </strong>
                    </div>

                    <div className="status-item">
                      <span>Last finished</span>
                      <strong>
                        {formatDateTime(
                          crawlerStatus?.last_finished_at
                        )}
                      </strong>
                    </div>

                  </div>
                </div>

              </div>
            </div>

              </div>
            </div>
          )}
        </section>

        {selectedArticle && (
          <div
            className="article-modal-backdrop"
            role="presentation"
            onMouseDown={(event) => {
              if (event.target === event.currentTarget) closeArticle();
            }}
          >
            <section
              className="article-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="article-modal-title"
            >
              <div className="article-modal-header">
                <div>
                  <span className="modal-eyebrow">ARTICLE DETAIL</span>
                  <h3 id="article-modal-title">{selectedArticle.title || "Không có tiêu đề"}</h3>
                </div>
                <button
                  type="button"
                  className="modal-close"
                  onClick={closeArticle}
                  aria-label="Đóng chi tiết bài viết"
                >
                  ×
                </button>
              </div>

              <div className="article-modal-meta">
                <div><span>Danh mục</span><strong>{selectedArticle.category || "—"}</strong></div>
                <div><span>Nguồn</span><strong>{selectedArticle.source || "—"}</strong></div>
                <div><span>Loại nội dung</span><strong>{selectedArticle.content_source || "—"}</strong></div>
                <div><span>Decision Score</span><strong>{typeof selectedArticle.decision_score === "number" ? selectedArticle.decision_score.toFixed(4) : "—"}</strong></div>
                <div><span>Ngày xuất bản</span><strong>{formatDateTime(selectedArticle.published_at)}</strong></div>
                <div><span>Được thu thập</span><strong>{formatDateTime(selectedArticle.crawled_at)}</strong></div>
              </div>

              <div className="article-modal-content">
                <h4>Nội dung</h4>
                {selectedArticle.content ? (
                  <p>{selectedArticle.content}</p>
                ) : (
                  <div className="modal-empty">
                    API Recent hiện chỉ trả về metadata của bài viết. Có thể mở rộng endpoint Article Detail để tải toàn bộ nội dung khi cần.
                  </div>
                )}
              </div>

              {selectedArticle.url && (
                <div className="article-modal-footer">
                  <a
                    href={selectedArticle.url}
                    target="_blank"
                    rel="noreferrer"
                    className="article-source-link"
                  >
                    Mở bài viết gốc →
                  </a>
                </div>
              )}
            </section>
          </div>
        )}

      </main>
      </div>
    </div>
  );
}

export default App;

