

def parse_data_str(data_str: str) -> tuple[tuple, list[tuple[tuple, int] | None], bool]:

    returnList = []
    data = data_str.split('/')

    metadata = data[0].split(',')
    
    if len(metadata) < 4:
        return (None, None), [None], True

    if len(metadata) > 4:
        pos_x, pos_z = metadata[3], metadata[5]
    else:
        pos_x, _, pos_z, _ = metadata

    # Get ray endpoint and collision flag
    for datapoint in data[1:]:
        ray_data = datapoint.split(',')
        if len(ray_data) < 4:
                break
        end_x, end_y, end_z, collFlag = int(ray_data[0]), int(ray_data[1]), int(ray_data[2]), int(ray_data[3])
        returnList.append(((end_x, end_z), collFlag))

    return (pos_x, pos_z), returnList, False
