# Import Checklist
ck = False
try: 
    openai = __import__('openai')
    if openai.__version__ < '1.0':
        raise ImportError("OpenAI SDK version must > 1.0.")
    sqlite3 = __import__('sqlite3')
    concurrent = __import__('concurrent')
    multiprocessing = __import__('multiprocessing')
    fastapi = __import__('fastapi')
except ImportError as e:
    print("ImportError: ", e)
    exit(1)

ck = True