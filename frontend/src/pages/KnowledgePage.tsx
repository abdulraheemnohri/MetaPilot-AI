import { useState } from 'react';
import { useKnowledgeStore } from '../store/useKnowledgeStore';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export function KnowledgePage() {
  const { documents, addDocument, deleteDocument } = useKnowledgeStore();
  const [file, setFile] = useState<File | null>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    await new Promise(resolve => setTimeout(resolve, 1000));
    addDocument({ id: Date.now().toString(), name: file.name, type: file.type, size: file.size, uploadedAt: new Date().toISOString() });
    setFile(null);
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Knowledge Base</h1>
          <p className="text-muted-foreground">Upload and manage documents for AI to learn from</p>
        </div>
        <Card className="p-6">
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Upload Document</h2>
            <div className="flex gap-4 items-end">
              <div className="flex-1">
                <Input type="file" onChange={handleFileUpload} className="border-0 p-0" />
                {file && <p className="text-sm text-muted-foreground mt-2">Selected: {file.name} ({Math.round(file.size / 1024)} KB)</p>}
              </div>
              <Button onClick={handleUpload} disabled={!file}>Upload</Button>
            </div>
          </div>
        </Card>
        <Card className="p-6">
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Your Documents</h2>
            {documents.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">No documents uploaded yet</p>
            ) : (
              <div className="space-y-3">
                {documents.map(doc => (
                  <div key={doc.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">📄</span>
                      <div>
                        <p className="font-medium">{doc.name}</p>
                        <p className="text-sm text-muted-foreground">{doc.type} • {(doc.size / 1024).toFixed(2)} KB</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" onClick={() => deleteDocument(doc.id)}>🗑️</Button>
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