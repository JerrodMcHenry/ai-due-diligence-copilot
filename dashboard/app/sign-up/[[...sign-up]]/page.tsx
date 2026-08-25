import { SignUp } from "@clerk/nextjs";

import PageHeader from "@/components/layout/PageHeader";

// SIE Authentication Phase 1: Clerk's own prebuilt <SignUp /> component --
// no custom password/email form, no credentials stored by us. Same
// catch-all convention as /sign-in (see that page's comment).
export default function SignUpPage() {
  return (
    <>
      <PageHeader
        title="Sign Up"
        subtitle="Create an account to analyze startups and build your personal workspace."
      />

      <div className="flex justify-center">
        <SignUp />
      </div>
    </>
  );
}
