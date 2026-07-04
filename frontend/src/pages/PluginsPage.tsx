import { useState } from 'react';
import { usePluginsStore } from '../store/usePluginsStore';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';

export function PluginsPage() {
  const { plugins, enablePlugin, disablePlugin, isLoading } = usePluginsStore();
  const [pluginUrl, setPluginUrl] = useState('');

  const handleInstall = async () => {
    if (!pluginUrl.trim()) return;
    await new Promise(resolve => setTimeout(resolve, 1000));
    setPluginUrl('');
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Plugins</h1>
          <p className="text-muted-foreground">
            Extend MetaPilot AI functionality with plugins
          </p>
        </div>

        <Card className="p-6">
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Install Plugin</h2>
            <div className="flex gap-4">
              <Input
                type="url"
                value={pluginUrl}
                onChange={(e) => setPluginUrl(e.target.value)}
                placeholder="https://example.com/plugin.zip"
                className="flex-1"
              />
              <Button 
                onClick={handleInstall}
                disabled={!pluginUrl.trim() || isLoading}
              >
                {isLoading ? 'Installing...' : 'Install'}
              </Button>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Installed Plugins</h2>
            {plugins.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">
                No plugins installed yet. Install your first plugin to get started.
              </p>
            ) : (
              <div className="space-y-3">
                {plugins.map(plugin => (
                  <div 
                    key={plugin.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">🧩</span>
                      <div>
                        <p className="font-medium">{plugin.name}</p>
                        <p className="text-sm text-muted-foreground">
                          v{plugin.version} by {plugin.author}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant={plugin.enabled ? 'default' : 'secondary'}>{
                        plugin.enabled ? 'Enabled' : 'Disabled'
                      }</Badge>
                      {plugin.enabled ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => disablePlugin(plugin.id)}
                        >
                          Disable
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          onClick={() => enablePlugin(plugin.id)}
                        >
                          Enable
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}