from langgraph.graph import END, START, StateGraph

from pipeline.nodes import (
  document_analyzer,
  company_sourcing, 
  company_research, 
  document_generator, 
  report_writer, 
  selection_agent
)
from models.pipeline import PipelineState

def route_after_document_analyzer(state: PipelineState) -> str:
  if state.get("status") == "failed":
    return END

def build_pipeline():
  g = StateGraph(PipelineState)
  g.add_node("document_analyzer", document_analyzer)
  g.add_node("company_sourcing", company_sourcing)
  g.add_node("company_research", company_research)
  g.add_node("selection_agent", selection_agent)
  g.add_node("report_writer", report_writer)
  g.add_node("document_generator", document_generator)
  
  g.add_edge(START, "document_analyzer")
  g.add_conditional_edges(
      "document_analyzer",
      route_after_document_analyzer,
      {
          END: END,
          "company_sourcing": "company_sourcing",
      },
  )
  g.add_edge("company_sourcing", "company_research")
  g.add_edge("company_research", "selection_agent")
  g.add_edge("selection_agent", "report_writer")
  g.add_edge("report_writer", "document_generator")
  g.add_edge("document_generator", END)
  return g.compile()