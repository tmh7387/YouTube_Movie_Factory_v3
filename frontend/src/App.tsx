import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Settings as SettingsIcon, Search, LayoutDashboard, Clapperboard, Layers } from 'lucide-react';
import Settings from './pages/Settings';

function Navigation() {
    const location = useLocation();

    const navItems = [
        { path: '/', label: 'Overview', icon: LayoutDashboard },
        { path: '/research', label: 'Research', icon: Search },
        { path: '/curation', label: 'Curation', icon: Layers },
        { path: '/production', label: 'Production', icon: Clapperboard },
        { path: '/settings', label: 'Settings', icon: SettingsIcon },
    ];

    return (
        <nav className="bg-gray-900 text-white w-64 min-h-screen flex flex-col pt-8">
            <div className="px-6 mb-10">
                <h1 className="text-xl font-bold tracking-tight">YM Factory v3</h1>
                <p className="text-xs text-gray-400 mt-1">Autonomous Video Engine</p>
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
                            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                                    ? 'bg-blue-600 text-white shadow-sm'
                                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                                }`}
                        >
                            <Icon className="w-5 h-5" />
                            <span className="font-medium">{item.label}</span>
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
        <BrowserRouter>
            <div className="flex min-h-screen bg-gray-50 font-sans">
                <Navigation />

                <main className="flex-1 overflow-auto">
                    <Routes>
                        <Route path="/" element={<Placeholder title="Dashboard Overview" />} />
                        <Route path="/research/*" element={<Placeholder title="Stage 1: Research Hub" />} />
                        <Route path="/curation/*" element={<Placeholder title="Stage 2: Curation Board" />} />
                        <Route path="/production/*" element={<Placeholder title="Stage 3: Production Studio" />} />
                        <Route path="/settings" element={<Settings />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    );
}

export default App;
