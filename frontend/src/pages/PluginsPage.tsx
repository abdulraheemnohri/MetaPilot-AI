import React, { useState, useEffect } from 'react';
import { pluginsService } from '../services/plugins';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

const PluginsPage: React.FC = () => {
  const [plugins, setPlugins] = useState<any[]>([]);

  useEffect(() => {
    pluginsService.listPlugins().then(res => setPlugins(res.items));
  }, []);

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Plugin Marketplace</h1>
        <p className="text-muted-foreground">Extend MetaPilot AI with custom tools and MCP servers</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plugins.length === 0 ? (
          <div className="col-span-full py-12 text-center text-muted-foreground border-2 border-dashed rounded-lg">
            No plugins installed. Visit the directory to discover more.
          </div>
        ) : (
          plugins.map(plugin => (
            <Card key={plugin.id}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg">{plugin.name}</CardTitle>
                <Badge variant={plugin.isEnabled ? "default" : "secondary"}>
                  {plugin.isEnabled ? "Enabled" : "Disabled"}
                </Badge>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">{plugin.description}</p>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline">Configure</Button>
                  <Button size="sm" variant="destructive">Uninstall</Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export { PluginsPage };
