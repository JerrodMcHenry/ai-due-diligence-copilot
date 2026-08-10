"use client";

import { useState } from "react";

import PillarNav from "./PillarNav";
import PillarWorkspace from "./PillarWorkspace";
import { PILLARS } from "./pillarMeta";

import type { PillarKey } from "./pillarMeta";
import type { SIEMethodologyAnalysis } from "@/types";

type IntelligencePillarsProps = {
  methodology: SIEMethodologyAnalysis;
};

export default function IntelligencePillars({
  methodology,
}: IntelligencePillarsProps) {
  const [selectedKey, setSelectedKey] = useState<PillarKey>(PILLARS[0].key);

  const selectedDefinition =
    PILLARS.find((pillar) => pillar.key === selectedKey) ?? PILLARS[0];

  return (
    <section>
      <h2 className="text-xl font-semibold text-text-primary">
        Startup Intelligence Workspace
      </h2>

      <div className="mt-4 grid gap-6 lg:grid-cols-[300px_1fr] lg:items-start">
        <PillarNav
          methodology={methodology}
          selectedKey={selectedKey}
          onSelect={setSelectedKey}
        />

        <PillarWorkspace
          label={selectedDefinition.label}
          pillar={methodology[selectedDefinition.key]}
        />
      </div>
    </section>
  );
}
