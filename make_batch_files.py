import json, math, os, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch_research_targets.json', encoding='utf-8') as f:
    providers = json.load(f)

names = list(providers.keys())
BATCH_SIZE = 12
batches = [names[i:i+BATCH_SIZE] for i in range(0, len(names), BATCH_SIZE)]
print('num batches:', len(batches))

outdir = r'C:\Users\prern\AppData\Local\Temp\claude\c--Users-prern-JobBoard\4ca55fa6-19c7-48f8-8c66-ceb2e56f79d0\scratchpad\batches'
os.makedirs(outdir, exist_ok=True)

for bi, batch_names in enumerate(batches):
    batch_data = {n: providers[n] for n in batch_names}
    path = os.path.join(outdir, f'batch_{bi:02d}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(batch_data, f, indent=1, default=str)
    print(bi, len(batch_names), path)
