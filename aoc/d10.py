grid = {i+j*1j: int("-1" if c == '.' else c) for i,r in enumerate(open(0))
                       for j,c in enumerate(r.strip())}

def split_iterate(acc, func):
    while True:
        r, acc = func(acc)
        yield (r, acc)


def search(trails):
    nines = []
    new_trails = []
    for pos, old_height in ((t+dir, grid[t]) for t in trails for dir in [1,-1,1j,-1j]):
        if grid.get(pos, None) == old_height+1:
            if grid.get(pos, None) == 9: nines.append(pos)
            else: new_trails.append(pos)
    print(new_trails, len(nines))
    return (nines, new_trails)

def take_while(it, pred):
   while True:
       x = next(it)
       yield x
       if (not pred(x)): return


trailheads = [p for p in grid if grid[p]==0]

print((list(len(set(el for nines, _ in take_while(split_iterate([head], search), lambda x: x[1])
      for el in nines)) for head in trailheads)))
print(len(list(el for nines, _ in take_while(split_iterate(trailheads, search), lambda x: x[1])
      for el in nines)))
