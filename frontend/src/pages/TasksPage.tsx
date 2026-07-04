import { useTasksStore } from '../store/useTasksStore';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export function TasksPage() {
  const { tasks, getTasksByStatus } = useTasksStore();
  const statusConfig = {
    running: { label: 'Running', color: 'bg-blue-100 text-blue-800', icon: '🔄' },
    completed: { label: 'Completed', color: 'bg-green-100 text-green-800', icon: '✅' },
    failed: { label: 'Failed', color: 'bg-red-100 text-red-800', icon: '❌' },
    pending: { label: 'Pending', color: 'bg-yellow-100 text-yellow-800', icon: '⏳' },
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Tasks</h1>
          <p className="text-muted-foreground">Monitor background tasks and processing jobs</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(statusConfig).map(([status, config]) => {
            const tasks = getTasksByStatus(status as any);
            return (
              <Card key={status} className="p-4">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{config.icon}</span>
                    <span className="font-medium">{config.label}</span>
                  </div>
                  <p className={`text-3xl font-bold ${config.color}`}>{tasks.length}</p>
                </div>
              </Card>
            );
          })}
        </div>
        <Card className="p-6">
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">All Tasks</h2>
            {tasks.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">No tasks found</p>
            ) : (
              <div className="space-y-3">
                {tasks.map(task => {
                  const config = statusConfig[task.status as keyof typeof statusConfig];
                  return (
                    <div key={task.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <span className="text-xl">{config.icon}</span>
                        <div>
                          <p className="font-medium">{task.title}</p>
                          <p className="text-sm text-muted-foreground">{task.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={task.status === 'failed' ? 'destructive' : 'secondary'}>{config.label}</Badge>
                        <span className="text-sm text-muted-foreground">{task.progress}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}