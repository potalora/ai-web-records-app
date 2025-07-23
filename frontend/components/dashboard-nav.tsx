"use client"

import type React from "react"

import Link from "next/link"
import { FileText, BookOpen, Settings, Home, TestTube } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useMobile } from "@/hooks/use-mobile"

export function DashboardNav() {
  const isMobile = useMobile()

  if (isMobile) {
    return (
      <div className="fixed bottom-0 left-0 z-10 w-full border-t bg-background">
        <div className="flex h-16 items-center justify-around">
          <NavItem href="/overview" icon={<Home className="h-5 w-5" />} label="Overview" />
          <NavItem href="/records" icon={<FileText className="h-5 w-5" />} label="Records" />
          <NavItem href="/summaries" icon={<BookOpen className="h-5 w-5" />} label="Summaries" />
        </div>
      </div>
    )
  }

  return (
    <div className="w-64 border-r bg-background">
      <div className="flex h-full flex-col py-4">
        <div className="px-4 py-2">
          <h2 className="text-lg font-semibold">HealthAI</h2>
        </div>
        <div className="flex-1 px-2">
          <nav className="flex flex-col gap-1">
            <NavItem href="/overview" icon={<Home className="h-5 w-5" />} label="Overview" />
            <NavItem href="/records" icon={<FileText className="h-5 w-5" />} label="Medical Records" />
            <NavItem href="/records/labs" icon={<TestTube className="h-5 w-5" />} label="Lab Results" />
            <NavItem href="/summaries" icon={<BookOpen className="h-5 w-5" />} label="Summaries" />
          </nav>
        </div>
        <div className="border-t px-2 pt-4">
          <nav className="flex flex-col gap-1">
            <NavItem href="/settings" icon={<Settings className="h-5 w-5" />} label="Settings" />
          </nav>
        </div>
      </div>
    </div>
  )
}

function NavItem({ href, icon, label }: { href: string; icon: React.ReactNode; label: string }) {
  const isMobile = useMobile()

  if (isMobile) {
    return (
      <Link href={href} className="flex flex-col items-center justify-center">
        {icon}
        <span className="mt-1 text-xs">{label}</span>
      </Link>
    )
  }

  return (
    <Link href={href}>
      <Button variant="ghost" className="w-full justify-start">
        {icon}
        <span className="ml-2">{label}</span>
      </Button>
    </Link>
  )
}
