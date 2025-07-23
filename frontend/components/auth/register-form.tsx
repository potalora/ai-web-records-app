'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Eye, EyeOff } from 'lucide-react';
import { ApiError } from '@/lib/api-client';

interface RegisterFormProps {
  onSwitchToLogin?: () => void;
}

export function RegisterForm({ onSwitchToLogin }: RegisterFormProps) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    dateOfBirth: '',
    phone: '',
    acceptTerms: false,
    acceptPrivacy: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { register, loading } = useAuth();
  const router = useRouter();

  const handleInputChange = (field: string, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (error) setError(null); // Clear error when user starts typing
  };

  const validateForm = () => {
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return false;
    }

    if (!formData.acceptTerms) {
      setError('You must accept the Terms of Service');
      return false;
    }

    if (!formData.acceptPrivacy) {
      setError('You must accept the Privacy Policy');
      return false;
    }

    // Basic date validation
    const birthDate = new Date(formData.dateOfBirth);
    const now = new Date();
    if (birthDate >= now) {
      setError('Please enter a valid birth date');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      return;
    }

    try {
      await register({
        email: formData.email,
        password: formData.password,
        firstName: formData.firstName,
        lastName: formData.lastName,
        dateOfBirth: formData.dateOfBirth,
        phone: formData.phone || undefined,
        acceptTerms: formData.acceptTerms,
        acceptPrivacy: formData.acceptPrivacy,
      });
      router.push('/dashboard');
    } catch (error) {
      const apiError = error as ApiError;
      setError(apiError.detail || 'Registration failed');
    }
  };

  const isFormValid = 
    formData.email.length > 0 &&
    formData.password.length > 0 &&
    formData.confirmPassword.length > 0 &&
    formData.firstName.length > 0 &&
    formData.lastName.length > 0 &&
    formData.dateOfBirth.length > 0 &&
    formData.acceptTerms &&
    formData.acceptPrivacy;

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold text-center">
          Create Account
        </CardTitle>
        <CardDescription className="text-center">
          Join us to securely manage your health records
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="firstName">First Name</Label>
              <Input
                id="firstName"
                value={formData.firstName}
                onChange={(e) => handleInputChange('firstName', e.target.value)}
                placeholder="John"
                required
                autoComplete="given-name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lastName">Last Name</Label>
              <Input
                id="lastName"
                value={formData.lastName}
                onChange={(e) => handleInputChange('lastName', e.target.value)}
                placeholder="Doe"
                required
                autoComplete="family-name"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              placeholder="john.doe@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="dateOfBirth">Date of Birth</Label>
            <Input
              id="dateOfBirth"
              type="date"
              value={formData.dateOfBirth}
              onChange={(e) => handleInputChange('dateOfBirth', e.target.value)}
              required
              max={new Date().toISOString().split('T')[0]} // Can't be future date
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">Phone Number (Optional)</Label>
            <Input
              id="phone"
              type="tel"
              value={formData.phone}
              onChange={(e) => handleInputChange('phone', e.target.value)}
              placeholder="+1 (555) 123-4567"
              autoComplete="tel"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                placeholder="Create a strong password"
                required
                autoComplete="new-password"
                minLength={8}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-2 top-1/2 -translate-y-1/2 h-auto p-1"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <div className="relative">
              <Input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                value={formData.confirmPassword}
                onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                placeholder="Confirm your password"
                required
                autoComplete="new-password"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-2 top-1/2 -translate-y-1/2 h-auto p-1"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="acceptTerms"
                checked={formData.acceptTerms}
                onCheckedChange={(checked) => 
                  handleInputChange('acceptTerms', checked as boolean)
                }
              />
              <Label htmlFor="acceptTerms" className="text-sm">
                I accept the{' '}
                <Button variant="link" className="p-0 h-auto text-sm">
                  Terms of Service
                </Button>
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="acceptPrivacy"
                checked={formData.acceptPrivacy}
                onCheckedChange={(checked) => 
                  handleInputChange('acceptPrivacy', checked as boolean)
                }
              />
              <Label htmlFor="acceptPrivacy" className="text-sm">
                I accept the{' '}
                <Button variant="link" className="p-0 h-auto text-sm">
                  Privacy Policy
                </Button>
              </Label>
            </div>
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={!isFormValid || loading}
          >
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Create Account
          </Button>

          {onSwitchToLogin && (
            <div className="text-center text-sm">
              <span className="text-muted-foreground">Already have an account? </span>
              <Button
                type="button"
                variant="link"
                className="p-0 h-auto font-medium"
                onClick={onSwitchToLogin}
              >
                Sign in
              </Button>
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
}