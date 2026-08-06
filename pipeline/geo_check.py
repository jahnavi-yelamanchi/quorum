from pathlib import Path

from .geo import load_parcels, resolve_parcel

parcels = load_parcels(Path("data/pluto_fixture.geojson"))
match = resolve_parcel("213 East 27th Street", parcels)
assert match.parcel and match.parcel.bbl == "1009080050" and match.confidence == 99
assert resolve_parcel("999 Nowhere Avenue", parcels).parcel is None
print("Parcel import and address-resolution checks passed")
