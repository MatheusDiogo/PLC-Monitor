from dataclasses import dataclass


@dataclass
class PLCConfig:
    id: str
    name: str
    ip: str
    port: int = 4840
    endpoint_url: str = ""
    application_uri: str = ""
    network: str = ""
    student: str = ""

    def to_dict(self):
        return self.__dict__.copy()

    @staticmethod
    def from_dict(d):
        return PLCConfig(
            id=d["id"],
            name=d["name"],
            ip=d["ip"],
            port=d.get("port", 4840),
            endpoint_url=d.get("endpoint_url", ""),
            application_uri=d.get("application_uri", ""),
            network=d.get("network", ""),
            student=d.get("student", ""),
        )
