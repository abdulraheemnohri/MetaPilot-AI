import { useState } from 'react';
import { useSettingsStore } from '../store/useSettingsStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export default function SettingsPage() {
  const { theme, setTheme } = useSettingsStore();
  const [activeTab, setActiveTab] = useState('general');

  const tabs = [
    { id: 'general', label: 'General', icon: '⚙️' },
    { id: 'orchestration', label: 'Orchestration', icon: '🧠' },
    { id: 'browser', label: 'Browser', icon: '🌐' },
    { id: 'security', label: 'Security', icon: '🔒' }
  ];

  return (
    <div className="container mx-auto p-6 max-w-5xl animate-fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-muted-foreground text-lg">System-wide configuration and project control.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        <div className="space-y-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full text-left px-4 py-3 rounded-xl transition-all flex items-center gap-3 ${activeTab === tab.id ? 'bg-primary text-white shadow-md' : 'hover:bg-muted text-muted-foreground'}`}
            >
              <span>{tab.icon}</span>
              <span className="font-medium">{tab.label}</span>
            </button>
          ))}
        </div>

        <div className="md:col-span-3">
          {activeTab === 'general' && (
            <Card className="shadow-lg border-none">
              <CardHeader><CardTitle>Appearance & Locale</CardTitle></CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold mb-3">Theme</label>
                  <div className="flex gap-4">
                    {['light', 'dark', 'system'].map(t => (
                      <button
                        key={t}
                        onClick={() => setTheme(t as any)}
                        className={`px-6 py-2 rounded-lg border-2 capitalize transition-all ${theme === t ? 'border-primary bg-primary/5 text-primary font-bold' : 'border-border'}`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="pt-4 border-t">
                  <label className="block text-sm font-semibold mb-2">Default Language</label>
                  <select className="w-full p-2 border rounded-lg bg-background">
                    <option>English (US)</option>
                    <option>Hindi (HI)</option>
                    <option>Spanish (ES)</option>
                  </select>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'orchestration' && (
            <Card className="shadow-lg border-none">
              <CardHeader><CardTitle>AI Orchestration Logic</CardTitle></CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold">Parallel Execution</div>
                    <div className="text-xs text-muted-foreground">Run subtasks across providers simultaneously.</div>
                  </div>
                  <Badge className="bg-green-500 cursor-pointer">ENABLED</Badge>
                </div>
                <div className="pt-4 border-t">
                  <label className="block text-sm font-semibold mb-2">Consensus Strategy</label>
                  <select className="w-full p-2 border rounded-lg bg-background">
                    <option>Best of (Ranked)</option>
                    <option>Consensus (Majority)</option>
                    <option>Concatenate (Full synthesis)</option>
                  </select>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'browser' && (
            <Card className="shadow-lg border-none">
              <CardHeader><CardTitle>Browser Automation</CardTitle></CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold">Headless Mode</div>
                    <div className="text-xs text-muted-foreground">Run browser sessions in the background.</div>
                  </div>
                  <Badge className="bg-primary cursor-pointer">ON</Badge>
                </div>
                <div className="pt-4 border-t">
                  <label className="block text-sm font-semibold mb-2">Max Concurrent Tabs</label>
                  <input type="number" defaultValue={5} className="w-full p-2 border rounded-lg bg-background" />
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === 'security' && (
            <Card className="shadow-lg border-none">
              <CardHeader><CardTitle>Privacy & Guardrails</CardTitle></CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold">Fact Checking</div>
                    <div className="text-xs text-muted-foreground">Cross-verify claims between different AI models.</div>
                  </div>
                  <Badge className="bg-green-500 cursor-pointer">STRICT</Badge>
                </div>
                <div className="flex items-center justify-between pt-4 border-t">
                  <div>
                    <div className="font-bold">Audit Logging</div>
                    <div className="text-xs text-muted-foreground">Keep detailed logs of all AI requests.</div>
                  </div>
                  <Badge variant="secondary" className="cursor-pointer">LOCAL ONLY</Badge>
                </div>
                <Button variant="destructive" className="w-full mt-4">Clear All Local Data</Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
