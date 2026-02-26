import React, { useState } from 'react';
import { Save, CheckCircle2 } from 'lucide-react';

export default function Settings() {
    const [dbUrl, setDbUrl] = useState('');
    const [cometApiKey, setCometApiKey] = useState('');
    const [anthropicApiKey, setAnthropicApiKey] = useState('');
    const [youtubeClientId, setYoutubeClientId] = useState('');
    const [youtubeClientSecret, setYoutubeClientSecret] = useState('');
    const [saved, setSaved] = useState(false);

    const handleSave = (e: React.FormEvent) => {
        e.preventDefault();
        // In a real app, these would be saved securely to the backend
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
    };

    return (
        <div className="max-w-4xl mx-auto p-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">System Settings</h1>
                <p className="text-gray-600">Configure API keys and core infrastructure connections for the YouTube Movie Factory.</p>
            </div>

            <form onSubmit={handleSave} className="space-y-8 bg-white p-8 rounded-xl shadow-sm border border-gray-100">

                {/* Environment section */}
                <section>
                    <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b">Core Infrastructure</h2>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Neon Database URL</label>
                            <input
                                type="password"
                                value={dbUrl}
                                onChange={(e) => setDbUrl(e.target.value)}
                                placeholder="postgresql+psycopg://..."
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            />
                        </div>
                    </div>
                </section>

                {/* AI Gateways section */}
                <section>
                    <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b">AI Services</h2>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">CometAPI Key (Unified Gateway)</label>
                            <input
                                type="password"
                                value={cometApiKey}
                                onChange={(e) => setCometApiKey(e.target.value)}
                                placeholder="sk-..."
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            />
                            <p className="text-xs text-gray-500 mt-1">Used for Image Gen, Kling 3 Video, Suno V5, and Gemini scoring.</p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Anthropic API Key (Creative Director)</label>
                            <input
                                type="password"
                                value={anthropicApiKey}
                                onChange={(e) => setAnthropicApiKey(e.target.value)}
                                placeholder="sk-ant-..."
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            />
                        </div>
                    </div>
                </section>

                {/* YouTube section */}
                <section>
                    <h2 className="text-xl font-semibold text-gray-800 mb-4 pb-2 border-b">YouTube Publishing</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Client ID</label>
                            <input
                                type="text"
                                value={youtubeClientId}
                                onChange={(e) => setYoutubeClientId(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Client Secret</label>
                            <input
                                type="password"
                                value={youtubeClientSecret}
                                onChange={(e) => setYoutubeClientSecret(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            />
                        </div>
                    </div>
                </section>

                <div className="pt-6 flex justify-end items-center gap-4">
                    {saved && (
                        <span className="flex items-center text-green-600 text-sm font-medium">
                            <CheckCircle2 className="w-4 h-4 mr-1" />
                            Settings saved securely
                        </span>
                    )}
                    <button
                        type="submit"
                        className="flex items-center px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors focus:ring-4 focus:ring-blue-100"
                    >
                        <Save className="w-4 h-4 mr-2" />
                        Save Configuration
                    </button>
                </div>

            </form>
        </div>
    );
}
