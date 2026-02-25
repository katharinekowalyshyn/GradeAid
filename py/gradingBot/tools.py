import math
import ast
import operator as op

# Safe operators
SAFE_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}

def safe_eval(expr):
    """
    Safely evaluate math expressions.
    Supports +, -, *, /, ** only.
    """
    def eval_node(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return SAFE_OPERATORS[type(node.op)](
                eval_node(node.left),
                eval_node(node.right)
            )
        elif isinstance(node, ast.UnaryOp):
            return SAFE_OPERATORS[type(node.op)](
                eval_node(node.operand)
            )
        else:
            raise TypeError("Unsupported expression")

    return eval_node(ast.parse(expr, mode='eval').body)


def calculator_tool(expression: str):
    try:
        result = safe_eval(expression)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}
    

import requests

def web_api_tool(query: str):
    """
    Fetches a short answer for a question using DuckDuckGo Instant Answer API.
    """
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "t": "gradingBot"
        }
        response = requests.get(url, params=params)
        data = response.json()
        answer = data.get("AbstractText") or "No answer found."
        return {"result": answer}
    except Exception as e:
        return {"error": str(e)}