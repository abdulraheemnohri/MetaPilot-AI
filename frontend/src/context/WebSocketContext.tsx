import { createContext, useContext, useEffect, useState, useRef, ReactNode } from 'react';

interface WebSocketMessage {
  type: string;
  data: unknown;
  timestamp: string;
}

interface WebSocketContextType {
  socket: WebSocket | null;
  isConnected: boolean;
  messages: WebSocketMessage[];
  sendMessage: (message: unknown) => void;
  connect: (url: string) => void;
  disconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: ReactNode;
  url?: string;
}

export function WebSocketProvider({ children, url }: WebSocketProviderProps) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const socketRef = useRef<WebSocket | null>(null);
  const messageQueueRef = useRef<unknown[]>([]);

  const connect = (customUrl?: string) => {
    const wsUrl = customUrl || url || `ws://${window.location.hostname}:8000`;
    
    if (socketRef.current) {
      socketRef.current.close();
    }

    const newSocket = new WebSocket(wsUrl);
    socketRef.current = newSocket;
    setSocket(newSocket);

    newSocket.onopen = () => {
      setIsConnected(true);
      while (messageQueueRef.current.length > 0) {
        const message = messageQueueRef.current.shift();
        if (message) {
          newSocket.send(JSON.stringify(message));
        }
      }
    };

    newSocket.onclose = () => {
      setIsConnected(false);
    };

    newSocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    newSocket.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        setMessages((prev) => [...prev, message]);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
  };

  const disconnect = () => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
      setSocket(null);
      setIsConnected(false);
    }
  };

  const sendMessage = (message: unknown) => {
    if (isConnected && socketRef.current) {
      try {
        socketRef.current.send(JSON.stringify(message));
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
      }
    } else {
      messageQueueRef.current.push(message);
    }
  };

  useEffect(() => {
    if (url) {
      connect(url);
    }
    
    return () => {
      disconnect();
    };
  }, [url]);

  const value: WebSocketContextType = {
    socket,
    isConnected,
    messages,
    sendMessage,
    connect,
    disconnect,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
}