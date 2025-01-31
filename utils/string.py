import re

def slug_to_string(slug):
    return re.sub(r'[^A-Za-z0-9]+', ' ', slug).strip()

def camel_to_string(camel):
    "TheChocolateWar121 -> The Chocolate War 121"
    camel = re.sub(r'(\d+)', r' \1 ', camel)
    return re.sub(r'(?<!^)(?=[A-Z][a-z])', ' ', camel).strip()
    


if __name__ == "__main__":
    print(f"{slug_to_string("-hello-world-now-")=}")
    print(f"{camel_to_string("HelloWorld")=}")
    print(f"{camel_to_string("OGuarani")=}")
    print(f"{camel_to_string("TheChocolateWar121")=}")
    print(f"{camel_to_string("ITSSF")=}")
