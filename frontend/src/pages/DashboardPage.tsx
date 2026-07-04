import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/useAppStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Plus, Settings, Users, MessageSquare, Database, CPU } from 'lucide-react';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, stats } = useAppStore();

  const quickActions = [
    {
      title: 'New Chat',
      description: 'Start a new conversation',
      icon: MessageSquare,
      action: () => navigate('/chat'),
      color: 'bg-blue-500',
    },
    {
      title: 'Knowledge Base',
      description: 'Manage your documents',
      icon: Database,
      action: () => navigate('/knowledge'),
      color: 'bg-green-500',
    },
    {
      title: 'Providers',
      description: 'Configure AI providers',
      icon: CPU,
      action: () => navigate('/providers'),
      color: 'bg-purple-500',
    },
    {
      title: 'Settings',
      description: 'Application settings',
      icon: Settings,
      action: () => navigate('/settings'),
      color: 'bg-gray-500',
    },
  ];

  const statCards = [
    {
      title: 'Total Chats',
      value: stats?.totalChats || 0,
      icon: MessageSquare,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
    },
    {
      title: 'Documents',
      value: stats?.totalDocuments || 0,
      icon: Database,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
    },
    {
      title: 'AI Providers',
      value: stats?.activeProviders || 0,
      icon: CPU,
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10',
    },
    {
      title: 'Tasks',
      value: stats?.pendingTasks || 0,
      icon: Users,
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
                <stat.icon className={stat.color + ' h-4 w-4'} />
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
                  <action.icon className="h-4 w-4 text-white" />
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
        <h2 className="text-2xl font-semibold mb-4">Recent Activity</h2>
        <Card>
          <CardHeader>
            <CardTitle>Coming Soon</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Recent chats and activity will be displayed here.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DashboardPage;