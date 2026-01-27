class NameService():
    @classmethod
    def get_warnings(self, first_name: str, last_name: str):
        warnings = []

        if not first_name:
            warnings.append("Pleas fill in your first name")
        elif not first_name.isalpha():
            warnings.append(f"Invalid first name '{first_name}'. Use letters only.")

        if not last_name:
            warnings.append("Pleas fill in your last name")
        elif not last_name.isalpha():
            warnings.append(f"Invalid last name '{last_name}'. Use letters only.")

        return warnings