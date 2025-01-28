import re

def slug_to_string(slug):
    return re.sub(r'[^A-Za-z0-9]+', ' ', slug).strip()

def camel_to_string(camel):
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', camel).strip()


if __name__ == "__main__":
    print(f"{slug_to_string("-hello-world-now-")=}")
    print(f"{camel_to_string("HelloWorld")=}")
    print(f"{camel_to_string("ALongerTitleNow")=}")