class LocationRequest:
    def __init__(self, lat, lng, data_sets=None):
        self.lat = lat
        self.lng = lng
        self.data_sets = data_sets if data_sets is not None else []
