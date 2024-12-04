import yaml
import sys
import argparse
import re
from collections import deque
from typing import Any, Dict, List, Tuple

OPERATORS = {
    '+': lambda x, y: x + y,
    '-': lambda x, y: x - y,
    '*': lambda x, y: x * y,
    'pow': lambda x, y: x ** y
}

NAME_REGEX = r'^[_a-zA-Z][_a-zA-Z0-9]*$'


def parse_arguments():
    parser = argparse.ArgumentParser(description="Обработка текстового файла в формат YAML.")
    parser.add_argument("input", help="Путь к входному текстовому файлу.")
    parser.add_argument("output", help="Путь к выходному YAML файлу.")
    return parser.parse_args()


def load_text(file_path: str) -> Tuple[Dict[str, Any], List[Tuple[int, str]]]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()
        data, comments = remove_comments(data)
        data_dict = yaml.safe_load(data)
        return data_dict, comments
    except yaml.YAMLError as e:
        sys.stderr.write("Ошибка синтаксиса YAML: " + str(e) + "\n")
        sys.exit(1)
    except IOError as e:
        sys.stderr.write("Ошибка чтения файла: " + str(e) + "\n")
        sys.exit(1)


def remove_comments(data: str) -> Tuple[str, List[Tuple[int, str]]]:
    """Удаляет однострочные комментарии и возвращает текст без них и список комментариев."""
    lines = data.splitlines()
    cleaned_lines = []
    comments = []

    for line_number, line in enumerate(lines):
        comment_split = line.split(';', 1)
        cleaned_lines.append(comment_split[0].rstrip())
        if len(comment_split) > 1:
            comments.append((line_number + 1, comment_split[1].strip()))

    return '\n'.join(cleaned_lines), comments


def validate_name(name: str):
    if not re.match(NAME_REGEX, name):
        raise ValueError(f"Некорректное имя '{name}'")


def evaluate_postfix(expression: List[Any], constants: Dict[str, Any]) -> Any:
    stack = deque()
    for token in expression:
        if isinstance(token, (int, float)):
            stack.append(token)
        elif isinstance(token, str) and token.isdigit():
            stack.append(int(token))
        elif token in constants:
            stack.append(constants[token])
        elif token in OPERATORS:
            try:
                b = stack.pop()
                a = stack.pop()
                result = OPERATORS[token](a, b)
                stack.append(result)
            except IndexError:
                raise ValueError("Недостаточно операндов для операции")
        else:
            raise ValueError(f"Неизвестная операция или константа '{token}'")
    if len(stack) != 1:
        raise ValueError("Ошибка в выражении: неверный остаток на стеке")
    return stack.pop()


def process_data(data: Dict[str, Any], constants: Dict[str, Any], comments: List[Tuple[int, str]]) -> Dict[str, Any]:
    processed_data = {}
    comment_dict = {line_number: comment for line_number, comment in comments}

    for key, value in data.items():
        validate_name(key)
        processed_item = {"value": None, "comment": comment_dict.get(key, None)}

        if isinstance(value, (int, float)):
            processed_item["value"] = value
            constants[key] = value
        elif isinstance(value, list):
            if all(isinstance(v, (int, float)) for v in value):
                processed_item["value"] = value
            else:
                raise ValueError(f"Массив '{key}' содержит недопустимые элементы")
        elif isinstance(value, dict) and "expr" in value:
            expression = value["expr"]
            try:
                result = evaluate_postfix(expression, constants)
                processed_item["value"] = result
                constants[key] = result
            except ValueError as e:
                raise ValueError(f"Ошибка в выражении для '{key}': {e}")
        else:
            raise ValueError(f"Некорректный формат для '{key}'")

        if processed_item["comment"]:
            processed_data[key] = {
                "value": processed_item["value"],
                "comment": processed_item["comment"]
            }
        else:
            processed_data[key] = processed_item["value"]

    return processed_data


def main():
    args = parse_arguments()
    data, comments = load_text(args.input)
    constants = {}

    try:
        processed_data = process_data(data, constants, comments)
    except ValueError as e:
        sys.stderr.write("Ошибка обработки данных: " + str(e) + "\n")
        sys.exit(1)

    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            yaml.dump(processed_data, f, allow_unicode=True, default_flow_style=False)
    except IOError as e:
        sys.stderr.write("Ошибка записи в файл: " + str(e) + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
