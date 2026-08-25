import { SignIn } from "@clerk/nextjs";

import PageHeader from "@/components/layout/PageHeader";

// SIE Authentication Phase 1: Clerk's own prebuilt <SignIn /> component --
// no custom password/email form, no credentials stored by us. The
// catch-all route ([[...sign-in]]) is Clerk's own current convention,
// required so its internal multi-step flows (e.g. a second verification
// factor) can render as sub-paths under /sign-in. Sits inside the
// existing PageHeader/AppShell shell like every other page -- no new
// layout, no redesign.
export default function SignInPage() {
  return (
    <>
      <PageHeader
        title="Sign In"
        subtitle="Sign in to analyze startups and build your personal workspace."
      />

      <div className="flex justify-center">
        <SignIn />
      </div>
    </>
  );
}
