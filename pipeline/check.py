from .monitor import lifecycle, should_alert
from .resolver import Document, resolve

documents = [
    Document("1", "2026-06-01", "https://example.test/a", "East 27th Street license\n213 East 27th Street\nCB6-2026-17 scheduled"),
    Document("2", "2026-07-01", "https://example.test/b", "27th Street liquor license\n213 East 27th Street\nCB6-2026-17 approved with conditions"),
]
items = resolve(documents)
assert len(items) == 1
assert items[0].confidence == 99
assert [event.state for event in lifecycle(items[0])] == ["scheduled", "approved"]
assert should_alert(items[0], lifecycle(items[0]), "213 East 27th Street")
print("Resolver and lifecycle checks passed")
