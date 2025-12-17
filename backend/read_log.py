
try:
    with open('backend/inspect_output.txt', 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
except Exception as e:
    print(e)
