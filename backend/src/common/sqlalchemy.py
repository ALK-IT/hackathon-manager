from sqlalchemy.exc import IntegrityError


def get_integrity_error_constraint(error: IntegrityError) -> str | None:
    current: BaseException | None = error.orig
    visited: set[int] = set()

    while current is not None and id(current) not in visited:
        visited.add(id(current))

        constraint_name = getattr(current, "constraint_name", None)
        if constraint_name:
            return constraint_name

        diagnostic = getattr(current, "diag", None)
        constraint_name = getattr(diagnostic, "constraint_name", None)
        if constraint_name:
            return constraint_name

        current = current.__cause__ or current.__context__

    return None
