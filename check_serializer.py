with open(r"R:\shopgenie backend\shopgenie_unified\products\serializers.py", "rb") as f:
    data = f.read()
idx = data.find(b'fields = [')
print(repr(data[idx:idx+150]))
