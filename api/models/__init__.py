"""Typed request/response models for the API layer.

Add a model only when a payload becomes repeated or complex enough that typing
helps; for data-driven bodies prefer a JSON template under data/api_payloads/
with <placeholders>:

    @dataclass(frozen=True)
    class CreateUserRequest:
        name: str
        email: str

        def to_dict(self) -> dict[str, Any]:
            return {"name": self.name, "email": self.email}
"""
