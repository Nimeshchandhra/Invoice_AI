from utils.llm import generate_response

def respond(query, analysis):
    prompt = f"""
    Give a clear final answer.

    Question: {query}
    Analysis: {analysis}
    """

    return generate_response(prompt)