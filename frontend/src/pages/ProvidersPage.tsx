import { useState } from 'react';
import { useProvidersStore } from '../store/useProvidersStore';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';

export function ProvidersPage() {
  const { providers, activeProvider, setActiveProvider, addProvider, removeProvider } = useProvidersStore();
  const [apiKey, setApiKey] = useState('');
  const [selectedProvider, setSelectedProvider] = useState('');

  const handleAddProvider = async () => {
    if (!selectedProvider || !apiKey.trim()) return;
    addProvider({
      id: selectedProvider.toLowerCase().replace(' ', '_'),
      name: selectedProvider,
      type: selectedProvider.toLowerCase(),
      apiKey: apiKey,
      isActive: true
    });
    setSelectedProvider('');
    setApiKey('');
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl animate-fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">AI Providers</h1>
        <p className="text-muted-foreground text-lg">Central control for API keys and browser-based orchestrations.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card className="lg:col-span-1 h-fit shadow-lg border-primary/10">
          <CardHeader>
            <CardTitle className="text-xl font-bold">Connect New AI</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-semibold mb-2 text-primary">Service Type</label>
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                className="w-full p-3 border rounded-xl bg-background focus:ring-2 focus:ring-primary outline-none transition-all"
              >
                <option value="">Select provider...</option>
                <optgroup label="API-based">
                  <option value="OpenAI">OpenAI (GPT-4o/o1)</option>
                  <option value="Anthropic">Anthropic (Claude 3.5)</option>
                  <option value="Mistral">Mistral AI</option>
                  <option value="Google">Google Gemini 1.5</option>
                </optgroup>
                <optgroup label="Browser-based">
                  <option value="ChatGPTBrowser">ChatGPT (Web)</option>
                  <option value="ClaudeBrowser">Claude (Web)</option>
                  <option value="GrokBrowser">Grok (Web)</option>
                  <option value="PerplexityBrowser">Perplexity (Web)</option>
                </optgroup>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold mb-2 text-primary">Credentials</label>
              <Input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="API Key or Session Token"
                className="rounded-xl p-3"
              />
              <p className="text-[10px] text-muted-foreground mt-2 italic px-1">MetaPilot encrypts keys locally. Never shared with our servers.</p>
            </div>
            <Button
              className="w-full py-6 rounded-xl font-bold text-lg shadow-primary/20 shadow-lg"
              onClick={handleAddProvider}
              disabled={!selectedProvider || !apiKey.trim()}
            >
              Link Assistant
            </Button>
          </CardContent>
        </Card>

        <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
          {providers.length === 0 ? (
            <div className="col-span-full py-20 text-center text-muted-foreground border-2 border-dashed rounded-2xl h-fit bg-muted/20">
              <div className="text-4xl mb-4">🔌</div>
              <p className="text-xl font-medium">No custom assistants connected</p>
              <p className="text-sm">Link an API or Web session to start orchestrating.</p>
            </div>
          ) : (
            providers.map(p => (
              <Card
                key={p.id}
                className={`transition-all duration-300 ${activeProvider === p.id ? "ring-2 ring-primary border-primary bg-primary/5" : "hover:shadow-md cursor-pointer border-transparent shadow-sm"}`}
                onClick={() => setActiveProvider(p.id)}
              >
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-center">
                    <CardTitle className="text-lg font-bold">{p.name}</CardTitle>
                    <Badge variant={p.isActive ? "default" : "secondary"} className={p.isActive ? "bg-green-500 hover:bg-green-600" : ""}>
                      {p.isActive ? "READY" : "OFFLINE"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-xs font-mono text-muted-foreground mb-4 opacity-70">ID: {p.id}</div>
                  <div className="flex gap-2 justify-end">
                    <Button size="sm" variant={activeProvider === p.id ? "default" : "outline"} className="rounded-lg">
                      {activeProvider === p.id ? "Active" : "Activate"}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-destructive hover:bg-destructive/10 rounded-lg"
                      onClick={(e) => { e.stopPropagation(); removeProvider(p.id); }}
                    >
                      Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
