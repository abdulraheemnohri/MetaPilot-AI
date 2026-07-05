import { useState } from 'react';
import { useSettingsStore } from '../store/useSettingsStore';
import { useProvidersStore } from '../store/useProvidersStore';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';

export function SettingsPage() {
  const { settings, updateSettings } = useSettingsStore();
  const { providers, activeProvider, setActiveProvider } = useProvidersStore();
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Configure your MetaPilot AI experience</p>
        </div>

        <Card>
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">AI Providers</h2>
            <div className="grid gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Active Provider</label>
                <Select
                  value={activeProvider}
                  onVolumeChange={(value) => setActiveProvider(value)}
                >
                  {providers.map(provider => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">General Settings</h2>
            <div className="grid gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Max Tokens
                </label>
                <Input
                  type="number"
                  value={settings.maxTokens}
                  onChange={(e) => 
                    updateSettings({ maxTokens: parseInt(e.target.value) || 4096 })
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">
                  Temperature
                </label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={settings.temperature}
                  onChange={(e) => 
                    updateSettings({ temperature: parseFloat(e.target.value) || 0.7 })
                  }
                />
              </div>
            </div>
          </div>
        </Card>

        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? 'Saving...' : 'Save Settings'}
          </Button>
        </div>
      </div>
    </div>
  );
}