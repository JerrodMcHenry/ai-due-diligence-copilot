import Sidebar from "./Sidebar";

type AppShellProps = {
  children: React.ReactNode;
};

export default function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="flex min-h-screen">
        <Sidebar />

        <main className="flex-1 px-8 py-8">{children}</main>
      </div>
    </div>
  );
}
