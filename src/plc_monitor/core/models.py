from dataclasses import dataclass, field
from typing import List


@dataclass
class Tag:
    label: str
    db_number: int
    offset: float
    data_type: str
    bit: int = 0
    length: int = 20
    is_identity: bool = False

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(d):
        return Tag(**d)


@dataclass
class PLCConfig:
    id: str
    name: str
    ip: str
    network: str
    rack: int = 0
    slot: int = 1
    tags: List[Tag] = field(default_factory=list)

    def to_dict(self):
        d = self.__dict__.copy()
        d["tags"] = [t.to_dict() for t in self.tags]
        return d

    @staticmethod
    def from_dict(d):
        tags = [Tag.from_dict(t) for t in d.get("tags", [])]
        return PLCConfig(
            id=d["id"],
            name=d["name"],
            ip=d["ip"],
            network=d.get("network", ""),
            rack=d.get("rack", 0),
            slot=d.get("slot", 1),
            tags=tags,
        )
