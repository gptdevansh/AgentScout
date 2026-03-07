/* ── App — routes and root layout ─────────────────────────────────────── */

import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import PipelinePage from './pages/PipelinePage';
import PipelineRunsPage from './pages/PipelineRunsPage';
import PipelineRunDetailPage from './pages/PipelineRunDetailPage';
import PostsPage from './pages/PostsPage';
import PostDetailPage from './pages/PostDetailPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="pipeline" element={<PipelinePage />} />
          <Route path="pipeline/runs" element={<PipelineRunsPage />} />
          <Route path="pipeline/runs/:runId" element={<PipelineRunDetailPage />} />
          <Route path="posts" element={<PostsPage />} />
          <Route path="posts/:postId" element={<PostDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
