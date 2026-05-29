import { createContext, useContext, useMemo, useState } from 'react';
import { tempUsers } from '../data/tempUsers.js';
import { clearGatewaySession, ensureGatewaySession } from '../api/gateway.js';

const USERS_KEY = 'blearn.tempUsers';
const SESSION_KEY = 'blearn.currentUserId';

const AuthContext = createContext(null);

function readUsers() {
  try {
    const saved = localStorage.getItem(USERS_KEY);
    return saved ? JSON.parse(saved) : tempUsers;
  } catch {
    return tempUsers;
  }
}

function writeUsers(users) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

function persistUsers(users) {
  writeUsers(users);
}

function makeSalt() {
  const values = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(values, (value) => value.toString(16).padStart(2, '0')).join('');
}

async function hashPassword(password, salt) {
  const encoded = new TextEncoder().encode(`${salt}:${password}`);
  const digest = await crypto.subtle.digest('SHA-256', encoded);
  return Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, '0')).join('');
}

function sanitizeUser(user) {
  if (!user) return null;
  const { passwordHash, salt, ...safeUser } = user;
  return safeUser;
}

export function AuthProvider({ children }) {
  const [users, setUsers] = useState(() => readUsers());
  const [currentUserId, setCurrentUserId] = useState(() => localStorage.getItem(SESSION_KEY));

  const currentUser = useMemo(
    () => sanitizeUser(users.find((user) => user.id === currentUserId)),
    [users, currentUserId],
  );

  const [gatewayToken, setGatewayToken] = useState(() => localStorage.getItem('blearn.gatewayToken'));
  const [currentStudentHash, setCurrentStudentHash] = useState(() => localStorage.getItem('blearn.studentHash'));

  const register = async ({ email, password, fullName, role, ...rest }) => {
    const normalizedEmail = email.trim().toLowerCase();
    if (users.some((user) => user.email === normalizedEmail)) {
      throw new Error('Email này đã được đăng ký.');
    }

    const salt = makeSalt();
    const passwordHash = await hashPassword(password, salt);
    const user = {
      id: `user-${Date.now()}`,
      email: normalizedEmail,
      passwordHash,
      salt,
      profile: {
        fullName: fullName.trim(),
        role: role || 'Học viên',
        phone: rest.phone || '',
        birthYear: rest.birthYear || '',
        gender: rest.gender || '',
        location: rest.location || '',
        educationLevel: rest.educationLevel || '',
        learningGoal: rest.learningGoal || '',
      },
      demographics: {
        school: rest.school || '',
        major: rest.major || '',
        occupation: rest.occupation || '',
        studyTimePreference: rest.studyTimePreference || '',
      },
      createdAt: new Date().toISOString(),
    };

    const nextUsers = [...users, user];
    setUsers(nextUsers);
    persistUsers(nextUsers);
    localStorage.setItem(SESSION_KEY, user.id);
    setCurrentUserId(user.id);
    const safeUser = sanitizeUser(user);
    await ensureGatewaySession(safeUser);
    setGatewayToken(localStorage.getItem('blearn.gatewayToken'));
    setCurrentStudentHash(localStorage.getItem('blearn.studentHash'));
    return safeUser;
  };

  const login = async ({ email, password }) => {
    const normalizedEmail = email.trim().toLowerCase();
    const user = users.find((item) => item.email === normalizedEmail);
    if (!user) {
      throw new Error('Email hoặc mật khẩu không đúng.');
    }

    const passwordHash = await hashPassword(password, user.salt);
    if (passwordHash !== user.passwordHash) {
      throw new Error('Email hoặc mật khẩu không đúng.');
    }

    localStorage.setItem(SESSION_KEY, user.id);
    setCurrentUserId(user.id);
    const safeUser = sanitizeUser(user);
    await ensureGatewaySession(safeUser);
    setGatewayToken(localStorage.getItem('blearn.gatewayToken'));
    setCurrentStudentHash(localStorage.getItem('blearn.studentHash'));
    return safeUser;
  };

  const logout = () => {
    localStorage.removeItem(SESSION_KEY);
    setCurrentUserId(null);
    clearGatewaySession();
    setGatewayToken(null);
    setCurrentStudentHash(null);
  };

  const updateProfile = (nextProfile) => {
    if (!currentUserId) return;
    const nextUsers = users.map((user) => {
      if (user.id !== currentUserId) return user;
      return {
        ...user,
        profile: {
          ...user.profile,
          fullName: nextProfile.fullName,
          role: nextProfile.role,
          phone: nextProfile.phone,
          birthYear: nextProfile.birthYear,
          gender: nextProfile.gender,
          location: nextProfile.location,
          educationLevel: nextProfile.educationLevel,
          learningGoal: nextProfile.learningGoal,
        },
        demographics: {
          school: nextProfile.school,
          major: nextProfile.major,
          occupation: nextProfile.occupation,
          studyTimePreference: nextProfile.studyTimePreference,
        },
      };
    });
    setUsers(nextUsers);
    persistUsers(nextUsers);
  };

  const value = useMemo(() => ({
    currentUser,
    isAuthenticated: Boolean(currentUser),
    login,
    logout,
    register,
    updateProfile,
    token: gatewayToken,
    currentStudentHash,
  }), [currentUser, users, gatewayToken, currentStudentHash]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return context;
}
