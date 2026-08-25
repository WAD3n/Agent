from asteval import Interpreter

CALCULATOR_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluate a mathematical expression, e.g. '2 + 2 * 3' or 'sqrt(16)'.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate.",
                },
            },
            "required": ["expression"],
        },
    },
}


def calculate(expression: str) -> str:
    aeval = Interpreter()
    result = aeval.eval(expression, raise_errors=False)
    if aeval.error:
        messages = "; ".join(err.get_error()[1] for err in aeval.error)
        return f"Error evaluating expression: {messages}"
    return str(result)
