import { Routes, Route } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import Dashboard from './pages/Dashboard'
import Nodes from './pages/Nodes'
import Tasks from './pages/Tasks'
import Storage from './pages/Storage'
import Providers from './pages/Providers'
import Events from './pages/Events'
import Settings from './pages/Settings'

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/nodes" element={<Nodes />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/storage" element={<Storage />} />
        <Route path="/providers" element={<Providers />} />
        <Route path="/events" element={<Events />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
