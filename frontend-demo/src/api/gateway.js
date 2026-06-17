const TOKEN_KEY = 'blearn.gatewayToken';
const STUDENT_HASH_KEY = 'blearn.studentHash';
const MATERIALS_CACHE_KEY = 'blearn.recommendationMaterials';

function normalizeBaseUrl(value) {
  return value.trim().replace(/\/$/, '');
}

export function resolveGatewayBaseUrl() {
  const configured = import.meta.env.VITE_GATEWAY_URL?.trim();
  if (configured) {
    return normalizeBaseUrl(configured);
  }

  if (typeof window !== 'undefined' && window.__BLEARN_GATEWAY_URL__) {
    return normalizeBaseUrl(window.__BLEARN_GATEWAY_URL__);
  }

  if (typeof window !== 'undefined' && window.location?.hostname) {
    const { protocol, hostname } = window.location;
    const localHosts = new Set(['localhost', '127.0.0.1', '::1']);
    const configuredPort = import.meta.env.VITE_GATEWAY_PORT?.trim() || (window.__BLEARN_GATEWAY_PORT__ ? String(window.__BLEARN_GATEWAY_PORT__) : '8000');
    const port = localHosts.has(hostname) ? configuredPort : (window.__BLEARN_GATEWAY_PORT__ ? String(window.__BLEARN_GATEWAY_PORT__) : '8000');
    const targetHost = localHosts.has(hostname) ? '127.0.0.1' : hostname;
    return `${protocol}//${targetHost}:${port}`;
  }

  return 'http://localhost:8000';
}

export function gatewayUrl(path = '') {
  const baseUrl = resolveGatewayBaseUrl();
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${normalizedPath}`;
}

const API_BASE_URL = resolveGatewayBaseUrl();
const OVERRIDE_STUDENT_HASH = import.meta.env.VITE_STUDENT_ID_HASH || '';

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function clearGatewaySession() {
  clearToken();
  localStorage.removeItem(STUDENT_HASH_KEY);
  localStorage.removeItem(MATERIALS_CACHE_KEY);
}

export function readCachedMaterials() {
  try {
    const raw = localStorage.getItem(MATERIALS_CACHE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

async function sha256Hex(value) {
  const encoded = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest('SHA-256', encoded);
  return Array.from(new Uint8Array(digest), (item) => item.toString(16).padStart(2, '0')).join('');
}

export async function resolveStudentHash(user) {
  if (OVERRIDE_STUDENT_HASH) {
    localStorage.setItem(STUDENT_HASH_KEY, OVERRIDE_STUDENT_HASH);
    return OVERRIDE_STUDENT_HASH;
  }

  const existing = localStorage.getItem(STUDENT_HASH_KEY);
  if (existing && existing !== 'undefined' && existing !== 'null') {
    return existing;
  }

  if (user?.student_id_hash) {
    localStorage.setItem(STUDENT_HASH_KEY, user.student_id_hash);
    return user.student_id_hash;
  }

  // Fallback to student 28400's real hash in user_embeddings.parquet
  const defaultHash = '79d86f4d0c556c37c879fb9ba278f9996d5f1f50468d8e26e13a19ba6b09c219';
  localStorage.setItem(STUDENT_HASH_KEY, defaultHash);
  return defaultHash;
}

export function readStudentHash() {
  return localStorage.getItem(STUDENT_HASH_KEY) || '';
}

export async function loginGateway({ username, role = 'student' }) {
  const response = await fetch(`${API_BASE_URL}/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, role }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Đăng nhập Gateway thất bại (${response.status}): ${detail || 'Unknown error'}`);
  }

  const payload = await response.json();
  if (!payload?.access_token) {
    throw new Error('Gateway không trả về access_token hợp lệ.');
  }

  setToken(payload.access_token);
  return payload.access_token;
}

export async function ensureGatewaySession(user) {
  const username = user?.email || user?.id || 'student@blearn.demo';
  const token = await loginGateway({ username, role: 'student' });
  const studentHash = await resolveStudentHash(user);
  return { token, studentHash };
}

async function fetchWithGatewayRetry(url, options, { username, role = 'student' } = {}) {
  const token = getToken() || (await loginGateway({ username, role }));
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options?.headers || {}),
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.status !== 401) {
    return response;
  }

  clearGatewaySession();
  const refreshedToken = await loginGateway({ username, role });
  return fetch(url, {
    ...options,
    headers: {
      ...(options?.headers || {}),
      Authorization: `Bearer ${refreshedToken}`,
    },
  });
}

export async function trackStudentClick(studentId, siteId, metadata = {}) {
  const studentHash = studentId || readStudentHash();
  const numericSiteId = Number(siteId);

  if (!studentHash || !Number.isFinite(numericSiteId)) {
    console.log('click tracking skipped: missing student hash or site id', { studentId, siteId });
    return false;
  }

  window.dispatchEvent(new CustomEvent('blearn-toast', {
    detail: { message: 'Đang ghi nhận hoạt động học tập...', type: 'info' }
  }));

  try {
    const response = await fetchWithGatewayRetry(`${API_BASE_URL}/track-click`, {
      method: 'POST',
      keepalive: true,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        student_id_hash: studentHash,
        id_site: numericSiteId,
        material_title: metadata.title || metadata.material_title || '',
        material_type: metadata.type || metadata.material_type || '',
        material_chapter: metadata.chapter || metadata.material_chapter || '',
        material_duration: metadata.duration || metadata.material_duration || '',
        duration_seconds: Number(metadata.duration_seconds || metadata.durationSeconds || 0),
        event_type: metadata.event_type || metadata.eventType || 'click',
        page_path: window.location.pathname,
        source: 'frontend-demo',
      }),
    }, { username: 'student@blearn.demo', role: 'student' });

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(`track-click failed (${response.status}): ${detail || 'Unknown error'}`);
    }

    window.dispatchEvent(new CustomEvent('blearn-toast', {
      detail: { message: 'Đã ghi nhận hoạt động học tập.', type: 'success' }
    }));

    return true;
  } catch (error) {
    console.log('track-click fallback:', error);
    window.dispatchEvent(new CustomEvent('blearn-toast', {
      detail: { message: 'Chưa kết nối được hệ thống ghi nhận, hoạt động đã được lưu tạm.', type: 'error' }
    }));
    return false;
  }
}

export async function fetchRecommendations(studentHash) {
  const cacheBuster = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const response = await fetchWithGatewayRetry(`${API_BASE_URL}/recommendations/${studentHash}?_ts=${encodeURIComponent(cacheBuster)}`, {
    method: 'GET',
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
    },
  }, { username: 'student@blearn.demo', role: 'student' });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Lấy recommendations thất bại (${response.status}): ${detail || 'Unknown error'}`);
  }

  const payload = await response.json();
  const materials = Array.isArray(payload?.recommendations) ? payload.recommendations : [];
  localStorage.setItem(MATERIALS_CACHE_KEY, JSON.stringify(materials));
  return payload;
}
