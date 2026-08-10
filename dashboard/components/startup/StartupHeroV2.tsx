import { SPSRing } from "@/components/sps";
import BaseCard from "@/components/ui/BaseCard";

import type { SIEMethodologyAnalysis } from "@/types";

type StartupHeroV2Props = {
  methodology: SIEMethodologyAnalysis;
};

export default function StartupHeroV2({ methodology }: StartupHeroV2Props) {
  return (
    <BaseCard className="p-8">
      <div className="grid gap-10 lg:grid-cols-[320px_1fr] lg:items-center">
        <div className="flex justify-center">
          <SPSRing
            score={methodology.startup_intelligence_score}
            confidence="High"
            size="xl"
          />
        </div>

        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-4xl font-bold text-text-primary">
              {methodology.context.company_name}
            </h1>

            <span className="rounded-full bg-primary/10 px-3 py-1 text-sm font-semibold text-primary">
              {methodology.context.company_stage}
            </span>
          </div>

          <p className="mt-2 text-lg text-text-secondary">
            {methodology.context.industry} •{" "}
            {methodology.context.business_model}
          </p>

          <div className="mt-8">
            <h2 className="text-lg font-semibold text-text-primary">
              Executive Coaching Summary
            </h2>

            <p className="mt-3 max-w-3xl leading-7 text-text-secondary">
              {methodology.executive_coaching_summary}
            </p>
          </div>
        </div>
      </div>
    </BaseCard>
  );
}
