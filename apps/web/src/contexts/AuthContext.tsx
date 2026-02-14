import { createContext, useContext, useEffect, useState } from 'react';
import { authApi, projectsApi } from '@/services/api';

type UserRole = 'admin' | 'contracting_officer' | 'program_manager' | 'approver' | 'viewer';

interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  department?: string;
  notification_preferences: {
    email: boolean;
    in_app: boolean;
    deadline_days: number[];
  };
  is_active: boolean;
  created_at: string;
}

interface AuthContextType {
  user: AuthUser | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name: string) => Promise<{ message: string }>;
  signOut: () => Promise<void>;
  hasRole: (roles: UserRole | UserRole[]) => boolean;
  canAccessProject: (projectId: string) => Promise<boolean>;
  canEditProject: (projectId: string) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('auth_token');
    if (token) {
      authApi.me()
        .then((userData) => setUser(userData as AuthUser))
        .catch(() => {
          // Token invalid, clear it
          localStorage.removeItem('auth_token');
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const signIn = async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    setUser(response.user as AuthUser);
  };

  const signUp = async (email: string, password: string, name: string) => {
    const response = await authApi.register(email, password, name, 'viewer');
    return { message: response.message };
  };

  const signOut = async () => {
    authApi.logout();
    setUser(null);
  };

  const hasRole = (roles: UserRole | UserRole[]) => {
    if (!user?.role) return false;
    const roleArray = Array.isArray(roles) ? roles : [roles];
    return roleArray.includes(user.role);
  };

  const canAccessProject = async (projectId: string) => {
    if (!user) return false;

    try {
      const project = await projectsApi.get(projectId);
      return !!project;
    } catch (error) {
      return false;
    }
  };

  const canEditProject = async (projectId: string) => {
    if (!user) return false;

    try {
      const project = await projectsApi.get(projectId);

      // User can edit if they are the contracting officer or creator
      if (project.contracting_officer_id === user.id || project.created_by === user.id) {
        return true;
      }

      // Also allow program managers and contracting officers to edit
      return hasRole(['contracting_officer', 'program_manager']);
    } catch (error) {
      return false;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signIn,
        signUp,
        signOut,
        hasRole,
        canAccessProject,
        canEditProject,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
