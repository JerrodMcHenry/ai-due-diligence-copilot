// Phase 21B, Part 37. Visible but not obnoxious -- one small line, not a
// wall of legal text burying the product. Reused everywhere the simulator
// shows a result (Part 32: "Do not bury the entire product beneath
// disclaimer text").
export default function FundraisingDisclaimer() {
  return (
    <p className="text-sm leading-6 text-text-muted">
      Fundraising Simulator models potential outcomes from the assumptions you enter. Actual financing outcomes
      depend on your company&rsquo;s real capitalization and legal documents. This is educational decision support,
      not legal, tax, or investment advice.
    </p>
  );
}
