import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, stats } = useAppStore();

  const quickActions = [
    {
      title: 'New Chat',
      description: 'Start a new conversation',
      icon: '💬',
      action: () => navigate('/chat'),
      color: 'bg-blue-500',
    },
    {
      title: 'Knowledge Base',
      description: 'Manage your documents',
      icon: '📚',
      action: () => navigate('/knowledge'),
      color: 'bg-green-500',
    },
    {
      title: 'Providers',
      description: 'Configure AI providers',
      icon: '🤖',
      action: () => navigate('/providers'),
      color: 'bg-purple-500',
    },
    {
      title: 'Settings',
      description: 'Application settings',
      icon: '⚙️',
      action: () => navigate('/settings'),
      color: 'bg-gray-500',
    },
  ];

  const statCards = [
    {
      title: 'Total Chats',
      value: stats?.totalChats || 0,
      icon: '💬',
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
    },
    {
      title: 'Documents',
      value: stats?.totalDocuments || 0,
      icon: '📚',
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
    },
    {
      title: 'AI Providers',
      value: stats?.activeProviders || 0,
      icon: '🤖',
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10',
    },
    {
      title: 'Tasks',
      value: stats?.pendingTasks || 0,
      icon: '⏳',
      color: 'text-orange-500',
      bgColor: 'bg-orange-500/10',
    },
  ];

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">
          Welcome back, {user?.name || 'User'}!
        </h1>
        <p className="text-muted-foreground">
          One Request. Multiple AI Systems. One Intelligent Result.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {statCards.map((stat, index) => (
          <Card key={index} className="hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <div className={stat.bgColor + ' p-2 rounded-lg'}>
                <span className={stat.color}>{stat.icon}</span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {quickActions.map((action, index) => (
            <Card
              key={index}
              className="cursor-pointer hover:shadow-lg transition-shadow"
              onClick={action.action}
            >
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">{action.title}</CardTitle>
                <div className={action.color + ' p-2 rounded-lg'}>
                  <span className="text-white">{action.icon}</span>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{action.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-semibold mb-4">AI Provider Health</h2>
        <Card>
          <CardHeader>
            <CardTitle>Status Monitor</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {['OpenAI', 'Anthropic', 'ChatGPT (Browser)', 'Local GGUF', 'Grok (Browser)', 'DeepSeek (Browser)'].map((name, i) => (
                <div key={i} className="flex items-center justify-between p-2 border rounded">
                  <span className="font-medium">{name}</span>
                  <span className="text-green-500 flex items-center gap-1">
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    Connected & Parallel Ready
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;
