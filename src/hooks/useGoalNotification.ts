/**
 * Hook para gerenciar notificações de metas atingidas
 */
import { useState, useEffect, useCallback } from 'react';
import { calendarService } from '../services/calendarService';
import { accountService } from '../services/accountService';

interface GoalNotification {
  id: string;
  type: 'monthly' | 'biweekly';
  title: string;
  message: string;
  amount: number;
  percentage: number;
  achieved_at: string;
  dismissed: boolean;
}

interface UseGoalNotificationReturn {
  notifications: GoalNotification[];
  showNotifications: boolean;
  dismissNotification: (id: string) => void;
  dismissAllNotifications: () => void;
  checkGoals: () => Promise<void>;
}

const STORAGE_KEY = 'gpfx_goal_notifications';
const DISMISSED_KEY = 'gpfx_dismissed_goals';

export function useGoalNotification(): UseGoalNotificationReturn {
  const [notifications, setNotifications] = useState<GoalNotification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [accounts, setAccounts] = useState<any[]>([]);

  // Carregar contas ao montar
  useEffect(() => {
    loadAccounts();
  }, []);

  // Verificar metas ao carregar e a cada mudança de página
  useEffect(() => {
    checkGoals();
    
    // Verificar a cada 5 minutos
    const interval = setInterval(checkGoals, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, [accounts]);

  const loadAccounts = async () => {
    try {
      const accountsList = await accountService.listAccounts();
      setAccounts(accountsList);
    } catch (error) {
      console.error('Error loading accounts:', error);
    }
  };

  const checkGoals = useCallback(async () => {
    if (accounts.length === 0) return;

    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1;
    
    const dismissedGoals = getDismissedGoals();
    const newNotifications: GoalNotification[] = [];

    for (const account of accounts) {
      try {
        // Verificar meta mensal
        const monthlyGoal = await calendarService.checkGoalReached(
          currentYear,
          currentMonth,
          account.id
        );

        if (monthlyGoal.monthly && monthlyGoal.monthly.achieved) {
          const notificationId = `monthly_${account.id}_${currentYear}_${currentMonth}`;
          
          if (!isGoalDismissed(notificationId, dismissedGoals)) {
            newNotifications.push({
              id: notificationId,
              type: 'monthly',
              title: 'Meta Mensal Atingida! 🎉',
              message: `Parabéns! Você atingiu sua meta mensal de ${monthlyGoal.monthly.goal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}`,
              amount: monthlyGoal.monthly.goal,
              percentage: monthlyGoal.monthly.percentage,
              achieved_at: new Date().toISOString(),
              dismissed: false,
            });
          }
        }

        // Verificar meta quinzenal
        if (monthlyGoal.biweekly && monthlyGoal.biweekly.achieved) {
          const notificationId = `biweekly_${account.id}_${currentYear}_${currentMonth}_${Math.ceil(currentMonth / 2)}`;
          
          if (!isGoalDismissed(notificationId, dismissedGoals)) {
            newNotifications.push({
              id: notificationId,
              type: 'biweekly',
              title: 'Meta Quinzenal Atingida! 🎉',
              message: `Excelente! Você atingiu sua meta quinzenal de ${monthlyGoal.biweekly.goal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}`,
              amount: monthlyGoal.biweekly.goal,
              percentage: monthlyGoal.biweekly.percentage,
              achieved_at: new Date().toISOString(),
              dismissed: false,
            });
          }
        }
      } catch (error) {
        console.error('Error checking goals for account:', account.id, error);
      }
    }

    if (newNotifications.length > 0) {
      setNotifications(prev => [...prev, ...newNotifications]);
      setShowNotifications(true);
      saveNotifications(newNotifications);
    }
  }, [accounts]);

  const getDismissedGoals = (): Set<string> => {
    try {
      const dismissed = localStorage.getItem(DISMISSED_KEY);
      return dismissed ? new Set(JSON.parse(dismissed)) : new Set();
    } catch (error) {
      console.error('Error loading dismissed goals:', error);
      return new Set();
    }
  };

  const isGoalDismissed = (goalId: string, dismissedGoals: Set<string>): boolean => {
    return dismissedGoals.has(goalId);
  };

  const saveNotifications = (newNotifications: GoalNotification[]) => {
    try {
      const existing = getStoredNotifications();
      const updated = [...existing, ...newNotifications];
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (error) {
      console.error('Error saving notifications:', error);
    }
  };

  const getStoredNotifications = (): GoalNotification[] => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.error('Error loading stored notifications:', error);
      return [];
    }
  };

  const dismissNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
    
    // Adicionar ao dismissed
    const dismissed = getDismissedGoals();
    dismissed.add(id);
    localStorage.setItem(DISMISSED_KEY, JSON.stringify([...dismissed]));
    
    // Remover do storage se não houver mais notificações
    const remaining = notifications.filter(n => n.id !== id);
    if (remaining.length === 0) {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [notifications]);

  const dismissAllNotifications = useCallback(() => {
    setNotifications([]);
    setShowNotifications(false);
    
    // Adicionar todos ao dismissed
    const dismissed = getDismissedGoals();
    notifications.forEach(n => dismissed.add(n.id));
    localStorage.setItem(DISMISSED_KEY, JSON.stringify([...dismissed]));
    
    // Limpar storage
    localStorage.removeItem(STORAGE_KEY);
  }, [notifications]);

  // Limpar notificações antigas (mais de 30 dias)
  useEffect(() => {
    const cleanupOldNotifications = () => {
      const stored = getStoredNotifications();
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      
      const validNotifications = stored.filter(n => 
        new Date(n.achieved_at) > thirtyDaysAgo
      );
      
      if (validNotifications.length !== stored.length) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(validNotifications));
        setNotifications(validNotifications);
      }
    };

    cleanupOldNotifications();
    
    // Executar a cada 24 horas
    const interval = setInterval(cleanupOldNotifications, 24 * 60 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);

  return {
    notifications,
    showNotifications,
    dismissNotification,
    dismissAllNotifications,
    checkGoals,
  };
}

/**
 * Componente para exibir banner de notificação de meta
 */
import React from 'react';
import { X, Trophy } from 'lucide-react';

interface GoalNotificationBannerProps {
  notification: {
    title: string;
    message: string;
    type: 'monthly' | 'biweekly';
  };
  onDismiss: () => void;
}

export function GoalNotificationBanner({ 
  notification, 
  onDismiss 
}: GoalNotificationBannerProps) {
  const bgColor = notification.type === 'monthly' 
    ? 'bg-green-50 border-green-200' 
    : 'bg-blue-50 border-blue-200';

  const textColor = notification.type === 'monthly' 
    ? 'text-green-800' 
    : 'text-blue-800';

  const iconColor = notification.type === 'monthly' 
    ? 'text-green-600' 
    : 'text-blue-600';

  return (
    <div className={`
      fixed top-0 left-0 right-0 z-50
      ${bgColor} border-b-2
      px-4 py-3
      flex items-center justify-between
      shadow-lg
    `}>
      <div className="flex items-center space-x-3">
        {/* Ícone */}
        <div className={`p-2 rounded-full ${iconColor}`}>
          <Trophy className="w-5 h-5" />
        </div>
        
        {/* Conteúdo */}
        <div>
          <h3 className={`font-bold ${textColor} text-sm`}>
            {notification.title}
          </h3>
          <p className={`${textColor} text-xs mt-1`}>
            {notification.message}
          </p>
        </div>
      </div>
      
      {/* Botão de fechar */}
      <button
        onClick={onDismiss}
        className={`
          p-1 rounded-full hover:bg-black hover:bg-opacity-10
          transition-colors
        `}
      >
        <X className={`w-4 h-4 ${textColor}`} />
      </button>
    </div>
  );
}

/**
 * Componente para exibir múltiplos banners de notificação
 */
export function GoalNotificationBanners() {
  const { 
    notifications, 
    showNotifications, 
    dismissNotification,
    dismissAllNotifications 
  } = useGoalNotification();

  if (!showNotifications || notifications.length === 0) {
    return null;
  }

  return (
    <>
      {notifications.map((notification, index) => (
        <div 
          key={notification.id}
          style={{ top: `${index * 80}px` }}
        >
          <GoalNotificationBanner
            notification={notification}
            onDismiss={() => dismissNotification(notification.id)}
          />
        </div>
      ))}
      
      {/* Botão para descartar todos */}
      {notifications.length > 1 && (
        <div 
          className="fixed top-4 right-4 z-50"
          style={{ top: `${notifications.length * 80 + 20}px` }}
        >
          <button
            onClick={dismissAllNotifications}
            className="px-3 py-2 bg-gray-600 text-white text-sm rounded-md hover:bg-gray-700 transition-colors"
          >
            Descartar Todas
          </button>
        </div>
      )}
    </>
  );
}
