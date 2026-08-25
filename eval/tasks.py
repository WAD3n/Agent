TASKS = [
    # --- calculator: exact-match on the numeric answer -----------------------
    {"id": "calc-1", "category": "calculator", "question": "What is 47 + 128?", "expected": "175"},
    {"id": "calc-2", "category": "calculator", "question": "Calculate 12 * 34.", "expected": "408"},
    {"id": "calc-3", "category": "calculator", "question": "What is (100 - 37) / 7?", "expected": "9"},
    {"id": "calc-4", "category": "calculator", "question": "Compute the square root of 225.", "expected": "15"},
    {"id": "calc-5", "category": "calculator", "question": "What is 2 to the power of 10?", "expected": "1024"},
    {"id": "calc-6", "category": "calculator", "question": "Calculate 9 * 9 - 81.", "expected": "0"},
    {"id": "calc-7", "category": "calculator", "question": "What is 1000 / 8?", "expected": "125"},
    # --- search: free-text answer graded by an LLM judge ----------------------
    {
        "id": "search-1",
        "category": "search",
        "question": "In which city is OpenAI headquartered?",
        "reference": "San Francisco",
    },
    {
        "id": "search-2",
        "category": "search",
        "question": "Who created the Python programming language?",
        "reference": "Guido van Rossum",
    },
    {
        "id": "search-3",
        "category": "search",
        "question": "In which year was Anthropic founded?",
        "reference": "2021",
    },
    {
        "id": "search-4",
        "category": "search",
        "question": "Which company created the GPT-4 model?",
        "reference": "OpenAI",
    },
    {
        "id": "search-5",
        "category": "search",
        "question": "Who is the current president of the European Central Bank?",
        "reference": "Christine Lagarde",
    },
    {
        "id": "search-6",
        "category": "search",
        "question": "What is the highest mountain on Earth?",
        "reference": "Mount Everest",
    },
    # --- combo: needs reasoning/knowledge + calculator, exact-match ----------
    {
        "id": "combo-1",
        "category": "combo",
        "question": "In which year was Anthropic founded? Multiply that year by 2 and give the result.",
        "expected": "4042",
    },
    {
        "id": "combo-2",
        "category": "combo",
        "question": "How many officially confirmed chemical elements are in the periodic table? Add 100 to that number.",
        "expected": "218",
    },
    {
        "id": "combo-3",
        "category": "combo",
        "question": "How many squares does a chessboard have? Multiply that number by 3.",
        "expected": "192",
    },
    {
        "id": "combo-4",
        "category": "combo",
        "question": "How many planets are in the Solar System? Square that number.",
        "expected": "64",
    },
    {
        "id": "combo-5",
        "category": "combo",
        "question": "How many minutes are in a day? Subtract 440 from that number.",
        "expected": "1000",
    },
]
