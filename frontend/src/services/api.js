const API_BASE_URL = "http://localhost:8000";

async function request(url, options = {}) {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `HTTP ${response.status}`;

    try {
      const errorData = await response.json();

      if (errorData?.detail) {
        message = errorData.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(message);
  }

  return response.json();
}

function buildQuery(params = {}) {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (
      value !== undefined &&
      value !== null &&
      value !== ""
    ) {
      searchParams.set(key, value);
    }
  });

  const query = searchParams.toString();

  return query ? `?${query}` : "";
}

// =========================
// Analytics
// =========================

export async function getSummary(params = {}) {
  return request(`/analytics/summary${buildQuery(params)}`);
}

export async function getCategories(params = {}) {
  return request(`/analytics/categories${buildQuery(params)}`);
}

export async function getDaily(params = {}) {
  return request(`/analytics/daily${buildQuery(params)}`);
}

export async function getSources(params = {}) {
  return request(`/analytics/sources${buildQuery(params)}`);
}

export async function getContentSources(params = {}) {
  return request(
    `/analytics/content-sources${buildQuery(params)}`
  );
}

export async function getTrendByCategory(params = {}) {
  return request(
    `/analytics/trend-by-category${buildQuery(params)}`
  );
}

export async function getRecent(limit = 20, params = {}) {
  return request(
    `/analytics/recent${buildQuery({
      ...params,
      limit,
    })}`
  );
}

// =========================
// Intelligence
// =========================

export async function getKeywords(params = {}) {
  return request(
    `/intelligence/keywords${buildQuery(params)}`
  );
}

export async function getIntelligenceTrends(params = {}) {
  return request(
    `/intelligence/trends${buildQuery(params)}`
  );
}

export async function getHotTopics(params = {}) {
  return request(
    `/intelligence/hot-topics${buildQuery(params)}`
  );
}

// =========================
// Prediction
// =========================

export async function predictNews(text) {
  return request("/predict", {
    method: "POST",
    body: JSON.stringify({
      text,
    }),
  });
}

// =========================
// Crawler Control
// =========================

export async function getCrawlerSources() {
  return request("/crawler/sources");
}

export async function getCrawlerStatus() {
  return request("/crawler/status");
}

export async function runCrawler({
  sources = [],
  fromDate = "",
  toDate = "",
} = {}) {
  return request("/crawler/run-now", {
    method: "POST",
    body: JSON.stringify({
      sources,
      from_date: fromDate || null,
      to_date: toDate || null,
    }),
  });
}
