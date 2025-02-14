class LocationRequest:
    def __init__(self, lat, lng, data_sets=None, legacy_mode=False):
        self.lat = lat
        self.lng = lng
        self.data_sets = data_sets if data_sets is not None else []
        self.legacy_mode = legacy_mode
