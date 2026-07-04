import { useState } from 'react';
import { useProvidersStore } from '../store/useProvidersStore';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export function ProvidersPage() {
  const { providers, activeProvider, setActiveProvider, addProvider } = useProvidersStore();
  const [apiKey, setApiKey] = useState('');
  const [selectedProvider, setSelectedProvider] = useState('');

  const handleAddProvider = async () => {
    if (!selectedProvider || !apiKey.trim()) return;
    await new Promise(resolve => setTimeout(resolve, 1000));
    addProvider({ id: Date.now().toString(), name: selectedProvider, type: selectedProvider.toLowerCase(), apiKey: apiKey, isActive: true });
    setSelectedProvider('');
    setApiKey('');
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">AI Providers</h1>
          <p className="text-muted-foreground">Manage your AI service providers</p>
        </div>
        <Card className="p-6">
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Add New Provider</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Provider Type</label>
                <select value={selectedProvider} onChange={(e) => setSelectedProvider(e.target.value)} className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm">
                  <option value="">Select a provider</option>
                  <option value="OpenAI">OpenAI</option>
                  <option value="Anthropic">Anthropic</option>
                  <option value="Mistral">Mistral</option>
                  <option value="Google">Google</option>
                  <option value="Perplexity">Perplexity</option>
                  <option value="Local">Local (GGUF)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">API Key</label>
                <Input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="sk-..." />
              </div>
            </div>
            <Button onClick={handleAddProvider} disabled={!selectedProvider || !apiKey.trim()}>{'Add Provider'}</Button>
          </div>
        </Card>
        <Card className="p-6">
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Your Providers</h2>
            {providers.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">No providers added yet</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {providers.map(provider => (
                  <div key={provider.id} className={`border rounded-lg p-4 cursor-pointer transition-all ${activeProvider === provider.id ? 'ring-2 ring-primary border-primary' : 'hover:border-muted'}`} onClick={() => setActiveProvider(provider.id)}>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold">{provider.name}</h3>
                      {activeProvider === provider.id && <Badge variant="default">Active</Badge>}
                    </div>
                    <p className="text-sm text-muted-foreground mb-3">{provider.type}</p>
                    <div className="flex gap-2">
                      <Badge variant={provider.isActive ? 'default' : 'secondary'}>{provider.isActive ? 'Connected' : 'Disconnected'}</Badge>
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