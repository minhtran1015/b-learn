import { Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from './components/AppLayout.jsx';
import CourseLayout from './components/CourseLayout.jsx';
import AnalyticsPage from './pages/AnalyticsPage.jsx';
import CoursesPage from './pages/CoursesPage.jsx';
import CourseOverviewPage from './pages/CourseOverviewPage.jsx';
import MaterialsPage from './pages/MaterialsPage.jsx';
import MaterialDetailPage from './pages/MaterialDetailPage.jsx';
import AssignmentsPage from './pages/AssignmentsPage.jsx';
import AssignmentDetailPage from './pages/AssignmentDetailPage.jsx';
import DoAssignmentPage from './pages/DoAssignmentPage.jsx';
import AuthPage from './pages/AuthPage.jsx';
import ProfilePage from './pages/ProfilePage.jsx';
import CalendarPage from './pages/CalendarPage.jsx';
import DiscussionsPage from './pages/DiscussionsPage.jsx';
import HelpPage from './pages/HelpPage.jsx';
import MessagesPage from './pages/MessagesPage.jsx';
import SettingsPage from './pages/SettingsPage.jsx';

export default function App() {
  return (
    <Routes>
      <Route path="login" element={<AuthPage mode="login" />} />
      <Route path="register" element={<AuthPage mode="register" />} />
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/courses" replace />} />
        <Route path="analytics" element={<Navigate to="/courses/machine-learning/analytics" replace />} />
        <Route path="calendar" element={<CalendarPage />} />
        <Route path="messages" element={<MessagesPage />} />
        <Route path="help" element={<HelpPage />} />
        <Route path="courses" element={<CoursesPage />} />
        <Route path="courses/:courseId" element={<CourseLayout />}>
          <Route index element={<CourseOverviewPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="materials" element={<MaterialsPage />} />
          <Route path="materials/:materialId" element={<MaterialDetailPage />} />
          <Route path="assignments" element={<AssignmentsPage />} />
          <Route path="assignments/:assignmentId" element={<AssignmentDetailPage />} />
          <Route path="assignments/:assignmentId/do" element={<DoAssignmentPage />} />
          <Route path="discussions" element={<DiscussionsPage />} />
        </Route>
        <Route path="settings" element={<SettingsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
