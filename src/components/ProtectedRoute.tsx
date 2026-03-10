/**
 * Componente para proteger rotas que exigem autenticação
 */
import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth, useAuthLoading } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  redirectTo?: string;
  requireAdmin?: boolean;
}

export default function ProtectedRoute({
  children,
  redirectTo = '/login',
  requireAdmin = false,
}: ProtectedRouteProps) {
  const { state } = useAuth();
  const isLoading = useAuthLoading();
  const location = useLocation();

  // Se estiver carregando, mostrar spinner
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center space-y-4">
          {/* Spinner */}
          <div className="relative">
            <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
          </div>
          
          {/* Texto de carregamento */}
          <div className="text-center">
            <p className="text-gray-600 font-medium">Carregando...</p>
            <p className="text-gray-500 text-sm mt-1">Verificando sua autenticação</p>
          </div>
        </div>
      </div>
    );
  }

  // Se não estiver autenticado, redirecionar para login
  if (!state.isAuthenticated) {
    // Salvar a URL atual para redirecionar após o login
    const returnUrl = encodeURIComponent(location.pathname + location.search);
    return (
      <Navigate 
        to={`${redirectTo}?returnUrl=${returnUrl}`} 
        replace 
      />
    );
  }

  // Se exigir admin e não for admin, redirecionar
  if (requireAdmin && !state.user?.is_superuser) {
    return (
      <Navigate 
        to="/unauthorized" 
        replace 
      />
    );
  }

  // Se tudo estiver ok, renderizar os filhos
  return <>{children}</>;
}

/**
 * Componente para rotas públicas (só acessíveis se não estiver logado)
 */
interface PublicRouteProps {
  children: ReactNode;
  redirectTo?: string;
}

export function PublicRoute({
  children,
  redirectTo = '/dashboard',
}: PublicRouteProps) {
  const { state } = useAuth();
  const isLoading = useAuthLoading();

  // Se estiver carregando, mostrar spinner
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center space-y-4">
          <div className="relative">
            <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
          </div>
          <div className="text-center">
            <p className="text-gray-600 font-medium">Carregando...</p>
          </div>
        </div>
      </div>
    );
  }

  // Se já estiver autenticado, redirecionar
  if (state.isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  // Se não estiver autenticado, renderizar
  return <>{children}</>;
}

/**
 * Componente para verificar permissões específicas
 */
interface PermissionRouteProps {
  children: ReactNode;
  permissions: string[];
  requireAll?: boolean; // Se true, exige todas as permissões; se false, exige qualquer uma
  fallback?: ReactNode;
}

export function PermissionRoute({
  children,
  permissions,
  requireAll = true,
  fallback = <div className="p-4 text-center text-gray-600">Acesso negado</div>,
}: PermissionRouteProps) {
  const { state } = useAuth();

  if (!state.isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Verificar permissões do usuário
  const userPermissions = state.user?.permissions || [];
  
  let hasPermission = false;
  
  if (requireAll) {
    // Exige todas as permissões
    hasPermission = permissions.every(permission => 
      userPermissions.includes(permission)
    );
  } else {
    // Exige qualquer uma das permissões
    hasPermission = permissions.some(permission => 
      userPermissions.includes(permission)
    );
  }

  return hasPermission ? <>{children}</> : <>{fallback}</>;
}

/**
 * Hook para verificar se usuário tem permissão específica
 */
export function usePermission(permission: string): boolean {
  const { state } = useAuth();
  
  if (!state.isAuthenticated) {
    return false;
  }
  
  const userPermissions = state.user?.permissions || [];
  return userPermissions.includes(permission);
}

/**
 * Hook para verificar se usuário é admin
 */
export function useIsAdmin(): boolean {
  const { state } = useAuth();
  return state.user?.is_superuser || false;
}

/**
 * Hook para verificar se usuário está verificado
 */
export function useIsVerified(): boolean {
  const { state } = useAuth();
  return state.user?.is_verified || false;
}

/**
 * Componente de Loading para autenticação
 */
export function AuthLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="flex flex-col items-center space-y-4">
        {/* Logo ou ícone */}
        <div className="w-16 h-16 bg-blue-600 rounded-lg flex items-center justify-center">
          <span className="text-white text-2xl font-bold">GP</span>
        </div>
        
        {/* Spinner */}
        <div className="relative">
          <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
        </div>
        
        {/* Texto */}
        <div className="text-center">
          <p className="text-gray-600 font-medium">Autenticando...</p>
          <p className="text-gray-500 text-sm mt-1">Aguarde um momento</p>
        </div>
      </div>
    </div>
  );
}

/**
 * Componente para página de acesso negado
 */
export function UnauthorizedPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8">
        <div className="text-center">
          {/* Ícone de acesso negado */}
          <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.932-3.021l-2.5-5.5A2.5 2.5 0 0014.062 5H9.938a2.5 2.5 0 00-2.288 1.479L5.15 11.979C4.58 13.333 5.042 15 6.582 15h10.836c1.54 0 2.502-1.667 1.932-3.021l-2.5-5.5z" />
            </svg>
          </div>
          
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Acesso Negado
          </h1>
          <p className="text-gray-600 mb-6">
            Você não tem permissão para acessar esta página.
          </p>
          
          <div className="space-y-4">
            <button
              onClick={() => window.history.back()}
              className="w-full px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              Voltar
            </button>
            
            <button
              onClick={() => window.location.href = '/dashboard'}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Ir para Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Componente para página não encontrada
 */
export function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="mb-4">
          <span className="text-6xl font-bold text-gray-300">404</span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Página Não Encontrada
        </h1>
        <p className="text-gray-600 mb-6">
          A página que você está procurando não existe.
        </p>
        
        <div className="space-y-4">
          <button
            onClick={() => window.history.back()}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
          >
            Voltar
          </button>
          
          <button
            onClick={() => window.location.href = '/dashboard'}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors ml-2"
          >
            Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
