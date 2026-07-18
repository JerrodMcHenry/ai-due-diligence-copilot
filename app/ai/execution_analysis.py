from app.ai.analyze_pillar import analyze_pillar
from app.models.analysis import ExecutionAnalysisResult


def analyze_execution(company_text):
    return analyze_pillar(
        pillar="Execution",
        company_text=company_text,
        result_model=ExecutionAnalysisResult,
        system_message=(
            "You are a venture capital analyst evaluating startup execution "
            "quality. Return only valid JSON."
        ),
        extra_fields={
            "gtm_execution": "Assessment of go-to-market execution.",
            "product_execution": "Assessment of product execution.",
            "operational_execution": "Assessment of operational execution.",
            "strategic_execution": "Assessment of strategic execution.",
        },
        extra_rules=[
            "Evaluate execution across go-to-market execution, product execution, operational execution, strategic execution, and execution velocity.",
            "Do not invent execution milestones.",
            "If execution details are missing, say what is missing.",
        ],
    )