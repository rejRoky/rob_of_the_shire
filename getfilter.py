def get_filter(filter_key: str,
               end_code: str = 'done',
               all_code: str = 'all') -> list | None:
    type_filters = []
    while True:
        get_filter = input(f"Input your {filter_key} filter "
                           f"(enter '{end_code}' to finish, '{all_code}' for all): ")
        if get_filter == end_code:
            break
        elif get_filter == all_code:
            return None
        else:
            type_filters.append(get_filter)
    return type_filters
