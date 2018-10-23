import os

path_prefix = "output/method2/"


def dealFile(name):
    f = open(path_prefix + name, "r")
    my_dict = {}
    while 1:
        lines = f.readlines(100000)
        if not lines:
            break
        for line in lines:
            if line not in my_dict:
                my_dict[line] = 1
    f.close()
    os.remove(path_prefix + name)
    if len(my_dict) > 1:
        o = open(path_prefix + "dealt" + name, "w")
        for x in my_dict:
            o.write(x.strip())
            o.write("\n")
            o.flush()
        o.close()


result = {}
for f_path, f_dir, f_files in os.walk(path_prefix):
    if not f_files:
        continue
    for f in f_files:
        if f.split(".")[-1] == 'txt':
            result[f] = len(result)

for x in result:
    dealFile(x)
