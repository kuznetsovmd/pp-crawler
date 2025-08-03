import json
from dataclasses import asdict, dataclass, fields
from typing import Optional

from pp_crawler.crawler.item import Item


@dataclass(eq=False)
class Product(Item):
    url: Optional[str] = None
    manufacturer: Optional[str] = None
    keyword: Optional[str] = None
    website: Optional[str] = None
    policy: Optional[str] = None
    hash: Optional[str] = None

    def __hash__(self):
        return hash(self.website)

    def __eq__(self, other: "Product"):
        return isinstance(other, self.__class__) and self.website == other.website

    def to_json(self) -> str:
        data = {k: v for k, v in asdict(self).items() if not k.startswith("_")}
        return json.dumps(data, ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str) -> "Product":
        obj = json.loads(data)
        field_names = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in obj.items() if k in field_names}
        return cls(**filtered)
