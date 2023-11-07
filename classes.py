import hashlib


class Tag():
    def __init__(self, value, type="default", typeOrder=0):
        self.value = value
        self.type = type
        self.typeOrder = typeOrder

    def __repr__(self):
        return f"({self.type}) {self.value}" if self.type != "default" else str(self.value)
    
    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.value == other.value and self.type == other.type

    def __hash__(self):
        return hash((self.value, self.type))


class Img:
    def __init__(self, fname) -> None:
        self.fname = fname
        # from SO
        with open(fname, "rb") as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)
        self.hash = file_hash.hexdigest()

    def __repr__(self):
        return f"{self.fname} {self.hash[:5]}"
