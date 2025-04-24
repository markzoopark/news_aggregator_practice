import uuid

def generate_config():
    # читаємо прізвище
    with open('student_id.txt', encoding='utf-8') as f:
        student = f.read().strip()

    # генеруємо унікальний ідентифікатор
    student_id = f"{student}_{uuid.uuid4().hex[:8]}"

    content = f'''STUDENT_ID = "{student_id}"
SOURCES    = []  # тут зберігатимуться URL джерел
'''
    with open('config.py', 'w', encoding='utf-8') as cfg:
        cfg.write(content)

if __name__ == '__main__':
    generate_config()
