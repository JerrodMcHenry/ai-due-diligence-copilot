import Link from "next/link";

// Phase 32 -- Product Information Architecture + Seamless User Journey,
// Part 7. Lightweight, opt-in context labels for the routes deep enough
// that "where am I?" isn't already answered by the primary nav's own
// active-state highlighting alone (TopNav.tsx) -- per the directive's own
// worked example ("Build / My Ideas / ClaimPilot"). Deliberately NOT
// added everywhere: a page one level below a highlighted nav item (e.g.
// /playbooks/[slug], which already has its own "← All playbooks" link)
// doesn't need a second wayfinding mechanism saying the same thing.
//
// Pure presentation: every item but the last is a link; the last is the
// current page, rendered as plain text (not a link to itself). No
// route/data logic lives here -- callers pass the exact crumbs for their
// own screen.
export type BreadcrumbItem = {
  label: string;
  href?: string;
};

export default function Breadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  if (items.length === 0) {
    return null;
  }

  return (
    <nav aria-label="Breadcrumb" className="mb-2 flex flex-wrap items-center gap-1.5 text-sm text-text-secondary">
      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <span key={`${item.label}-${index}`} className="flex items-center gap-1.5">
            {index > 0 ? (
              <span aria-hidden="true" className="text-text-muted">
                /
              </span>
            ) : null}
            {item.href && !isLast ? (
              <Link href={item.href} className="font-medium hover:text-primary">
                {item.label}
              </Link>
            ) : (
              <span className={isLast ? "font-medium text-text-primary" : undefined} aria-current={isLast ? "page" : undefined}>
                {item.label}
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
