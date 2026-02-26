import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Settings as SettingsIcon, Search, LayoutDashboard, Clapperboard, ClipboardCheck } from 'lucide-react';
import Research from './pages/Research';
import Curation from './pages/Curation';
import Settings from './pages/Settings';

const queryClient = new QueryClient();

function Navigation() {
    const location = useLocation();

    const navItems = [
        { path: '/', label: 'Overview', icon: LayoutDashboard },
        { path: '/research', label: 'Research', icon: Search },
        { path: '/curation', label: 'Curation', icon: ClipboardCheck },
        { path: '/production', label: 'Production', icon: Clapperboard },
        { path: '/settings', label: 'Settings', icon: SettingsIcon },
    ];

    return (
        <nav className="bg-gray-900 text-white w-64 min-h-screen flex flex-col pt-8 shadow-xl">
            <div className="px-6 mb-10">
                <h1 className="text-xl font-bold tracking-tight text-blue-400">YM Factory v3</h1>
                <p className="text-[10px] uppercase tracking-widest text-gray-500 mt-1 font-bold">Autonomous Video Engine</p>
            </div>

            <div className="flex-1 flex flex-col gap-2 px-4">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path ||
                        (item.path !== '/' && location.pathname.startsWith(item.path));

                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={`flex items - center gap - 3 px - 4 py - 3 rounded - xl transition - all duration - 200 ${isActive
                                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
                                : 'text-gray-400 hover:bg-gray-800/50 hover:text-white'
                                } `}
                        >
                            <Icon className={`w - 5 h - 5 ${isActive ? 'text-white' : 'text-gray-500'} `} />
                            <span className="font-semibold text-sm">{item.label}</span>
                        </Link>
                    );
                })}
            </div>
        </nav>
    );
}

// Placeholder pages for early routing
const Placeholder = ({ title }: { title: string }) => (
    <div className="flex items-center justify-center h-full text-gray-400">
        <p>Module under construction: {title}</p>
    </div>
);

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                <div className="flex min-h-screen bg-[#0f1117] text-gray-100 font-sans">
                    <Navigation />

                    <main className="flex-1 overflow-auto">
                        <Routes>
                            <Route path="/" element={<Placeholder title="Dashboard Overview" />} />
                            <Route path="/research/*" element={<Research />} />
                            <Route path="/curation/*" element={<Curation />} />
                            <Route path="/production/*" element={<Placeholder title="Stage 3: Production Studio" />} />
                            <Route path="/settings" element={<Settings />} />
                        </Routes>
                    </main>
                </div>
            </BrowserRouter>
        </QueryClientProvider>
    );
}

export default App;
