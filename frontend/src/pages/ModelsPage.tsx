import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';

export function ModelsPage() {
  const [models, setModels] = useState<any[]>([]);
  const [repoId, setRepoId] = useState('TheBloke/Llama-2-7B-Chat-GGUF');
  const [filename, setFilename] = useState('llama-2-7b-chat.Q4_K_M.gguf');
  const [isDownloading, setIsDownloading] = useState(false);

  const fetchModels = async () => {
    const res = await apiService.get<any[]>('/api/models/');
    if (res.success) setModels(res.data || []);
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      const res = await apiService.post('/api/models/download', { repo_id: repoId, filename });
      if (res.success) {
        alert('Download started/completed successfully!');
        fetchModels();
      }
    } catch (e) {
      alert('Download failed');
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Local Models</h1>
        <p className="text-muted-foreground">Download and manage GGUF models from Hugging Face</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card className="lg:col-span-1 h-fit">
          <CardHeader><CardTitle>Download from Hugging Face</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Repo ID</label>
              <Input value={repoId} onChange={(e) => setRepoId(e.target.value)} placeholder="Username/Repo" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Filename</label>
              <Input value={filename} onChange={(e) => setFilename(e.target.value)} placeholder="model.gguf" />
            </div>
            <Button className="w-full" onClick={handleDownload} disabled={isDownloading}>
              {isDownloading ? 'Downloading...' : 'Start Download'}
            </Button>
          </CardContent>
        </Card>

        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-semibold">Available Local Models</h2>
          {models.length === 0 ? (
            <div className="text-center py-12 border-2 border-dashed rounded-lg text-muted-foreground">
              No models downloaded yet.
            </div>
          ) : (
            models.map(m => (
              <Card key={m.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="py-4">
                  <div className="flex justify-between items-center">
                    <CardTitle className="text-lg">{m.name}</CardTitle>
                    <Badge variant={m.is_loaded ? "default" : "secondary"}>
                      {m.is_loaded ? "Loaded" : "Cached"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="pb-4 text-sm text-muted-foreground">
                  <p className="truncate">{m.path}</p>
                  <p className="mt-1 font-mono text-[10px]">{m.type.toUpperCase()}</p>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
