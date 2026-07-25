export type SPSMetadata = {
  grade: string;
  label: string;
  description: string;
  strokeClass: string;
  textClass: string;
  backgroundClass: string;
  glowClass: string;
};

export function normalizeSPS(score: number) {
  return Math.max(0, Math.min(score, 100));
}

export function getSPSMetadata(score: number): SPSMetadata {
  const normalizedScore = normalizeSPS(score);

  if (normalizedScore >= 95) {
    return {
      grade: "A+",
      label: "Exceptional",
      description:
        "Elite startup strength with outstanding overall performance.",
      strokeClass: "stroke-success",
      textClass: "text-success",
      backgroundClass: "bg-success/10",
      glowClass: "shadow-[0_0_40px_rgba(34,197,94,0.18)]",
    };
  }

  if (normalizedScore >= 90) {
    return {
      grade: "A",
      label: "Exceptional",
      description: "Outstanding performance across the core startup pillars.",
      strokeClass: "stroke-success",
      textClass: "text-success",
      backgroundClass: "bg-success/10",
      glowClass: "shadow-[0_0_36px_rgba(34,197,94,0.16)]",
    };
  }

  if (normalizedScore >= 85) {
    return {
      grade: "A−",
      label: "Excellent",
      description:
        "A highly competitive startup with limited major weaknesses.",
      strokeClass: "stroke-success",
      textClass: "text-success",
      backgroundClass: "bg-success/10",
      glowClass: "shadow-[0_0_32px_rgba(34,197,94,0.14)]",
    };
  }

  if (normalizedScore >= 80) {
    return {
      grade: "B+",
      label: "Excellent",
      description:
        "Strong performance with a clear path toward elite readiness.",
      strokeClass: "stroke-success",
      textClass: "text-success",
      backgroundClass: "bg-success/10",
      glowClass: "shadow-[0_0_28px_rgba(34,197,94,0.12)]",
    };
  }

  if (normalizedScore >= 75) {
    return {
      grade: "B",
      label: "Strong",
      description:
        "A strong startup with several meaningful competitive advantages.",
      strokeClass: "stroke-primary",
      textClass: "text-primary",
      backgroundClass: "bg-primary/10",
      glowClass: "shadow-[0_0_28px_rgba(59,130,246,0.12)]",
    };
  }

  if (normalizedScore >= 70) {
    return {
      grade: "B−",
      label: "Strong",
      description:
        "Solid overall performance with identifiable areas to improve.",
      strokeClass: "stroke-primary",
      textClass: "text-primary",
      backgroundClass: "bg-primary/10",
      glowClass: "shadow-[0_0_24px_rgba(59,130,246,0.1)]",
    };
  }

  if (normalizedScore >= 65) {
    return {
      grade: "C+",
      label: "Promising",
      description:
        "Promising fundamentals with important execution gaps remaining.",
      strokeClass: "stroke-warning",
      textClass: "text-warning",
      backgroundClass: "bg-warning/10",
      glowClass: "shadow-[0_0_24px_rgba(245,158,11,0.1)]",
    };
  }

  if (normalizedScore >= 60) {
    return {
      grade: "C",
      label: "Promising",
      description:
        "Early strength is visible, but the startup still needs development.",
      strokeClass: "stroke-warning",
      textClass: "text-warning",
      backgroundClass: "bg-warning/10",
      glowClass: "shadow-[0_0_22px_rgba(245,158,11,0.09)]",
    };
  }

  if (normalizedScore >= 50) {
    return {
      grade: "D",
      label: "Developing",
      description:
        "The startup has potential but several core areas need attention.",
      strokeClass: "stroke-warning",
      textClass: "text-warning",
      backgroundClass: "bg-warning/10",
      glowClass: "",
    };
  }

  if (normalizedScore >= 40) {
    return {
      grade: "D−",
      label: "Developing",
      description:
        "Foundational weaknesses are limiting current startup readiness.",
      strokeClass: "stroke-warning",
      textClass: "text-warning",
      backgroundClass: "bg-warning/10",
      glowClass: "",
    };
  }

  return {
    grade: "F",
    label: "Needs attention",
    description:
      "Major weaknesses require focused improvement before the startup is ready.",
    strokeClass: "stroke-danger",
    textClass: "text-danger",
    backgroundClass: "bg-danger/10",
    glowClass: "",
  };
}
