// Phase 21B, Part 37. Visible but not obnoxious -- one small line, not a
// wall of legal text burying the product. Reused everywhere the simulator
// shows a result (Part 32: "Do not bury the entire product beneath
// disclaimer text").
//
// Phase 33 -- Idea Workspace Information Architecture & Founder Operating
// Loop, Part 13: this component is shown at the chooser step, before a
// founder has set anything up -- the right moment to state plainly that
// Fundraising is optional exploration, not a required destination. One
// added sentence, no new component, no change to the existing legal/
// accuracy language below it.
export default function FundraisingDisclaimer() {
  return (
    <p className="text-base leading-7 text-text-secondary">
      You don&rsquo;t need to raise money to build a successful company -- this is here for when (or if) it becomes
      relevant to you. Fundraising Simulator models potential outcomes from the assumptions you enter. Actual
      financing outcomes depend on your company&rsquo;s real capitalization and legal documents. This is educational
      decision support, not legal, tax, or investment advice.
    </p>
  );
}
