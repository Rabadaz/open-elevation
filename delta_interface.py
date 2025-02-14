class DeltaInterface:
    def __init__(self, interfaces, ds1_name, ds2_name, minimum_elevation=None):
        self.interfaces = interfaces
        self.ds1, self.ds2 = ds1_name, ds2_name
        self.minimum_elevation = minimum_elevation

    def lookup(self, lat, lng):
        elevation1 = self.interfaces[self.ds1].lookup(lat, lng)
        elevation2 = self.interfaces[self.ds2].lookup(lat, lng)
        delta = elevation1 - elevation2

        return delta if self.minimum_elevation is None else max(delta, self.minimum_elevation)
