import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../store/useChatStore';
import { useProvidersStore } from '../store/useProvidersStore';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Card } from '../components/ui/Card';

export function ChatPage() {
  const { messages, addMessage, clearMessages, isLoading } = useChatStore();
  const { activeProvider, providers } = useProvidersStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    addMessage({ role: 'user', content: input.trim() });
    setInput('');
    setTimeout(() => {
      addMessage({ role: 'assistant', content: `Response from ${activeProvider}: ${input.trim()}` });
    }, 1000);
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full p-4 space-y-4">
      <div className="flex-1 overflow-y-auto space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <h2 className="text-2xl font-bold mb-2">MetaPilot AI</h2>
            <p className="text-center max-w-md">Start a conversation with multiple AI providers</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <Card key={index} className={`p-4 max-w-[80%] ${msg.role === 'user' ? 'ml-auto bg-primary/10' : 'mr-auto bg-muted'}`}>
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </Card>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="sticky bottom-0 bg-background border-t border-border p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Select value={activeProvider} onValueChange={(value) => {}} className="w-48">
            {providers.map(provider => (<option key={provider.id} value={provider.id}>{provider.name}</option>))}
          </Select>
          <Input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type your message..." className="flex-1" disabled={isLoading} />
          <Button type="submit" disabled={isLoading || !input.trim()}>{isLoading ? 'Thinking...' : 'Send'}</Button>
        </form>
      </div>
    </div>
  );
}