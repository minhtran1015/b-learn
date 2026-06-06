const TOKEN_KEY = 'blearn.gatewayToken';
const STUDENT_HASH_KEY = 'blearn.studentHash';
const MATERIALS_CACHE_KEY = 'blearn.recommendationMaterials';

const rawBaseUrl = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000';
const API_BASE_URL = rawBaseUrl.replace(/\/$/, '');
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
  const token = getToken() || (await loginGateway({ username, role: 'student' }));
  const studentHash = await resolveStudentHash(user);
  return { token, studentHash };
}

export async function trackStudentClick(studentId, siteId) {
  const studentHash = studentId || readStudentHash();
  const numericSiteId = Number(siteId);

  if (!studentHash || !Number.isFinite(numericSiteId)) {
    console.log('click tracking skipped: missing student hash or site id', { studentId, siteId });
    return false;
  }

  try {
    const token = getToken();
    if (!token) {
      throw new Error('missing JWT token');
    }

    const response = await fetch(`${API_BASE_URL}/track-click`, {
      method: 'POST',
      keepalive: true,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        student_id_hash: studentHash,
        id_site: numericSiteId,
        page_path: window.location.pathname,
        source: 'frontend-demo',
      }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        clearGatewaySession();
        window.location.reload();
      }
      const detail = await response.text();
      throw new Error(`track-click failed (${response.status}): ${detail || 'Unknown error'}`);
    }

    return true;
  } catch (error) {
    console.log('track-click fallback:', error);
    return false;
  }
}

export async function fetchRecommendations(studentHash) {
  const token = getToken();
  if (!token) {
    throw new Error('Chưa có JWT token, vui lòng đăng nhập lại.');
  }

  const response = await fetch(`${API_BASE_URL}/recommendations/${studentHash}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearGatewaySession();
      window.location.reload();
    }
    const detail = await response.text();
    throw new Error(`Lấy recommendations thất bại (${response.status}): ${detail || 'Unknown error'}`);
  }

  const payload = await response.json();
  const materials = Array.isArray(payload?.recommendations) ? payload.recommendations : [];
  localStorage.setItem(MATERIALS_CACHE_KEY, JSON.stringify(materials));
  return payload;
}
