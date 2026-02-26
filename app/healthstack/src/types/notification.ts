export interface NotificationItem {
  id: string;
  type: 'medication' | 'news' | 'analysis';
  title: string;
  body: string;
  timestamp: number;
  read: boolean;
}
