import Link from "next/link";

export default function Sidebar() {
  return (
    <aside className="w-64 bg-gray-900 min-h-screen p-6 border-r border-gray-800">
      <h2 className="text-2xl font-bold mb-8">Startup Intelligence</h2>

      <nav className="space-y-4">
        <Link href="/" className="block hover:text-blue-400">
          Dashboard
        </Link>

        <Link href="/rankings" className="block hover:text-blue-400">
          Rankings
        </Link>

        <Link href="/search" className="block hover:text-blue-400">
          Search
        </Link>

        <Link href="/historical-trends" className="block hover:text-blue-400">
          Historical Trends
        </Link>

        <Link href="/settings" className="block hover:text-blue-400">
          Settings
        </Link>
      </nav>
    </aside>
  );
}
