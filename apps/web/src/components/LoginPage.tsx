import { useState } from 'react';
import { Lock, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AcesLogo } from '@/components/shared/AcesLogo';
import { ApiError } from '@/services/api';
import { PasswordRequirements, validatePassword } from '@/components/shared/PasswordRequirements';

type ErrorType = 'credentials' | 'locked' | 'rate_limit' | 'password' | 'pending_approval' | null;
type ViewMode = 'login' | 'register';

export function LoginPage() {
  const { signIn, signUp, loading } = useAuth();
  const [mode, setMode] = useState<ViewMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [errorType, setErrorType] = useState<ErrorType>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [lockoutMinutes, setLockoutMinutes] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);

  const resetState = () => {
    setErrorType(null);
    setErrorMessage('');
    setRegistrationSuccess(false);
  };

  const switchMode = (newMode: ViewMode) => {
    setMode(newMode);
    setEmail('');
    setPassword('');
    setName('');
    resetState();
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    resetState();
    setIsLoading(true);

    try {
      await signIn(email, password);
    } catch (err) {
      console.error('Login error:', err);

      if (err instanceof ApiError) {
        switch (err.status) {
          case 423: // Account locked
            setErrorType('locked');
            // Extract minutes from message like "Try again in X minutes"
            const minuteMatch = err.detail.match(/(\d+)\s*minute/);
            setLockoutMinutes(minuteMatch ? parseInt(minuteMatch[1]) : 15);
            setErrorMessage(err.detail);
            break;
          case 429: // Rate limited
            setErrorType('rate_limit');
            setErrorMessage(err.detail);
            break;
          case 403: // Pending approval
            setErrorType('pending_approval');
            setErrorMessage(err.detail);
            break;
          case 400: // Password validation error
            setErrorType('password');
            setErrorMessage(err.detail);
            break;
          case 401: // Invalid credentials
          default:
            setErrorType('credentials');
            setErrorMessage('Invalid email or password');
            break;
        }
      } else {
        setErrorType('credentials');
        setErrorMessage('An error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    resetState();

    if (!validatePassword(password)) {
      setErrorType('password');
      setErrorMessage('Password does not meet all requirements.');
      return;
    }

    setIsLoading(true);

    try {
      await signUp(email, password, name);
      setRegistrationSuccess(true);
    } catch (err) {
      console.error('Registration error:', err);

      if (err instanceof ApiError) {
        if (err.status === 429) {
          setErrorType('rate_limit');
          setErrorMessage(err.detail);
        } else {
          setErrorType('password');
          setErrorMessage(err.detail);
        }
      } else {
        setErrorType('credentials');
        setErrorMessage('An error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Quick login buttons for testing
  const quickLogin = (userEmail: string, userPassword: string) => {
    setEmail(userEmail);
    setPassword(userPassword);
    resetState();
    setTimeout(() => {
      signIn(userEmail, userPassword).catch((err) => {
        if (err instanceof ApiError) {
          if (err.status === 423) {
            setErrorType('locked');
            const minuteMatch = err.detail.match(/(\d+)\s*minute/);
            setLockoutMinutes(minuteMatch ? parseInt(minuteMatch[1]) : 15);
          } else if (err.status === 429) {
            setErrorType('rate_limit');
          } else if (err.status === 403) {
            setErrorType('pending_approval');
          } else {
            setErrorType('credentials');
          }
          setErrorMessage(err.detail);
        } else {
          setErrorType('credentials');
          setErrorMessage('Login failed');
        }
        console.error(err);
      });
    }, 100);
  };

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-slate-100">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-slate-100">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <AcesLogo size="lg" showText={true} />
            </div>
            <p className="text-slate-600 text-sm">
              Acquisition Contracting Enterprise System
            </p>
            <p className="text-slate-500 text-xs mt-1">
              {mode === 'login'
                ? 'Sign in to access your procurement projects'
                : 'Create an account to get started'}
            </p>
          </div>

          {/* Registration Success Message */}
          {registrationSuccess && (
            <Alert className="mb-6 bg-green-50 border-green-200">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertTitle className="text-green-800">Account Created</AlertTitle>
              <AlertDescription className="text-green-700">
                Your account is pending admin approval. You will be able to sign in once an administrator approves your account.
              </AlertDescription>
            </Alert>
          )}

          {mode === 'login' ? (
            <>
              {/* Login Form */}
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="your.email@navy.mil"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="••••••••"
                    required
                  />
                </div>

                {errorType === 'locked' && (
                  <Alert variant="destructive" className="bg-red-50 border-red-200">
                    <Lock className="h-4 w-4" />
                    <AlertTitle>Account Locked</AlertTitle>
                    <AlertDescription>
                      Your account has been temporarily locked due to too many failed login attempts.
                      Please try again in {lockoutMinutes} minute{lockoutMinutes !== 1 ? 's' : ''}.
                    </AlertDescription>
                  </Alert>
                )}

                {errorType === 'rate_limit' && (
                  <Alert variant="destructive" className="bg-amber-50 border-amber-200">
                    <Clock className="h-4 w-4 text-amber-600" />
                    <AlertTitle className="text-amber-800">Rate Limited</AlertTitle>
                    <AlertDescription className="text-amber-700">
                      Too many requests. Please wait a moment before trying again.
                    </AlertDescription>
                  </Alert>
                )}

                {errorType === 'pending_approval' && (
                  <Alert className="bg-amber-50 border-amber-200">
                    <Clock className="h-4 w-4 text-amber-600" />
                    <AlertTitle className="text-amber-800">Pending Approval</AlertTitle>
                    <AlertDescription className="text-amber-700">
                      Your account is pending admin approval. Please contact an administrator.
                    </AlertDescription>
                  </Alert>
                )}

                {(errorType === 'credentials' || errorType === 'password') && (
                  <Alert variant="destructive" className="bg-red-50 border-red-200">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>Login Failed</AlertTitle>
                    <AlertDescription>{errorMessage}</AlertDescription>
                  </Alert>
                )}

                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-lg font-medium transition-colors"
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                      Signing in...
                    </span>
                  ) : (
                    'Sign In'
                  )}
                </Button>
              </form>

              {/* Register Link */}
              <div className="mt-4 text-center">
                <p className="text-sm text-slate-600">
                  Don't have an account?{' '}
                  <button
                    type="button"
                    onClick={() => switchMode('register')}
                    className="text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Register
                  </button>
                </p>
              </div>

              {/* Quick Login for Testing */}
              <div className="mt-8 pt-6 border-t border-slate-200">
                <p className="text-xs text-slate-500 text-center mb-3">
                  Quick Test Logins
                </p>
                <div className="space-y-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => quickLogin('john.contracting@navy.mil', 'SecureTest123!')}
                    className="w-full text-xs"
                  >
                    Contracting Officer
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => quickLogin('sarah.pm@navy.mil', 'SecureTest123!')}
                    className="w-full text-xs"
                  >
                    Program Manager
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => quickLogin('viewer@navy.mil', 'SecureTest123!')}
                    className="w-full text-xs"
                  >
                    Viewer
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <>
              {/* Register Form */}
              <form onSubmit={handleRegister} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="John Smith"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="your.email@navy.mil"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="••••••••"
                    required
                  />
                  <PasswordRequirements password={password} className="mt-2" />
                </div>

                {errorType === 'rate_limit' && (
                  <Alert variant="destructive" className="bg-amber-50 border-amber-200">
                    <Clock className="h-4 w-4 text-amber-600" />
                    <AlertTitle className="text-amber-800">Rate Limited</AlertTitle>
                    <AlertDescription className="text-amber-700">
                      Too many requests. Please wait a moment before trying again.
                    </AlertDescription>
                  </Alert>
                )}

                {(errorType === 'credentials' || errorType === 'password') && (
                  <Alert variant="destructive" className="bg-red-50 border-red-200">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>Registration Failed</AlertTitle>
                    <AlertDescription>{errorMessage}</AlertDescription>
                  </Alert>
                )}

                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-lg font-medium transition-colors"
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                      Creating account...
                    </span>
                  ) : (
                    'Register'
                  )}
                </Button>
              </form>

              {/* Back to Login Link */}
              <div className="mt-4 text-center">
                <p className="text-sm text-slate-600">
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => switchMode('login')}
                    className="text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Back to login
                  </button>
                </p>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-slate-500 mt-6">
          ACES - Acquisition Contracting Enterprise System v1.0
        </p>
      </div>
    </div>
  );
}
