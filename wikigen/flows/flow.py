from pocketflow import Flow

# Import all node classes from nodes.py
from wikigen.nodes.nodes import (
    FetchRepo,
    IdentifyAbstractions,
    AnalyzeRelationships,
    OrderComponents,
    WriteComponents,
    GenerateDocContent,
    WriteDocFiles,
)


def create_wiki_flow():
    """Creates and returns the codebase wiki generation flow."""

    # Instantiate nodes
    fetch_repo = FetchRepo()
    identify_abstractions = IdentifyAbstractions(max_retries=5, wait=20)
    analyze_relationships = AnalyzeRelationships(max_retries=5, wait=20)
    order_components = OrderComponents(max_retries=5, wait=20)
    write_components = WriteComponents(max_retries=5, wait=20)  # This is a BatchNode
    generate_doc_content = GenerateDocContent()
    write_doc_files = WriteDocFiles()

    # Connect nodes in sequence based on the design
    fetch_repo >> identify_abstractions
    identify_abstractions >> analyze_relationships
    analyze_relationships >> order_components
    order_components >> write_components
    write_components >> generate_doc_content
    generate_doc_content >> write_doc_files

    # Create the flow starting with FetchRepo
    wiki_flow = Flow(start=fetch_repo)

    return wiki_flow
