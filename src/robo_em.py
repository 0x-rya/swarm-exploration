

def parse_data_str(data_str: str) -> list[tuple[tuple, int]]:

    returnList = []
    data = data_str.split('/')
    # Get ray endpoint and collision flag
    for datapoint in data[1:]:
        ray_data = datapoint.split(',')
        print(ray_data)
        if len(ray_data) < 4:
                break
        end_x, end_y, end_z, collFlag = int(ray_data[0]), int(ray_data[1]), int(ray_data[2]), int(ray_data[3])
        returnList.append(((end_x, end_z), collFlag))

    return returnList
