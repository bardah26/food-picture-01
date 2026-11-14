# food-picture-01 — A Cheeseburger Worth Craving

Entry for the make.fun bounty **"Make the best-looking food picture"** ($250).

## What it is

A Python 3.13 program using only the standard library. It draws a large
cheeseburger on a white plate — golden sesame bun, melted cheese dripping
over the patty, tomato, lettuce — with fries, a ketchup dip, cherry tomatoes
and parsley, on a warm cream background with a wooden table. No text, no
network, fully deterministic: two runs produce byte-identical output.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes one PNG (`entry.png`, 768×1024, ~13 KB) to `$MAKEFUN_OUTPUT_DIR`
(default `/output/entry.png`).

## License

MIT — see `LICENSE`.
