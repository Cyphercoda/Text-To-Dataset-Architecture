/**
 * Login Page Component
 * User authentication with MFA support
 */

import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';

// Components
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import LoadingSpinner from '../../components/ui/LoadingSpinner';

// Services and Stores  
import { useAppStore } from '../../stores/appStore';
import { cognitoAuthService } from '../../services/awsIntegration';

// Icons
import {
  EyeIcon,
  EyeSlashIcon,
  UserIcon,
  LockClosedIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';

// Validation schema
const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  mfaCode: z.string().optional(),
  rememberMe: z.boolean().default(false),
});

type LoginFormData = z.infer<typeof loginSchema>;

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAppStore();
  
  const [showPassword, setShowPassword] = useState(false);
  const [requiresMfa, setRequiresMfa] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const from = (location.state as any)?.from?.pathname || '/dashboard';

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setError,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      rememberMe: false,
    },
  });

  const email = watch('email');
  const password = watch('password');

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);

    try {
      if (requiresMfa && !data.mfaCode) {
        setError('mfaCode', {
          message: 'MFA code is required',
        });
        return;
      }

      // Attempt login with Cognito
      const authResult = await cognitoAuthService.signIn(
        data.email,
        data.password,
        data.mfaCode
      );

      if (!authResult) {
        setRequiresMfa(true);
        toast.success('Please enter your MFA code');
        return;
      }

      // Update app store with authenticated user
      await login({
        accessToken: authResult.AccessToken!,
        refreshToken: authResult.RefreshToken!,
        idToken: authResult.IdToken!,
        expiresIn: authResult.ExpiresIn!,
        rememberMe: data.rememberMe,
      });

      toast.success('Welcome back!');
      navigate(from, { replace: true });

    } catch (error: any) {
      console.error('Login error:', error);
      
      // Handle specific error cases
      if (error.name === 'UserNotConfirmedException') {
        toast.error('Please verify your email address first');
        navigate('/auth/verify-email', { 
          state: { email: data.email } 
        });
      } else if (error.name === 'NotAuthorizedException') {
        setError('password', {
          message: 'Invalid email or password',
        });
      } else if (error.name === 'UserNotFoundException') {
        setError('email', {
          message: 'No account found with this email address',
        });
      } else if (error.name === 'TooManyRequestsException') {
        toast.error('Too many failed attempts. Please try again later.');
      } else {
        toast.error(error.message || 'Login failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Text-to-Dataset Platform
          </h1>
          <h2 className="text-xl text-gray-600">
            Sign in to your account
          </h2>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Email Input */}
            <Input
              {...register('email')}
              type="email"
              label="Email address"
              placeholder="Enter your email"
              error={errors.email?.message}
              leftIcon={<UserIcon />}
              fullWidth
              disabled={isLoading}
            />

            {/* Password Input */}
            <Input
              {...register('password')}
              type={showPassword ? 'text' : 'password'}
              label="Password"
              placeholder="Enter your password"
              error={errors.password?.message}
              leftIcon={<LockClosedIcon />}
              rightIcon={
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeSlashIcon /> : <EyeIcon />}
                </button>
              }
              fullWidth
              disabled={isLoading}
            />

            {/* MFA Code Input */}
            {requiresMfa && (
              <Input
                {...register('mfaCode')}
                type="text"
                label="MFA Code"
                placeholder="Enter 6-digit code"
                error={errors.mfaCode?.message}
                leftIcon={<ShieldCheckIcon />}
                maxLength={6}
                fullWidth
                disabled={isLoading}
                hint="Enter the code from your authenticator app"
              />
            )}

            {/* Remember Me Checkbox */}
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  {...register('rememberMe')}
                  id="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  disabled={isLoading}
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                  Remember me
                </label>
              </div>

              <Link
                to="/auth/forgot-password"
                className="text-sm text-blue-600 hover:text-blue-500"
              >
                Forgot your password?
              </Link>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              fullWidth
              loading={isLoading}
              disabled={!email || !password || isLoading}
            >
              {requiresMfa ? 'Verify & Sign In' : 'Sign In'}
            </Button>
          </form>

          {/* Divider */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Don't have an account?</span>
              </div>
            </div>

            <div className="mt-6">
              <Link to="/auth/register">
                <Button variant="outline" fullWidth>
                  Create new account
                </Button>
              </Link>
            </div>
          </div>

          {/* Help Text */}
          <div className="mt-6 text-center">
            <p className="text-xs text-gray-500">
              By signing in, you agree to our{' '}
              <a href="/terms" className="text-blue-600 hover:text-blue-500">
                Terms of Service
              </a>{' '}
              and{' '}
              <a href="/privacy" className="text-blue-600 hover:text-blue-500">
                Privacy Policy
              </a>
            </p>
          </div>
        </div>

        {/* Demo Credentials */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h3 className="text-sm font-medium text-yellow-800 mb-2">
              Demo Credentials
            </h3>
            <div className="text-xs text-yellow-700 space-y-1">
              <div>Email: demo@textdataset.com</div>
              <div>Password: DemoPassword123!</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LoginPage;