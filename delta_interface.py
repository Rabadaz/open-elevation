class DeltaInterface:
    def __init__(self, interface1, interface2, minimum_elevation=None):
        self.interface1 = interface1
        self.interface2 = interface2
        self.minimum_elevation = minimum_elevation

    def lookup(self, lat, lng):
        elevation1 = self.interface1.lookup(lat, lng)
        elevation2 = self.interface2.lookup(lat, lng)
        delta = elevation1 - elevation2

        return delta if self.minimum_elevation is None else max(delta, self.minimum_elevation)
