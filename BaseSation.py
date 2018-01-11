class BaseStation:

    def __init__(self, location):
        self.location = location
        self.packagesInAir = list()

    def addPackage(self, package):
        self.packagesInAir.insert(package)

    def removePackage(self, package):
        self.packagesInAir.remove(package)