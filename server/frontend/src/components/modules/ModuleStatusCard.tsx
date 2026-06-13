import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface ModuleStatus {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'error';
  lastSeen: string;
  batteryLevel: number;
}

interface ModuleStatusCardProps {
  module: ModuleStatus;
  className?: string;
}

export const ModuleStatusCard = ({ module, className }: ModuleStatusCardProps) => {
  const getStatusColor = (status: ModuleStatus['status']) => {
    switch (status) {
      case 'online':
        return 'bg-green-500';
      case 'offline':
        return 'bg-gray-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getBatteryColor = (level: number) => {
    if (level > 75) return 'text-green-500';
    if (level > 25) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{module.name}</CardTitle>
        <Badge
          variant="secondary"
          className={cn('h-2 w-2 rounded-full', getStatusColor(module.status))}
        />
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Statut</span>
            <span className="text-sm font-medium capitalize">{module.status}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Dernière vue</span>
            <span className="text-sm font-medium">
              {new Date(module.lastSeen).toLocaleString()}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Batterie</span>
            <span className={cn('text-sm font-medium', getBatteryColor(module.batteryLevel))}>
              {module.batteryLevel}%
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}; 