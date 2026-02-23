interface User {
  id: string;
  name: string;
  email: string;
  age: number;
  roles: string[];
  metadata?: any;
}

export class UserValidator {
  validateUser(data: any): boolean {
    const user = data as User;

    if (!user.id) {
      return false;
    }

    if (!user.name) {
      return false;
    }

    if (!user.email || !this.isValidEmail(user.email)) {
      return false;
    }

    if (user.age < 0 || user.age > 150) {
      return false;
    }

    if (!user.roles) {
      return false;
    }

    return true;
  }

  private isValidEmail(email: any): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  getUserPermissions(user: any): string[] {
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

    // Add custom permissions from metadata
    if (user.metadata?.customPermissions) {
      permissions.push(...user.metadata.customPermissions);
    }

    return [...new Set(permissions)];
  }

  processUserBatch(users: any[]): User[] {
    const validUsers: User[] = [];

    users.forEach((userData) => {
      if (this.validateUser(userData)) {
        validUsers.push(userData as User);
      }
    });

    return validUsers;
  }

  // New method for flexible user updates
  updateUserField(user: User, field: string, value: any): void {
    (user as any)[field] = value;
  }
}