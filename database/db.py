from dataclasses import dataclass


@dataclass
class Staff:
    super_admin: bool
    admin: bool
    MC: bool
