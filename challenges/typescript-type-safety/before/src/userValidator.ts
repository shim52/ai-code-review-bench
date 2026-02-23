interface User {
  id: string;
  name: string;
  email: string;
  age: number;
  roles: string[];
}

export class UserValidator {
  validateUser(user: User): boolean {
    if (!user.id || typeof user.id !== 'string') {
      return false;
    }

    if (!user.name || typeof user.name !== 'string') {
      return false;
    }

    if (!user.email || !this.isValidEmail(user.email)) {
      return false;
    }

    if (typeof user.age !== 'number' || user.age < 0 || user.age > 150) {
      return false;
    }

    if (!Array.isArray(user.roles)) {
      return false;
    }

    return true;
  }

  private isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  getUserPermissions(user: User): string[] {
    const permissions: string[] = [];

    for (const role of user.roles) {
      switch (role) {
        case 'admin':
          permissions.push('read', 'write', 'delete', 'manage_users');
          break;
        case 'editor':
          permissions.push('read', 'write');
          break;
        case 'viewer':
          permissions.push('read');
          break;
      }
    }

    return [...new Set(permissions)];
  }
}