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
  if (existing) {
    return existing;
  }

  const source = user?.id || user?.email || '';
  if (!source) {
    throw new Error('Không thể xác định student_id_hash cho người dùng hiện tại.');
  }

  const hash = await sha256Hex(source);
  localStorage.setItem(STUDENT_HASH_KEY, hash);
  return hash;
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
      clearToken();
    }
    const detail = await response.text();
    throw new Error(`Lấy recommendations thất bại (${response.status}): ${detail || 'Unknown error'}`);
  }

  const payload = await response.json();
  const materials = Array.isArray(payload?.recommendations) ? payload.recommendations : [];
  localStorage.setItem(MATERIALS_CACHE_KEY, JSON.stringify(materials));
  return payload;
}
