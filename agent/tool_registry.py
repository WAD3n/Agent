from tools.calculator import CALCULATOR_TOOL_SCHEMA, calculate
from tools.knowledge_base import KNOWLEDGE_BASE_TOOL_SCHEMA, knowledge_base_search
from tools.search import SEARCH_TOOL_SCHEMA, web_search

TOOL_SCHEMAS = [SEARCH_TOOL_SCHEMA, CALCULATOR_TOOL_SCHEMA, KNOWLEDGE_BASE_TOOL_SCHEMA]

TOOL_FUNCTIONS = {
    "web_search": web_search,
    "calculator": calculate,
    "knowledge_base_search": knowledge_base_search,
}
