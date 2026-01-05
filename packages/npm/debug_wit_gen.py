import inspect

from scripts.generate_wit import WitGenerator

print("Attributes of WitGenerator:")
for name, val in inspect.getmembers(WitGenerator):
    print(name)

print("\nMethod check:")
print(f"Has scan_class_methods: {hasattr(WitGenerator, 'scan_class_methods')}")
print(f"Has generate_wit_file: {hasattr(WitGenerator, 'generate_wit_file')}")
