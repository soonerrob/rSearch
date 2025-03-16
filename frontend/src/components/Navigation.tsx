'use client';

import { Search, Users } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function Navigation() {
  const pathname = usePathname();

  const links = [
    {
      href: '/',
      label: 'Search',
      icon: Search
    },
    {
      href: '/audiences',
      label: 'Audiences',
      icon: Users
    }
  ];

  return (
    <nav className="flex items-center gap-6">
      {links.map(({ href, label, icon: Icon }) => (
        <Link
          key={href}
          href={href}
          className={`flex items-center gap-2 text-sm font-medium transition-colors ${
            pathname === href
              ? 'text-accent-primary'
              : 'text-muted hover:text-primary'
          }`}
        >
          <Icon className="h-4 w-4" />
          {label}
        </Link>
      ))}
    </nav>
  );
} 