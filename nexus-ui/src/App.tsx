import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { Shell } from './components/layout/Shell';

// 1. IMPORTANDO AS PÁGINAS REAIS AQUI!
import Dashboard from './pages/Dashboard';
import Chronos from './pages/Chronos';
import Treasury from './pages/Treasury';
import RPG from './pages/RPG';
import Library from './pages/Library';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutos de cache
      refetchOnWindowFocus: false,
    },
  },
});

// Mantemos o Placeholder apenas para o Inbox, que faremos depois
const Placeholder = ({ title }: { title: string }) => (
  <div className="flex h-full items-center justify-center text-zinc-500 border-2 border-dashed border-zinc-800 rounded-lg">
    {title} Module Loading...
  </div>
);

const router = createBrowserRouter([
  {
    path: '/',
    element: <Shell />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      
      // 2. SUBSTITUINDO OS PLACEHOLDERS PELOS COMPONENTES REAIS
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'chronos', element: <Chronos /> },
      { path: 'treasury', element: <Treasury /> },
      { path: 'rpg', element: <RPG /> },
      { path: 'library', element: <Library /> },
      
      { path: 'inbox', element: <Placeholder title="Inbox (HitL)" /> },
      { path: '*', element: <Navigate to="/dashboard" replace /> },
    ],
  },
]);

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

export default App;